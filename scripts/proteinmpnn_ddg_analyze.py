"""Compare candidate mutations against the proteinmpnn_ddg saturation table.

Reads the per-position ΔΔG CSV produced by `03_proteinmpnn_ddg.sbatch` and
emits a small summary table with the ΔΔG for every mutation in PLM3, PLM4,
en31, and en15 — so we can see whether any of our PLM picks are
stability-risky before we commit more compute to Boltz-2.

The peptoneltd/proteinmpnn_ddg CSV format isn't 100% nailed down in the
container docs, so this script supports both wide (pos,wt + one column per
target aa) and long (pos,wt,mut,ddg) layouts — autodetect from the header.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# Mutations we care about
PLM3_MUTATIONS = [("G", 1243, "T"), ("W", 1507, "K"), ("C", 1292, "K"), ("M", 1617, "K")]
PLM4_MUTATIONS = [("T", 1535, "V"), ("Y", 1249, "F"), ("Y", 1341, "L"), ("A", 1325, "K")]
EN31_MUTATIONS = [("G", 1243, "T"), ("E", 1369, "R"), ("E", 1449, "H")]
EN15_MUTATIONS = [("E", 1603, "H")]

AAS = "ACDEFGHIKLMNPQRSTVWY"


def load_ddg(csv_path: Path) -> dict[tuple[int, str], float]:
    """Return mapping (pos, target_aa) -> ddg (kcal/mol; positive = destabilizing).

    Handles three known peptoneltd / proteinmpnn_ddg layouts:
      A. LONG with explicit names: pos,wt,mut,ddg
      B. LONG with peptoneltd names: (index),pre,post,pos,logit_difference,logit_difference_ddg
      C. WIDE: one column per target aa
    """
    text = csv_path.read_text().splitlines()
    if not text:
        raise ValueError(f"Empty file: {csv_path}")
    cols = [c.strip().lower() for c in text[0].split(",")]
    out: dict[tuple[int, str], float] = {}

    # peptoneltd format: 'pre' (wt) + 'post' (mut) + 'pos' + 'logit_difference_ddg'
    if "pre" in cols and "post" in cols and "pos" in cols:
        log.info("Detected peptoneltd LONG-format CSV (pre,post,pos,logit_difference_ddg)")
        i_pos = cols.index("pos")
        i_pre = cols.index("pre")
        i_post = cols.index("post")
        # Prefer the calibrated ddg column over the raw logit
        ddg_candidates = [i for i, c in enumerate(cols) if "ddg" in c]
        if not ddg_candidates:
            raise ValueError(f"No ΔΔG column found in header: {cols}")
        i_ddg = ddg_candidates[-1]  # rightmost = most processed
        for line in text[1:]:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            try:
                pos = int(parts[i_pos])
                pre = parts[i_pre].upper()
                post = parts[i_post].upper()
                if pre == post:
                    continue  # self-mutation has ddg=0 by definition
                ddg = float(parts[i_ddg])
            except (ValueError, IndexError):
                continue
            out[(pos, post)] = ddg
        log.info("Loaded %d (pos, mut) -> ΔΔG entries", len(out))
        return out

    # generic LONG: pos + (mut|target) + a ddg column
    if ("mut" in cols or "target" in cols) and ("pos" in cols or "position" in cols):
        log.info("Detected generic LONG-format CSV (pos,wt,mut,ddg)")
        i_pos = cols.index("pos") if "pos" in cols else cols.index("position")
        i_mut = cols.index("mut") if "mut" in cols else cols.index("target")
        ddg_candidates = [i for i, c in enumerate(cols) if "ddg" in c]
        if not ddg_candidates:
            raise ValueError(f"No ΔΔG column found in header: {cols}")
        i_ddg = ddg_candidates[0]
        for line in text[1:]:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            try:
                pos = int(parts[i_pos])
                mut = parts[i_mut].upper()
                ddg = float(parts[i_ddg])
            except (ValueError, IndexError):
                continue
            out[(pos, mut)] = ddg
        log.info("Loaded %d (pos, mut) -> ΔΔG entries", len(out))
        return out

    # WIDE: one column per target aa
    log.info("Detected WIDE-format CSV (one column per target aa)")
    raw_cols = [c.strip() for c in text[0].split(",")]
    i_pos = 0
    if raw_cols[0].lower() in ("pos", "position"):
        i_pos = 0
    elif len(raw_cols) > 1 and raw_cols[1].lower() in ("pos", "position"):
        i_pos = 1
    aa_cols = {i: c for i, c in enumerate(raw_cols) if len(c) == 1 and c in AAS}
    for line in text[1:]:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        try:
            pos = int(parts[i_pos])
        except (ValueError, IndexError):
            continue
        for i, aa in aa_cols.items():
            try:
                out[(pos, aa)] = float(parts[i])
            except (ValueError, IndexError):
                continue
    log.info("Loaded %d (pos, mut) -> ΔΔG entries", len(out))
    return out


def report_block(name: str, mutations: list[tuple[str, int, str]],
                 ddg: dict[tuple[int, str], float]) -> None:
    log.info("\n=== %s ===", name)
    log.info("%-8s  %-10s  %-30s",
             "Variant", "ΔΔG (kcal/mol)", "Stability call")
    cum = 0.0
    any_missing = False
    for wt, pos, mut in mutations:
        if (pos, mut) not in ddg:
            log.info("  %s%d%s    not in table — position outside saturation range?",
                     wt, pos, mut)
            any_missing = True
            continue
        value = ddg[(pos, mut)]
        cum += value
        if value < -0.5:
            call = "STABILIZING"
        elif value < 0.5:
            call = "neutral"
        elif value < 1.5:
            call = "mild destabilizer"
        elif value < 3.0:
            call = "moderate destabilizer"
        else:
            call = "STRONG destabilizer — risk"
        log.info("  %s%d%s    %+7.2f       %s", wt, pos, mut, value, call)
    if not any_missing:
        log.info("  -- additive ΔΔG (independent assumption): %+.2f", cum)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ddg", required=True,
                        help="Path to ddg.csv from 03_proteinmpnn_ddg.sbatch")
    args = parser.parse_args()

    ddg = load_ddg(Path(args.ddg))

    report_block("PLM3 (ESM-2 sequence-only)", PLM3_MUTATIONS, ddg)
    report_block("PLM4 (LigandMPNN structure+ligand)", PLM4_MUTATIONS, ddg)
    report_block("en31 reference (Acharya 2024)", EN31_MUTATIONS, ddg)
    report_block("en15 reference (Acharya 2024)", EN15_MUTATIONS, ddg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
