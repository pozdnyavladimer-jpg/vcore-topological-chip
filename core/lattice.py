# -*- coding: utf-8 -*-
"""
V-CORE: Lattice (42-state quantization)
License: AGPL-3.0
Author: Володимир Поздняк

This module defines:
- 7 Octaves (layers)
- 6 Phases (strength quantization)
- 42 discrete states
- A minimal face-fill lattice for "crystallization" tracking
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
import math

OCTAVES = 7
PHASES = 6

OCTAVE_COLOR: Dict[int, str] = {
    1: "RED (Matter/Base)",
    2: "ORANGE (System)",
    3: "YELLOW (Flow)",
    4: "GREEN (Heart/Life)",
    5: "BLUE (Logic)",
    6: "INDIGO (Drive)",
    7: "VIOLET (Spirit)",
}

TOPIC_TO_OCTAVE: Dict[str, int] = {
    "matter": 1,
    "system": 2,
    "flow": 3,
    "life": 4,
    "logic": 5,
    "drive": 6,
    "spiritual": 7,
}

OCTAVE_TO_TOPIC: Dict[int, str] = {v: k for k, v in TOPIC_TO_OCTAVE.items()}


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def strength_to_phase(strength: float) -> int:
    """
    Quantize strength (0..1) into phase (1..6).
    """
    s = clamp(float(strength), 0.0, 1.0)
    phase = int(math.ceil(s * PHASES))
    return 1 if phase < 1 else PHASES if phase > PHASES else phase


def state_id(octave: int, phase: int) -> int:
    """
    State IDs: 1..42
    """
    if octave < 1 or octave > OCTAVES:
        raise ValueError("octave must be 1..7")
    if phase < 1 or phase > PHASES:
        raise ValueError("phase must be 1..6")
    return (octave - 1) * PHASES + phase


@dataclass
class LatticeHit:
    topic: str
    octave: int
    phase: int
    state_id: int
    crystallized_face: bool


class VFaceLattice:
    """
    Minimal 'honeycomb' per octave: count filled slots (0..6).
    This is a compact memory representation (no text storage).
    """
    def __init__(self) -> None:
        self.faces: Dict[int, int] = {i: 0 for i in range(1, OCTAVES + 1)}

    def add(self, octave: int) -> bool:
        """
        Returns True iff the face became crystallized (reached 6) on this hit.
        """
        if self.faces[octave] < PHASES:
            self.faces[octave] += 1
            return self.faces[octave] == PHASES
        return False

    def fill_level(self, octave: int) -> int:
        return self.faces[octave]

    def is_crystal(self, octave: int) -> bool:
        return self.faces[octave] == PHASES

    def axis_ready(self) -> bool:
        """
        Axis criterion: 1-4-7 full (Root + Heart + Spirit).
        """
        return self.is_crystal(1) and self.is_crystal(4) and self.is_crystal(7)

    def snapshot(self) -> Dict[int, int]:
        return dict(self.faces)

    def restore(self, snap: Dict[int, int]) -> None:
        # json keys may be strings
        restored = {}
        for k, v in snap.items():
            restored[int(k)] = int(v)
        for i in range(1, OCTAVES + 1):
            restored.setdefault(i, 0)
        self.faces = restored

    def pretty_bar(self, octave: int) -> str:
        fill = self.faces[octave]
        return "⬢" * fill + "⬡" * (PHASES - fill)
