# -*- coding: utf-8 -*-
"""
V-CORE Adapter: Linguistics -> VPacket
License: AGPL-3.0
Author: Володимир Поздняк

Purpose:
- Convert natural language tokens/words into VPacket fields:
  - octave/topic via gematria-like indexing
  - coherence via "water balance" (vowel/consonant ratio)
  - shadow = 1 - coherence
  - strength derived from coherence (or configurable)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import re

from core.sri_yantra_core import VPacket
from core.lattice import clamp


@dataclass
class LinguisticConfig:
    # Ideal vowel ratio for "water-like" flow (language-agnostic heuristic)
    ideal_vowel_ratio: float = 0.40
    # How sharply coherence drops when ratio deviates
    ratio_sensitivity: float = 2.5
    # How strength is mapped from coherence (min..max)
    strength_min: float = 0.20
    strength_max: float = 1.00


class VLinguisticsAdapter:
    """
    Two outputs matter for the engine:
    - octave: where the token *wants* to go
    - shadow/coherence: whether it *falls* (heavy) or *rises* (light)
    """

    ENG = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    UKR = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"

    VOWELS = set("AEIOUYАЕЄИІЇОУЮЯ")

    # Optional: allow you to "pin" special tokens to specific topics/octaves
    # (useful for demos; keep small to avoid hard-coding ideology)
    DEFAULT_OVERRIDES: Dict[str, Tuple[int, float]] = {
        # token: (octave, coherence)
        "VCORE": (7, 0.95),
        "V-CORE": (7, 0.95),
        "LOVE": (4, 0.85),
        "WATER": (4, 0.90),
    }

    def __init__(self, cfg: Optional[LinguisticConfig] = None,
                 overrides: Optional[Dict[str, Tuple[int, float]]] = None) -> None:
        self.cfg = cfg or LinguisticConfig()
        self.overrides = dict(self.DEFAULT_OVERRIDES)
        if overrides:
            self.overrides.update(overrides)

    def _clean(self, text: str) -> str:
        # keep letters + dash (for V-CORE), remove digits/punct except dash
        t = re.sub(r"[^A-Za-zА-Яа-яҐґЄєІіЇї\-]", "", text)
        return t.strip()

    def _letter_weight(self, ch: str) -> int:
        c = ch.upper()
        if c in self.ENG:
            return self.ENG.index(c) + 1
        if c in self.UKR:
            return self.UKR.index(c) + 1
        return 0

    def octave_from_word(self, word: str) -> int:
        clean = "".join([c for c in word if c.isalpha()])
        if not clean:
            return 2
        wsum = sum(self._letter_weight(c) for c in clean)
        oc = wsum % 7
        return 7 if oc == 0 else oc

    def coherence_from_word(self, word: str) -> float:
        clean = "".join([c for c in word if c.isalpha()]).upper()
        if not clean:
            return 0.0

        v = sum(1 for c in clean if c in self.VOWELS)
        ratio = v / len(clean)

        dist = abs(ratio - self.cfg.ideal_vowel_ratio)
        coherence = 1.0 - (dist * self.cfg.ratio_sensitivity)
        return clamp(coherence, 0.0, 1.0)

    def strength_from_coherence(self, coherence: float) -> float:
        # map coherence into [strength_min..strength_max]
        c = clamp(coherence, 0.0, 1.0)
        return self.cfg.strength_min + c * (self.cfg.strength_max - self.cfg.strength_min)

    def to_packet(self, word: str) -> VPacket:
        raw = word
        clean = self._clean(word)

        if not clean:
            return VPacket(content=raw, octave=2, strength=0.2, coherence=0.0, shadow=1.0)

        key = clean.upper()
        if key in self.overrides:
            oc, coh = self.overrides[key]
            coh = clamp(coh, 0.0, 1.0)
            return VPacket(
                content=raw,
                octave=int(oc),
                strength=self.strength_from_coherence(coh),
                coherence=coh,
                shadow=1.0 - coh
            )

        oc = self.octave_from_word(clean)
        coh = self.coherence_from_word(clean)
        sh = 1.0 - coh
        strength = self.strength_from_coherence(coh)

        return VPacket(
            content=raw,
            octave=oc,
            strength=strength,
            coherence=coh,
            shadow=sh
        )
