# -*- coding: utf-8 -*-
"""
V-CORE: Meru / Sri Yantra gravity rules
License: AGPL-3.0
Author: Володимир Поздняк

This module defines the hierarchical constraints:
BASE (1-2) -> RING (3-5) -> APEX (6-7)

It is intentionally simple and explainable.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from .lattice import VFaceLattice

@dataclass
class GravityDecision:
    allowed: bool
    corrected_octave: int
    reason: str


class VMeruGravity:
    """
    Practical gravity gate:
    - APEX cannot be entered if BASE isn't sufficiently built.
    """
    def __init__(self, base_threshold: int = 6) -> None:
        # base_threshold is a "mass" score: fill(1)+fill(2) must reach it.
        self.base_threshold = int(base_threshold)

    @staticmethod
    def layer(octave: int) -> str:
        if octave <= 2:
            return "BASE"
        if octave <= 5:
            return "RING"
        return "APEX"

    def decide(self, octave: int, lattice: VFaceLattice) -> GravityDecision:
        base_mass = lattice.fill_level(1) + lattice.fill_level(2)
        layer = self.layer(octave)

        if layer == "APEX" and base_mass < self.base_threshold:
            # redirect to matter foundation
            return GravityDecision(
                allowed=False,
                corrected_octave=1,
                reason=f"GRAVITY_REJECT: base_mass={base_mass} < {self.base_threshold}, redirect->Matter"
            )

        return GravityDecision(
            allowed=True,
            corrected_octave=octave,
            reason="OK"
        )
