# -*- coding: utf-8 -*-
"""
V-CORE Adapter: Protein Color Grammar (no brute force)
License: AGPL-3.0
Author: Володимир Поздняк

Goal:
- Map amino acids to 7 V-CORE octaves (colors)
- Provide a RULE-BASED generator (motifs) for "new proteins" without brute-force search.

Important:
This does NOT claim biological validity by itself.
It provides a structured prior / grammar that can be tested by external protein models.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random

# ---- V-CORE amino palette (20 aa -> octave/color group)
# Groups are standard biochemical categories mapped onto your 7-octave logic.

AA_TO_OCTAVE: Dict[str, int] = {
    # Hydrophobic core builders (Matter)
    "G": 1, "A": 1, "V": 1, "L": 1, "I": 1,
    # Structure / turns (System)
    "P": 2,
    # Bridges / sulfur (Flow)
    "C": 3, "M": 3,
    # Polar surface (Heart)
    "S": 4, "T": 4, "N": 4, "Q": 4,
    # Positive charge (Logic)
    "K": 5, "R": 5, "H": 5,
    # Negative charge (Drive)
    "D": 6, "E": 6,
    # Aromatic / resonance (Spirit)
    "F": 7, "Y": 7, "W": 7,
}

OCTAVE_EMOJI: Dict[int, str] = {
    1: "🔴",
    2: "🟠",
    3: "🟡",
    4: "🟢",
    5: "🔵",
    6: "🟣",
    7: "🔮",
}

OCTAVE_NAME: Dict[int, str] = {
    1: "Matter(core hydrophobic)",
    2: "System(turns/scaffold)",
    3: "Flow(bridges/sulfur)",
    4: "Heart(polar surface)",
    5: "Logic(positive charge)",
    6: "Drive(negative charge)",
    7: "Spirit(aromatic resonance)",
}

# pools for sampling
POOL: Dict[int, List[str]] = {}
for aa, oc in AA_TO_OCTAVE.items():
    POOL.setdefault(oc, []).append(aa)


@dataclass
class ProteinSpec:
    """
    A simple "design intent" specification:
    - length: sequence length
    - core_ratio: fraction of hydrophobic core (octave 1)
    - turn_ratio: fraction of proline/turns (octave 2)
    - bridge_count: number of Cys (octave 3) to place as stabilizers
    - charge_balance: desired (positives - negatives) around 0 for neutrality
    - aromatic_markers: number of aromatic residues to act as "signal markers"
    """
    length: int = 60
    core_ratio: float = 0.35
    turn_ratio: float = 0.08
    bridge_count: int = 2
    charge_balance: int = 0
    aromatic_markers: int = 2
    seed: Optional[int] = None


class VProteinDesigner:
    """
    Rule-based generator:
    1) Allocate counts per octave (structure prior)
    2) Place stabilizers (Cys) at mirrored positions
    3) Distribute core vs surface vs functional residues
    4) Output sequence + color visualization + stats
    """

    def __init__(self) -> None:
        pass

    def visualize(self, seq: str) -> str:
        return "".join(OCTAVE_EMOJI.get(AA_TO_OCTAVE.get(a, 2), "⬡") for a in seq)

    def stats(self, seq: str) -> Dict[str, int]:
        counts = {i: 0 for i in range(1, 8)}
        for a in seq:
            oc = AA_TO_OCTAVE.get(a, 2)
            counts[oc] += 1
        return counts

    def _pick(self, octave: int) -> str:
        return random.choice(POOL[octave])

    def design(self, spec: ProteinSpec) -> Tuple[str, Dict[str, int]]:
        if spec.seed is not None:
            random.seed(spec.seed)

        n = max(10, int(spec.length))

        # Allocate by ratios (simple prior)
        n_core = int(n * spec.core_ratio)         # octave 1
        n_turn = int(n * spec.turn_ratio)         # octave 2
        n_arom = int(spec.aromatic_markers)       # octave 7
        n_bridge = int(spec.bridge_count)         # octave 3 (Cys)
        n_rest = n - (n_core + n_turn + n_arom + n_bridge)
        if n_rest < 0:
            # clamp in case of extreme spec
            n_rest = 0

        # Charges: allocate positives/negatives around desired balance
        # Let total charged be ~20% of remaining by default.
        charged_total = int(0.20 * n_rest)
        pos = charged_total // 2
        neg = charged_total - pos

        # adjust balance (pos - neg)
        # if balance positive, increase positives; if negative, increase negatives
        diff = int(spec.charge_balance)
        if diff > 0:
            pos += diff
        elif diff < 0:
            neg += abs(diff)

        # keep inside remaining budget
        if pos + neg > n_rest:
            scale = n_rest / max(1, (pos + neg))
            pos = int(pos * scale)
            neg = n_rest - pos

        n_polar = n_rest - (pos + neg)            # octave 4

        # ---- Build sequence scaffold as segments (core/surface/turn repeats)
        # We avoid brute force by using a "grammar":
        # [core block] + [surface block] + [turn] + [core] + [surface] + ...
        seq = ["X"] * n

        # Place bridges (Cys) as mirrored anchors (stabilizer heuristic)
        # E.g. positions ~ 1/3 and 2/3 (or mirrored near ends).
        bridge_positions: List[int] = []
        if n_bridge > 0:
            # For 2 bridges: p and n-1-p.
            p = n // 3
            bridge_positions.append(p)
            if n_bridge >= 2:
                bridge_positions.append(n - 1 - p)
            # If more, sprinkle
            for k in range(2, n_bridge):
                bridge_positions.append((k * n) // (n_bridge + 1))
            bridge_positions = sorted(set(bridge_positions))[:n_bridge]

        for bp in bridge_positions:
            seq[bp] = "C"

        # Place aromatic markers near N-terminus and around middle/end (signal tags)
        arom_positions: List[int] = []
        if n_arom > 0:
            arom_positions.append(max(0, n // 10))
            if n_arom >= 2:
                arom_positions.append(min(n - 1, (7 * n) // 10))
            for k in range(2, n_arom):
                arom_positions.append((k * n) // (n_arom + 1))
            arom_positions = [p for p in arom_positions if seq[p] == "X"]
            arom_positions = arom_positions[:n_arom]

        for ap in arom_positions:
            seq[ap] = random.choice(["F", "Y", "W"])  # octave 7

        # Fill remaining with grammar-driven distribution
        # Create buckets
        bucket: List[str] = []
        bucket += [self._pick(1) for _ in range(n_core)]
        bucket += ["P" for _ in range(n_turn)]
        bucket += [self._pick(4) for _ in range(n_polar)]
        bucket += [self._pick(5) for _ in range(pos)]
        bucket += [self._pick(6) for _ in range(neg)]

        random.shuffle(bucket)

        # Fill empty slots
        bi = 0
        for i in range(n):
            if seq[i] == "X":
                if bi < len(bucket):
                    seq[i] = bucket[bi]
                    bi += 1
                else:
                    seq[i] = self._pick(4)

        final_seq = "".join(seq)
        counts = self.stats(final_seq)

        info = {
            "length": len(final_seq),
            "core(🔴)": counts[1],
            "turn(🟠)": counts[2],
            "bridge(🟡)": counts[3],
            "polar(🟢)": counts[4],
            "pos(🔵)": counts[5],
            "neg(🟣)": counts[6],
            "arom(🔮)": counts[7],
        }
        return final_seq, info
