# -*- coding: utf-8 -*-
"""
V-CORE: Seed Memory (Phoenix persistence)
License: AGPL-3.0
Author: Володимир Поздняк

Stores only geometry:
- lattice fills (7 numbers)
- last state id
- short trail hash (few tokens)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any
import json
import time

@dataclass
class VStateSeed:
    timestamp: float
    lattice: Dict[int, int]
    last_state_id: int
    trail: List[str]

    def to_json(self) -> str:
        payload = {
            "timestamp": self.timestamp,
            "lattice": self.lattice,
            "last_state_id": self.last_state_id,
            "trail": self.trail,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "VStateSeed":
        obj = json.loads(s)
        return VStateSeed(
            timestamp=float(obj.get("timestamp", time.time())),
            lattice={int(k): int(v) for k, v in obj.get("lattice", {}).items()},
            last_state_id=int(obj.get("last_state_id", 0)),
            trail=[str(x) for x in obj.get("trail", [])],
        )
