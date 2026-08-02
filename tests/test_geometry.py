from __future__ import annotations

import numpy as np

from fibonacci_galaxy.geometry import build_fibonacci_tiling, fibonacci_sequence
from fibonacci_galaxy.renderer import GalaxyConfig, generate_particle_field


def test_sequence_begins_with_visible_unit_squares() -> None:
    assert fibonacci_sequence(10) == [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]


def test_squares_have_expected_sizes_and_do_not_overlap() -> None:
    squares = build_fibonacci_tiling(10)
    assert [square.size for square in squares] == fibonacci_sequence(10)
    for left_index, left in enumerate(squares):
        for right in squares[left_index + 1 :]:
            overlap_x = min(left.x + left.size, right.x + right.size) - max(left.x, right.x)
            overlap_y = min(left.y + left.size, right.y + right.size) - max(left.y, right.y)
            assert overlap_x <= 1e-9 or overlap_y <= 1e-9


def test_arc_samples_stay_inside_their_squares() -> None:
    for square in build_fibonacci_tiling(10):
        points = square.sample_arc(101)
        assert np.all(points[:, 0] >= square.x - 1e-9)
        assert np.all(points[:, 0] <= square.x + square.size + 1e-9)
        assert np.all(points[:, 1] >= square.y - 1e-9)
        assert np.all(points[:, 1] <= square.y + square.size + 1e-9)


def test_adjacent_arcs_are_continuous() -> None:
    squares = build_fibonacci_tiling(10)
    for current, following in zip(squares, squares[1:]):
        assert np.allclose(current.arc_end, following.arc_start, atol=1e-9)


def test_seeded_particle_field_is_reproducible(tmp_path) -> None:
    config = GalaxyConfig(particle_count=200, background_stars=20, output=tmp_path / "x.mp4")
    squares = build_fibonacci_tiling(config.terms)
    first = generate_particle_field(config, squares)
    second = generate_particle_field(config, squares)
    assert np.array_equal(first.target, second.target)
    assert np.array_equal(first.colors, second.colors)
    assert np.array_equal(first.progress, second.progress)
