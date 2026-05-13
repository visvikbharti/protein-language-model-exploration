"""Smoke test: load ESM-2 8M, score one position on FnCas9, sanity-check output shape.

Run from project root with PYTHONPATH=src .venv/bin/python scripts/smoke_esm.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")

from nuclease_design.io import load_fasta
from nuclease_design.scoring.esm import ESMScorer, score_saturation
from nuclease_design.variants import Variant


def main() -> int:
    fasta = load_fasta(Path("data/raw/A0Q5Y3_fncas9.fasta"))
    seq = fasta[0].sequence
    print(f"WT FnCas9 length: {len(seq)} aa")
    print(f"Residue at 1369 (expected E for E1369R): {seq[1369-1]}")
    print(f"Residue at 1449 (expected E for E1449H): {seq[1449-1]}")
    print(f"Residue at 1243 (expected G for G1243T): {seq[1243-1]}")
    print(f"Residue at 1603 (expected E for E1603H): {seq[1603-1]}")

    print("\nLoading ESM-2 8M for smoke test...")
    scorer = ESMScorer(name="esm2_8M", device="cpu")
    sat = score_saturation(scorer, seq, [1369])
    print(f"\nTop 5 substitutions at position 1369 (WT=E):")
    for variant, llr in sat[:5]:
        marker = "  ← en1 mutation" if str(variant) == "E1369R" else ""
        print(f"  {variant}  LLR={llr:+.3f}{marker}")
    print(f"\nE1369R rank: {[str(v) for v, _ in sat].index('E1369R') + 1} of {len(sat)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
