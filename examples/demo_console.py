# -*- coding: utf-8 -*-
"""
V-CORE Demo Console
License: AGPL-3.0
Author: Володимир Поздняк

Run:
  python -m examples.demo_console
"""

from __future__ import annotations

from core.sri_yantra_core import VSriYantraCore
from adapters.linguistics import VLinguisticsAdapter
from adapters.protein_visualizer import VProteinDesigner, ProteinSpec


def demo_words():
    print("\n" + "=" * 70)
    print("DEMO 1) WORDS -> V-CORE (Sri Yantra / Meru Gravity)")
    print("=" * 70)

    core = VSriYantraCore(base_threshold=6)
    ling = VLinguisticsAdapter()

    stream = [
        "ВІЙНА", "ГРОШІ", "ДІМ", "WATER", "LOVE",
        "ІСТИНА", "ДУХ", "TRUTH", "V-CORE"
    ]

    for w in stream:
        pkt = ling.to_packet(w)
        res = core.ingest(pkt)
        print(f"{w:<10} | oc={res.octave} ph={res.phase} "
              f"| layer={res.layer:<5} | shadow={pkt.shadow:.2f} coh={pkt.coherence:.2f} | {res.note}")

    print("\nFACES:")
    print(core.pretty_faces())
    print("\nREPORT:", core.report())


def demo_phoenix_seed():
    print("\n" + "=" * 70)
    print("DEMO 2) PHOENIX SEED (Save / Load without memory bloat)")
    print("=" * 70)

    core1 = VSriYantraCore(base_threshold=6)
    ling = VLinguisticsAdapter()

    for w in ["WAR", "FOOD", "HOUSE", "MONEY", "EARTH", "STONE", "WATER", "LOVE"]:
        core1.ingest(ling.to_packet(w))

    seed = core1.export_seed()
    print("\nSEED JSON:", seed)

    # new instance
    core2 = VSriYantraCore(base_threshold=6)
    core2.import_seed(seed)

    print("\nRESURRECTED FACES:")
    print(core2.pretty_faces())
    print("REPORT:", core2.report())

    # continue
    for w in ["TRUTH", "SPIRIT", "V-CORE"]:
        pkt = ling.to_packet(w)
        res = core2.ingest(pkt)
        print(f"{w:<10} -> layer={res.layer} note={res.note}")

    print("\nFINAL REPORT:", core2.report())


def demo_protein_design():
    print("\n" + "=" * 70)
    print("DEMO 3) PROTEIN COLOR GRAMMAR (Rule-based, no brute force)")
    print("=" * 70)

    designer = VProteinDesigner()

    # Example specs (different "intent" proteins)
    specs = [
        ProteinSpec(length=60, core_ratio=0.40, turn_ratio=0.07, bridge_count=2, charge_balance=0, aromatic_markers=2, seed=7),
        ProteinSpec(length=80, core_ratio=0.30, turn_ratio=0.10, bridge_count=4, charge_balance=2, aromatic_markers=3, seed=11),
        ProteinSpec(length=45, core_ratio=0.45, turn_ratio=0.05, bridge_count=2, charge_balance=-2, aromatic_markers=1, seed=21),
    ]

    for i, spec in enumerate(specs, 1):
        seq, info = designer.design(spec)
        vis = designer.visualize(seq)
        print(f"\n--- Protein #{i} ---")
        print("SEQ:", seq)
        print("VIZ:", vis)
        print("INFO:", info)


def main():
    demo_words()
    demo_phoenix_seed()
    demo_protein_design()


if __name__ == "__main__":
    main()
def demo_chemistry():
    print("\n" + "=" * 70)
    print("DEMO 4) CHEMISTRY FORMULAS -> V-CORE (No molecular brute force)")
    print("=" * 70)

    from adapters.chem_formula import VChemicalFormulaAdapter
    core = VSriYantraCore(base_threshold=6)
    chem = VChemicalFormulaAdapter()

    formulas = ["H2O", "C6H12O6", "Fe2O3", "NaCl"]

    for f in formulas:
        packets = chem.to_packets(f)
        for pkt in packets:
            core.ingest(pkt)

        print(f"\nFORMULA: {f} | events={len(packets)}")
        print(core.pretty_faces())
        print("REPORT:", core.report())


# і в main():
def main():
    demo_words()
    demo_phoenix_seed()
    demo_protein_design()
    demo_chemistry()
      
