"""Compute and dump per-position conservation across the Cas9 family for the
WED-PI hotspot windows. Output two-column TSV: pos, identity_conservation,
shannon_entropy, normalised_conservation.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta
from nuclease_design.scoring.conservation import (
    DEFAULT_ORTHOLOG_FILES,
    compute_conservation,
    load_orthologs_from_dir,
)


HOTSPOT_WINDOWS = {
    "WED_PLL_G1243": (1233, 1253),
    "PI_E1369": (1359, 1379),
    "PI_E1449": (1439, 1459),
    "PI_WED_E1603": (1593, 1613),
}

REFERENCE_VARIANTS = {
    "G1243T": "en31, WED-PLL",
    "E1369R": "en1+en31, PI PAM",
    "E1449H": "en31, PI PAM",
    "E1603H": "en15, PI/WED",
}
PLM1_SITES = {
    "H1236L": "PLM1, WED",
    "R1367L": "PLM1, PI",
    "W1459K": "PLM1, PI RNA-contact",
    "Q1596N": "PLM1, PI surface",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_conservation",
    )
    args = parser.parse_args()

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    log.info("FnCas9: %d aa", len(fncas9))

    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)
    log.info("Orthologs: %s", list(orthologs))

    scores = compute_conservation(fncas9, orthologs)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dump all positions in the hotspot windows
    tsv = out_dir / "hotspot_conservation.tsv"
    with tsv.open("w") as f:
        cols = ["pos", "fncas9_residue", "id_conservation", "class_conservation",
                "shannon_entropy", "normalised_conservation"] + list(orthologs.keys())
        f.write("\t".join(cols) + "\n")
        for window_name, (lo, hi) in HOTSPOT_WINDOWS.items():
            for pos in range(lo, hi + 1):
                s = scores[pos - 1]
                row = [str(pos), s.fncas9_residue,
                       f"{s.identity_conservation:.3f}",
                       f"{s.class_conservation:.3f}",
                       f"{s.shannon_entropy:.3f}",
                       f"{s.normalised_conservation:.3f}"]
                for name in orthologs:
                    row.append(s.column[name])
                f.write("\t".join(row) + "\n")
    log.info("Wrote %s", tsv)

    # Print summary at engineered sites
    log.info("\n=== Conservation at reference + PLM1 mutation sites ===")
    log.info(f"{'Site':<8}  {'WT':<3}  {'id_cons':>7}  {'class_cons':>9}  {'norm_cons':>9}  {'role':<22}")
    log.info("-" * 90)
    for v_str, role in {**REFERENCE_VARIANTS, **PLM1_SITES}.items():
        pos = int(v_str[1:-1])
        s = scores[pos - 1]
        max_cons = max(s.identity_conservation, s.class_conservation)
        flag = "<-- HIGH CONS" if max_cons >= 0.6 else "    " if max_cons >= 0.2 else "  (variable)"
        log.info("%-8s  %-3s  %7.3f  %9.3f  %9.3f  %-22s %s",
                 v_str, s.fncas9_residue,
                 s.identity_conservation,
                 s.class_conservation,
                 s.normalised_conservation,
                 role, flag)

    # Histogram-like summary across the 84 hotspot residues
    hotspot_positions: list[int] = []
    for lo, hi in HOTSPOT_WINDOWS.values():
        hotspot_positions.extend(range(lo, hi + 1))
    cons_at_hotspots = [scores[p - 1].identity_conservation for p in hotspot_positions]
    log.info("\n=== Distribution of identity_conservation across the 84 hotspot residues ===")
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.001]
    for lo, hi in zip(bins, bins[1:]):
        n = sum(1 for c in cons_at_hotspots if lo <= c < hi)
        bar = "#" * n
        log.info("  [%.1f, %.1f)  %s (%d)", lo, hi, bar, n)
    log.info("Mean conservation across hotspots: %.3f", sum(cons_at_hotspots) / len(cons_at_hotspots))

    return 0


if __name__ == "__main__":
    sys.exit(main())
