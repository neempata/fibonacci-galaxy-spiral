from __future__ import annotations

import argparse
from pathlib import Path

from .renderer import (
    GalaxyConfig,
    render_galaxy,
    render_preview_frames,
    show_galaxy,
    smoke_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play or render an animated Fibonacci galaxy.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Save an MP4 instead of opening the animation popup.",
    )
    parser.add_argument("--terms", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1618033)
    parser.add_argument("--particles", type=int, default=8_000)
    parser.add_argument("--background-stars", type=int, default=2_000)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--resolution", type=int, default=1440)
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--smoke", action="store_true", help="Render a fast 512px test video.")
    parser.add_argument("--previews", type=Path, help="Render three diagnostic PNG frames.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = GalaxyConfig(
        terms=args.terms,
        seed=args.seed,
        particle_count=args.particles,
        background_stars=args.background_stars,
        fps=args.fps,
        duration=args.duration,
        resolution=args.resolution,
        output=args.output or Path("fibonacci_galaxy.mp4"),
        dpi=args.dpi,
    )
    if args.smoke:
        config = smoke_config(args.output or Path("smoke-test.mp4"))
    if args.previews:
        for path in render_preview_frames(config, args.previews):
            print(path)
    elif args.output:
        print(render_galaxy(config))
    else:
        show_galaxy(config)


if __name__ == "__main__":
    main()
