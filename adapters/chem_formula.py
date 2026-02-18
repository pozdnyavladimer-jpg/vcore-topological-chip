# -*- coding: utf-8 -*-
"""
V-CORE Adapter: Chemical Formula -> VPacket stream
License: AGPL-3.0
Author: Володимир Поздняк

Goal:
- Parse strings like "C6H12O6", "Fe2O3", "H2O", "NaCl"
- Convert into packets for V-CORE Sri Yantra core:
  - octave derived from element -> topic/octave map
  - strength from "phase fill" logic (cyclic 1..6)
  - shadow/coherence can be set by heuristic (default neutral)

Notes:
- This is NOT a chemistry simulator. It's a structured encoder:
  "formula -> topological event stream".
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import re

from core.sri_yantra_core import VPacket
from core.lattice import clamp


# ---- Minimal element->octave mapping (extend as needed)
# The goal is not "correct chemistry", but stable deterministic encoding.
DEFAULT_ELEMENT_OCTAVE: Dict[str, int] = {
    # life / water / breath
    "O": 4,
    # spirit-like light carrier (gas)
    "H": 7,
    # matter scaffold
    "C": 1,
    "S": 1,
    # system / salts / ionic
    "Na": 2,
    "K": 2,
    "Cl": 2,
    "Mg": 3,
    "Ca": 2,
    # metals / magnets
    "Fe": 1,
    "Cu": 3,
    "Zn": 5,
    # info/flow-ish
    "N": 3,
    "P": 3,
    "Si": 5,
}


@dataclass
class ChemConfig:
    # coherence for chemical events (0..1). neutral by default
    coherence: float = 0.55
    # how strong a single atom-hit is (mapped from phase 1..6)
    strength_min: float = 0.20
    strength_max: float = 1.00


class VChemicalFormulaAdapter:
    """
    Encodes formula as a stream:
      element count -> repeated hits with cyclic phases (1..6).
    """

    # Element token: Capital + optional lowercase; count: optional digits
    TOKEN_RE = re.compile(r"([A-Z][a-z]?)(\d*)")

    def __init__(self,
                 element_octave: Optional[Dict[str, int]] = None,
                 cfg: Optional[ChemConfig] = None) -> None:
        self.map = dict(DEFAULT_ELEMENT_OCTAVE)
        if element_octave:
            self.map.update(element_octave)
        self.cfg = cfg or ChemConfig()

    def parse(self, formula: str) -> List[Tuple[str, int]]:
        """
        Returns list of (element, count).
        Example: "C6H12O6" -> [("C",6), ("H",12), ("O",6)]
        """
        s = formula.strip()
        out: List[Tuple[str, int]] = []
        for el, n in self.TOKEN_RE.findall(s):
            if not el:
                continue
            cnt = int(n) if n else 1
            out.append((el, cnt))
        return out

    def _strength_from_phase(self, phase: int) -> float:
        phase = max(1, min(6, int(phase)))
        # linear map phase->strength
        t = (phase - 1) / 5.0
        return self.cfg.strength_min + t * (self.cfg.strength_max - self.cfg.strength_min)

    def to_packets(self, formula: str) -> List[VPacket]:
        """
        Convert formula to a list of VPackets.
        Each atom contributes one packet; phase cycles 1..6 for each element group.
        """
        coherence = clamp(self.cfg.coherence, 0.0, 1.0)
        shadow = 1.0 - coherence

        items = self.parse(formula)
        packets: List[VPacket] = []

        for el, cnt in items:
            octave = int(self.map.get(el, 2))  # default "system"
            # cyclic phases: 1..6 repeating for repeated atoms
            for i in range(cnt):
                phase = (i % 6) + 1
                strength = self._strength_from_phase(phase)
                packets.append(
                    VPacket(
                        content=f"{el}{cnt if cnt != 1 else ''}",
                        octave=octave,
                        strength=strength,
                        coherence=coherence,
                        shadow=shadow
                    )
                )
        return packets
