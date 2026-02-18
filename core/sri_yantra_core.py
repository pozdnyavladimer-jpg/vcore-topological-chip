# -*- coding: utf-8 -*-
"""
V-CORE: Sri Yantra / Meru Core (Topological Attractor)
License: AGPL-3.0
Author: Володимир Поздняк

This is the main engine for the repository:

- Input packet: {content, topic/octave, strength, coherence, shadow}
- Lattice: quantizes to 42 discrete states
- Gravity: hierarchical routing BASE->RING->APEX
- Bindu: singularity trigger when axis (1-4-7) is ready

This is a research preview implementation: explainable, testable, minimal.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .lattice import (
    VFaceLattice, TOPIC_TO_OCTAVE, OCTAVE_COLOR,
    strength_to_phase, state_id, OCTAVE_TO_TOPIC, clamp
)
from .gravity import VMeruGravity
from .seed_memory import VStateSeed
import time


@dataclass
class VPacket:
    content: str
    topic: Optional[str] = None     # "matter/system/..."
    octave: Optional[int] = None    # 1..7
    strength: float = 0.5          # 0..1
    coherence: Optional[float] = None  # 0..1 (optional)
    shadow: Optional[float] = None     # 0..1 (optional, high=heavy entropy)


@dataclass
class VResult:
    accepted: bool
    layer: str
    octave: int
    phase: int
    state_id: int
    crystallized_face: bool
    bindu_active: bool
    note: str


class VSriYantraCore:
    def __init__(self, *, base_threshold: int = 6, max_trail: int = 8) -> None:
        self.lattice = VFaceLattice()
        self.gravity = VMeruGravity(base_threshold=base_threshold)

        self.last_state_id: int = 0
        self.bindu_active: bool = False

        self._trail: List[str] = []
        self._max_trail = int(max_trail)

        # optional: store small counters per layer
        self.layer_counts: Dict[str, int] = {"BASE": 0, "RING": 0, "APEX": 0}

    def _resolve_octave(self, pkt: VPacket) -> int:
        if pkt.octave is not None:
            oc = int(pkt.octave)
            return 1 if oc < 1 else 7 if oc > 7 else oc
        if pkt.topic:
            return TOPIC_TO_OCTAVE.get(pkt.topic, 2)
        return 2  # default system

    def ingest(self, pkt: VPacket) -> VResult:
        octave_in = self._resolve_octave(pkt)

        # shadow/coherence coupling (optional):
        # if user provides coherence, shadow defaults to inverse, and vice versa.
        if pkt.coherence is not None and pkt.shadow is None:
            pkt.shadow = 1.0 - clamp(pkt.coherence, 0.0, 1.0)
        if pkt.shadow is not None and pkt.coherence is None:
            pkt.coherence = 1.0 - clamp(pkt.shadow, 0.0, 1.0)

        # "Gravitational sorting": heavy shadow tends to fall down
        octave = octave_in
        note = "OK"

        if pkt.shadow is not None:
            sh = clamp(pkt.shadow, 0.0, 1.0)
            # if very heavy, force to BASE regardless of intended octave
            if sh >= 0.75 and octave > 2:
                octave = 1
                note = f"SHADOW_DROP({sh:.2f})->BASE"

        # Meru gravity gate (APEX requires BASE mass)
        decision = self.gravity.decide(octave, self.lattice)
        if not decision.allowed:
            octave = decision.corrected_octave
            note = decision.reason

        layer = self.gravity.layer(octave)
        self.layer_counts[layer] += 1

        # quantize strength -> phase -> state
        phase = strength_to_phase(pkt.strength)
        sid = state_id(octave, phase)

        crystallized = self.lattice.add(octave)

        self.last_state_id = sid
        self._trail.append(f"{octave}.{phase}")
        if len(self._trail) > self._max_trail:
            self._trail.pop(0)

        # bindu criterion
        self.bindu_active = self.lattice.axis_ready()

        return VResult(
            accepted=True,
            layer=layer,
            octave=octave,
            phase=phase,
            state_id=sid,
            crystallized_face=crystallized,
            bindu_active=self.bindu_active,
            note=note
        )

    def report(self) -> Dict[str, Any]:
        faces = self.lattice.snapshot()
        return {
            "faces": faces,
            "axis_ready": self.lattice.axis_ready(),
            "bindu": "OPEN" if self.bindu_active else "CLOSED",
            "last_state_id": self.last_state_id,
            "trail": list(self._trail),
            "layers": dict(self.layer_counts)
        }

    # ---------- Phoenix / Seed ----------
    def export_seed(self) -> str:
        seed = VStateSeed(
            timestamp=time.time(),
            lattice=self.lattice.snapshot(),
            last_state_id=self.last_state_id,
            trail=list(self._trail),
        )
        return seed.to_json()

    def import_seed(self, seed_json: str) -> None:
        seed = VStateSeed.from_json(seed_json)
        self.lattice.restore(seed.lattice)
        self.last_state_id = seed.last_state_id
        self._trail = list(seed.trail)[-self._max_trail :]
        self.bindu_active = self.lattice.axis_ready()

    # ---------- Pretty console helpers ----------
    def pretty_faces(self) -> str:
        lines = []
        for oc in range(1, 8):
            bar = self.lattice.pretty_bar(oc)
            lines.append(f"{oc} {OCTAVE_COLOR[oc]:<18} {bar}")
        return "\n".join(lines)

    @staticmethod
    def octave_topic(octave: int) -> str:
        return OCTAVE_TO_TOPIC.get(octave, "system")
