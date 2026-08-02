"""Procedural artwork and animation renderer for the Fibonacci galaxy."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import imageio_ffmpeg
import matplotlib

# TkAgg gives the project a native popup window on desktop Python. It also
# continues to support PNG and MP4 rendering when an output is requested.
matplotlib.use("TkAgg")

import matplotlib.animation as animation
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from matplotlib.transforms import Affine2D
from PIL import Image, ImageDraw, ImageFilter

from .geometry import FibonacciSquare, build_fibonacci_tiling, tiling_bounds


@dataclass(frozen=True)
class GalaxyConfig:
    terms: int = 10
    seed: int = 1618033
    particle_count: int = 8_000
    background_stars: int = 2_000
    fps: int = 30
    duration: float = 12.0
    resolution: int = 1440
    output: Path = Path("fibonacci_galaxy.mp4")
    dpi: int = 120

    @property
    def frames(self) -> int:
        return max(1, round(self.fps * self.duration))


@dataclass
class ParticleField:
    target: np.ndarray
    colors: np.ndarray
    sizes: np.ndarray
    progress: np.ndarray
    secondary: np.ndarray


def _smoothstep(value: float) -> float:
    value = float(np.clip(value, 0.0, 1.0))
    return value * value * (3.0 - 2.0 * value)


def _window(time: float, start: float, end: float) -> float:
    return _smoothstep((time - start) / (end - start))


def _center_and_span(squares: list[FibonacciSquare]) -> tuple[np.ndarray, float]:
    min_x, min_y, max_x, max_y = tiling_bounds(squares)
    center = np.array([(min_x + max_x) / 2, (min_y + max_y) / 2])
    return center, max(max_x - min_x, max_y - min_y)


def _rotate(points: np.ndarray, center: np.ndarray, angle: float) -> np.ndarray:
    cosine, sine = np.cos(angle), np.sin(angle)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return (points - center) @ rotation.T + center


def generate_particle_field(
    config: GalaxyConfig,
    squares: list[FibonacciSquare],
) -> ParticleField:
    """Generate reproducible start and target locations for both galaxy arms."""
    rng = np.random.default_rng(config.seed)
    center, span = _center_and_span(squares)
    count = config.particle_count
    secondary = rng.random(count) < 0.34

    weights = np.array([square.size**0.82 for square in squares], dtype=float)
    weights /= weights.sum()
    arc_indices = rng.choice(len(squares), size=count, p=weights)
    fractions = rng.random(count)

    targets = np.empty((count, 2), dtype=float)
    widths = np.empty(count, dtype=float)
    progress = np.empty(count, dtype=float)
    for index, square in enumerate(squares):
        mask = arc_indices == index
        angles = np.deg2rad(
            square.theta_start
            + fractions[mask] * (square.theta_end - square.theta_start)
        )
        radial = np.column_stack((np.cos(angles), np.sin(angles)))
        base = np.array([square.arc_center_x, square.arc_center_y]) + square.size * radial
        width = 0.07 * square.size + 0.045 * span
        offsets = rng.normal(0.0, width, size=mask.sum())
        tangent_offsets = rng.normal(0.0, width * 0.32, size=mask.sum())
        tangent = np.column_stack((-radial[:, 1], radial[:, 0]))
        targets[mask] = base + radial * offsets[:, None] + tangent * tangent_offsets[:, None]
        widths[mask] = width
        progress[mask] = (index + fractions[mask]) / len(squares)

    targets[secondary] = 2 * center - targets[secondary]

    core_factor = 1.0 - np.clip(progress, 0.0, 1.0)
    inner = np.array([1.0, 0.82, 0.56, 0.92])
    outer = np.array([0.48, 0.68, 1.0, 0.80])
    colors = outer + core_factor[:, None] * (inner - outer)
    violet = (rng.random(count) < 0.22) & (progress > 0.35)
    colors[violet, :3] = np.array([0.74, 0.48, 1.0])
    colors[secondary, 3] *= 0.62

    sizes = rng.lognormal(mean=0.0, sigma=0.58, size=count) * 3.6
    bright = rng.random(count) < 0.025
    sizes[bright] *= 4.0
    colors[bright, 3] = 1.0
    return ParticleField(targets, colors, sizes, progress, secondary)


def generate_background(
    config: GalaxyConfig,
    squares: list[FibonacciSquare],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(config.seed + 1)
    center, span = _center_and_span(squares)
    positions = center + rng.uniform(-0.67 * span, 0.67 * span, (config.background_stars, 2))
    sizes = rng.lognormal(-0.2, 0.72, config.background_stars) * 1.8
    colors = np.ones((config.background_stars, 4))
    colors[:, :3] = rng.choice(
        np.array([[0.72, 0.82, 1.0], [1.0, 0.93, 0.78], [0.78, 0.67, 1.0]]),
        size=config.background_stars,
    )
    colors[:, 3] = rng.uniform(0.22, 0.80, config.background_stars)
    return positions, sizes, colors


def _to_pixels(
    points: np.ndarray,
    center: np.ndarray,
    span: float,
    layer_size: int,
) -> np.ndarray:
    normalized = (points - center) / (span * 1.38) + 0.5
    pixels = normalized * layer_size
    pixels[:, 1] = layer_size - pixels[:, 1]
    return pixels


def create_nebula_layer(
    config: GalaxyConfig,
    squares: list[FibonacciSquare],
    layer_size: int = 768,
) -> np.ndarray:
    """Pre-render a blurred galactic core and dust-lane texture with Pillow."""
    rng = np.random.default_rng(config.seed + 2)
    center, span = _center_and_span(squares)
    glow = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
    dust = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    dust_draw = ImageDraw.Draw(dust, "RGBA")

    center_px = _to_pixels(center[None, :], center, span, layer_size)[0]
    for radius, color in (
        (0.18, (255, 220, 150, 145)),
        (0.32, (130, 95, 255, 82)),
        (0.52, (45, 95, 225, 38)),
    ):
        rx = radius * layer_size
        ry = rx * 0.68
        glow_draw.ellipse(
            (center_px[0] - rx, center_px[1] - ry, center_px[0] + rx, center_px[1] + ry),
            fill=color,
        )

    all_points = np.concatenate([square.sample_arc(100) for square in squares])
    px = _to_pixels(all_points, center, span, layer_size)
    for x, y in px[::2]:
        radius = rng.uniform(2.0, 7.0)
        glow_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(85, 110, 255, 18))
        dust_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(5, 8, 24, 38))

    glow = glow.filter(ImageFilter.GaussianBlur(layer_size * 0.035))
    dust = dust.filter(ImageFilter.GaussianBlur(layer_size * 0.012))
    return np.asarray(Image.alpha_composite(glow, dust))


def _setup_scene(config: GalaxyConfig):
    squares = build_fibonacci_tiling(config.terms)
    center, span = _center_and_span(squares)
    field = generate_particle_field(config, squares)
    bg_positions, bg_sizes, bg_colors = generate_background(config, squares)
    nebula = create_nebula_layer(config, squares)

    fig_inches = config.resolution / config.dpi
    fig, ax = plt.subplots(figsize=(fig_inches, fig_inches), dpi=config.dpi)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.patch.set_facecolor("#02030b")
    ax.set_facecolor("#02030b")
    ax.set_aspect("equal")
    ax.axis("off")

    # A tighter crop makes the spiral the dominant visual. The outermost square
    # is allowed to run slightly beyond the frame for a cinematic composition.
    half = span * 0.59
    base_limits = (center[0] - half, center[0] + half, center[1] - half, center[1] + half)
    ax.set_xlim(base_limits[:2])
    ax.set_ylim(base_limits[2:])

    bg_artist = ax.scatter(
        bg_positions[:, 0], bg_positions[:, 1], s=bg_sizes, c=bg_colors, linewidths=0, zorder=1
    )
    extent = base_limits
    nebula_artist = ax.imshow(nebula, extent=extent, origin="upper", alpha=0, zorder=2)
    hidden_colors = field.colors.copy()
    hidden_colors[:, 3] = 0
    particle_artist = ax.scatter(
        field.target[:, 0],
        field.target[:, 1],
        s=field.sizes,
        c=hidden_colors,
        linewidths=0,
        zorder=3,
    )

    square_patches = []
    labels = []
    arc_lines = []
    for square in squares:
        rectangle = patches.Rectangle(
            (square.x, square.y),
            square.size,
            square.size,
            fill=False,
            edgecolor="#64d8ff",
            linewidth=0.95,
            alpha=0,
            zorder=5,
        )
        ax.add_patch(rectangle)
        square_patches.append(rectangle)

        points = square.sample_arc(80)
        line, = ax.plot(
            points[:, 0],
            points[:, 1],
            color="#ffd67a",
            linewidth=2.15,
            alpha=0,
            solid_capstyle="round",
            zorder=6,
        )
        line.set_path_effects([path_effects.Stroke(linewidth=7.0, foreground="#ffb347", alpha=0.18), path_effects.Normal()])
        arc_lines.append((line, points))

        x, y = square.center
        label = ax.text(
            x,
            y,
            str(square.value),
            ha="center",
            va="center",
            color="#d9f5ff",
            fontsize=max(6, min(15, 5 + np.sqrt(square.size))),
            alpha=0,
            zorder=7,
        )
        labels.append(label)

    phi_label = ax.text(
        0.965,
        0.045,
        "φ ≈ 1.618",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color="#ffe6a8",
        fontsize=13,
        alpha=0,
        zorder=8,
    )
    title = ax.text(
        0.045,
        0.955,
        "FIBONACCI GALAXY",
        transform=ax.transAxes,
        ha="left",
        va="top",
        color="#d9f5ff",
        fontsize=12,
        alpha=0,
        zorder=8,
    )
    return {
        "fig": fig,
        "ax": ax,
        "squares": squares,
        "center": center,
        "span": span,
        "base_limits": base_limits,
        "field": field,
        "bg_artist": bg_artist,
        "nebula_artist": nebula_artist,
        "particle_artist": particle_artist,
        "square_patches": square_patches,
        "arc_lines": arc_lines,
        "labels": labels,
        "phi_label": phi_label,
        "title": title,
    }


def _update_scene(scene: dict, config: GalaxyConfig, frame: int):
    time = frame / config.fps
    center = scene["center"]
    field = scene["field"]

    background_alpha = _window(time, 0.0, 2.2)
    scene["bg_artist"].set_alpha(0.10 + 0.90 * background_alpha)

    # The mathematical spiral now leads the story. Particles remain at their
    # final positions and bloom just behind the advancing drawing tip.
    spiral_reveal = _window(time, 0.45, 8.6)
    nebula_alpha = _window(time, 0.25, 3.2)
    scene["nebula_artist"].set_alpha(0.70 * nebula_alpha)

    angle = np.deg2rad(6.0) * _window(time, 0.0, 11.0)
    positions = _rotate(field.target, center, angle)
    scene["particle_artist"].set_offsets(positions)

    particle_progress = field.progress + np.where(field.secondary, 0.055, 0.018)
    particle_reveal = np.clip((spiral_reveal - particle_progress) / 0.075, 0.0, 1.0)
    particle_reveal = particle_reveal * particle_reveal * (3.0 - 2.0 * particle_reveal)
    twinkle = 0.88 + 0.12 * np.sin(frame * 0.13 + np.arange(len(field.sizes)) * 0.71)
    visible_colors = field.colors.copy()
    visible_colors[:, 3] *= particle_reveal * twinkle
    scene["particle_artist"].set_facecolors(visible_colors)

    rotation = Affine2D().rotate_around(center[0], center[1], angle) + scene["ax"].transData
    scene["nebula_artist"].set_transform(rotation)

    geometry = spiral_reveal
    total = len(scene["squares"])
    for index, (square, rectangle, arc_item) in enumerate(
        zip(scene["squares"], scene["square_patches"], scene["arc_lines"])
    ):
        local = _smoothstep(geometry * total - index)
        rectangle.set_alpha(0.24 * local)
        rectangle.set_transform(rotation)

        line, points = arc_item
        visible = max(2, round(local * len(points)))
        line.set_data(points[:visible, 0], points[:visible, 1])
        line.set_alpha(0.92 * local)
        line.set_transform(rotation)

    label_alpha = _window(time, 8.4, 10.7)
    for label in scene["labels"]:
        label.set_alpha(0.72 * label_alpha)
        label.set_transform(rotation)
    scene["phi_label"].set_alpha(0.88 * label_alpha)
    scene["title"].set_alpha(0.65 * label_alpha)

    zoom = 1.0 - 0.07 * _window(time, 0.0, 11.0)
    min_x, max_x, min_y, max_y = scene["base_limits"]
    half_x = (max_x - min_x) * zoom / 2
    half_y = (max_y - min_y) * zoom / 2
    scene["ax"].set_xlim(center[0] - half_x, center[0] + half_x)
    scene["ax"].set_ylim(center[1] - half_y, center[1] + half_y)
    return []


def _create_animation(scene: dict, config: GalaxyConfig) -> animation.FuncAnimation:
    """Connect the prepared scene to its per-frame update function."""
    return animation.FuncAnimation(
        scene["fig"],
        lambda frame: _update_scene(scene, config, frame),
        frames=config.frames,
        interval=1000 / config.fps,
        blit=False,
        repeat=True,
        repeat_delay=1_000,
    )


def show_galaxy(config: GalaxyConfig) -> None:
    """Play the animation in a native Matplotlib popup until it is closed."""
    scene = _setup_scene(config)
    movie = _create_animation(scene, config)
    # Keep a reference alive while the blocking window is open. Matplotlib
    # otherwise may garbage-collect an animation before it can play.
    scene["animation"] = movie
    plt.show()
    plt.close(scene["fig"])


def render_galaxy(config: GalaxyConfig) -> Path:
    """Render an H.264 MP4 using Matplotlib and ImageIO's FFmpeg binary."""
    config.output.parent.mkdir(parents=True, exist_ok=True)
    scene = _setup_scene(config)
    matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    movie = _create_animation(scene, config)
    writer = animation.FFMpegWriter(
        fps=config.fps,
        codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart"],
        metadata={"title": "Fibonacci Galaxy", "artist": "Python / Matplotlib"},
    )
    movie.save(str(config.output), writer=writer, dpi=config.dpi)
    plt.close(scene["fig"])
    return config.output


def render_preview_frames(config: GalaxyConfig, output_dir: Path) -> list[Path]:
    """Render the opening, midpoint, and final frames as PNGs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = _setup_scene(config)
    frames = [0, config.frames // 2, config.frames - 1]
    names = ["preview-00-opening.png", "preview-50-midpoint.png", "preview-100-final.png"]
    paths = []
    for frame, name in zip(frames, names):
        _update_scene(scene, config, frame)
        path = output_dir / name
        scene["fig"].savefig(path, dpi=config.dpi, facecolor=scene["fig"].get_facecolor())
        paths.append(path)
    plt.close(scene["fig"])
    return paths


def smoke_config(output: Path) -> GalaxyConfig:
    return replace(
        GalaxyConfig(),
        particle_count=1_200,
        background_stars=350,
        fps=12,
        duration=2.0,
        resolution=512,
        output=output,
        dpi=100,
    )
