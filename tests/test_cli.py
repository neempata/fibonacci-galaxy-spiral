from __future__ import annotations

import sys
from pathlib import Path

from fibonacci_galaxy import cli
from fibonacci_galaxy import renderer
from fibonacci_galaxy.renderer import GalaxyConfig


def test_cli_renders_video_by_default(monkeypatch, capsys) -> None:
    received: list[GalaxyConfig] = []

    monkeypatch.setattr(sys, "argv", ["fibonacci-galaxy"])
    monkeypatch.setattr(
        cli,
        "render_galaxy",
        lambda config: received.append(config) or config.output,
    )
    monkeypatch.setattr(
        cli,
        "render_preview_frames",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected preview render")),
    )

    cli.main()

    assert len(received) == 1
    assert received[0].output == Path("fibonacci_galaxy.mp4")
    assert "fibonacci_galaxy.mp4" in capsys.readouterr().out


def test_cli_uses_requested_output_path(monkeypatch, tmp_path, capsys) -> None:
    output = tmp_path / "galaxy.mp4"
    received: list[GalaxyConfig] = []

    def fake_render(config: GalaxyConfig) -> Path:
        received.append(config)
        return config.output

    monkeypatch.setattr(sys, "argv", ["fibonacci-galaxy", "--output", str(output)])
    monkeypatch.setattr(cli, "render_galaxy", fake_render)
    monkeypatch.setattr(
        cli,
        "render_preview_frames",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected preview render")),
    )

    cli.main()

    assert len(received) == 1
    assert received[0].output == output
    assert str(output) in capsys.readouterr().out


def test_render_galaxy_closes_scene_after_saving_movie(monkeypatch, tmp_path) -> None:
    output = tmp_path / "galaxy.mp4"
    figure = object()
    scene = {"fig": figure}
    closed: list[object] = []

    class FakeMovie:
        def __init__(self) -> None:
            self.saved_args: dict[str, object] = {}

        def save(self, path: str, writer: object | None = None, dpi: int | None = None) -> None:
            self.saved_args = {"path": path, "writer": writer, "dpi": dpi}

    movie = FakeMovie()

    monkeypatch.setattr(renderer, "_setup_scene", lambda _config: scene)
    monkeypatch.setattr(renderer.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr(renderer.animation, "FuncAnimation", lambda *args, **kwargs: movie)
    monkeypatch.setattr(renderer.animation, "FFMpegWriter", lambda *args, **kwargs: object())
    monkeypatch.setattr(renderer.plt, "close", lambda value: closed.append(value))

    result = renderer.render_galaxy(GalaxyConfig(output=output))

    assert result == output
    assert movie.saved_args["path"] == str(output)
    assert closed == [figure]
