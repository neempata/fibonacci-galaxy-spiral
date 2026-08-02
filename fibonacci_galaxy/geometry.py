"""Mathematically exact Fibonacci tiling and quarter-circle geometry."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

import numpy as np


@dataclass(frozen=True)
class FibonacciSquare:
    """A square in the tiling and the quarter-circle drawn inside it."""

    index: int
    value: int
    x: float
    y: float
    size: float
    direction: str
    arc_center_x: float
    arc_center_y: float
    theta_start: float
    theta_end: float

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.size / 2, self.y + self.size / 2

    @property
    def arc_start(self) -> tuple[float, float]:
        angle = self.theta_start * pi / 180
        return (
            self.arc_center_x + self.size * cos(angle),
            self.arc_center_y + self.size * sin(angle),
        )

    @property
    def arc_end(self) -> tuple[float, float]:
        angle = self.theta_end * pi / 180
        return (
            self.arc_center_x + self.size * cos(angle),
            self.arc_center_y + self.size * sin(angle),
        )

    def sample_arc(self, samples: int = 48) -> np.ndarray:
        angles = np.deg2rad(np.linspace(self.theta_start, self.theta_end, samples))
        return np.column_stack(
            (
                self.arc_center_x + self.size * np.cos(angles),
                self.arc_center_y + self.size * np.sin(angles),
            )
        )


def fibonacci_sequence(terms: int) -> list[int]:
    """Return Fibonacci values beginning with 1, 1."""
    if terms < 1:
        raise ValueError("terms must be at least 1")
    if terms == 1:
        return [1]
    values = [1, 1]
    while len(values) < terms:
        values.append(values[-1] + values[-2])
    return values


def build_fibonacci_tiling(terms: int = 10) -> list[FibonacciSquare]:
    """Build adjoining squares and a tangent-continuous Fibonacci spiral.

    The first two unit squares form a 2x1 rectangle. Further squares are added
    top, left, bottom, and right around the current bounding rectangle.
    """
    values = fibonacci_sequence(terms)
    squares: list[FibonacciSquare] = [
        FibonacciSquare(0, 1, 0, 0, 1, "seed", 1, 1, 180, 270)
    ]
    if terms == 1:
        return squares

    squares.append(FibonacciSquare(1, 1, 1, 0, 1, "right", 1, 1, 270, 360))
    min_x, min_y, max_x, max_y = 0.0, 0.0, 2.0, 1.0
    directions = ("top", "left", "bottom", "right")

    for index, size in enumerate(values[2:], start=2):
        direction = directions[(index - 2) % 4]
        if direction == "top":
            x, y = min_x, max_y
            arc_x, arc_y, start, end = min_x, max_y, 0, 90
            max_y += size
        elif direction == "left":
            x, y = min_x - size, min_y
            arc_x, arc_y, start, end = min_x, min_y, 90, 180
            min_x -= size
        elif direction == "bottom":
            x, y = min_x, min_y - size
            arc_x, arc_y, start, end = max_x, min_y, 180, 270
            min_y -= size
        else:
            x, y = max_x, min_y
            arc_x, arc_y, start, end = max_x, max_y, 270, 360
            max_x += size

        squares.append(
            FibonacciSquare(
                index,
                size,
                x,
                y,
                size,
                direction,
                arc_x,
                arc_y,
                start,
                end,
            )
        )
    return squares


def tiling_bounds(squares: list[FibonacciSquare]) -> tuple[float, float, float, float]:
    return (
        min(square.x for square in squares),
        min(square.y for square in squares),
        max(square.x + square.size for square in squares),
        max(square.y + square.size for square in squares),
    )


def spiral_path(squares: list[FibonacciSquare], samples_per_arc: int = 64) -> np.ndarray:
    sections = [square.sample_arc(samples_per_arc) for square in squares]
    return np.concatenate([sections[0], *(section[1:] for section in sections[1:])])
