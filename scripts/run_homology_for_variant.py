"""Re-run the full sequence + structural-context + cross-ortholog homology
analyses for any FnCas9 variant (PLM1, PLM2, or future). Thin orchestrator
that just calls the three already-existing analysis scripts.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/run_homology_for_variant.py \\
        --variants results/runs/2026-05-13_candidates_v2/fncas9_variants_v2.fasta \\
        --meta     results/runs/2026-05-13_candidates_v2/FnCas9-PLM2.meta.json \\
        --label    PLM2
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def run(cmd: list[str]) -> int:
    log.info(">>> %s", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--label", required=True, help="Suffix for output dirs (e.g. PLM2)")
    parser.add_argument("--python", default=".venv/bin/python")
    args = parser.parse_args()

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    env = {"PYTHONPATH": "src"}
    import os
    full_env = {**os.environ, **env}

    seq_out = Path(f"results/runs/{date}_homology_{args.label}")
    struct_out = Path(f"results/runs/{date}_structure_{args.label}")
    cross_out = Path(f"results/runs/{date}_cross_ortholog_{args.label}")

    # 1. Sequence homology
    log.info("\n=== Sequence homology (%s) ===", args.label)
    if subprocess.call(
        [args.python, "scripts/run_sequence_homology.py",
         "--variants", args.variants, "--output-dir", str(seq_out)],
        env=full_env,
    ) != 0:
        log.error("Sequence homology failed")
        return 1

    # 2. Structural context (PDB 5B2O)
    log.info("\n=== Structural context (%s) ===", args.label)
    if subprocess.call(
        [args.python, "scripts/run_structure_analysis.py",
         "--plm1-meta", args.meta,  # script accepts arbitrary meta with `mutations` key
         "--output-dir", str(struct_out)],
        env=full_env,
    ) != 0:
        log.error("Structural analysis failed")
        return 1

    # 3. Cross-ortholog residue mapping — note this script uses hardcoded sites
    # (PLM1 + en31 + en15). For PLM2 the user can either edit the script's SITES
    # dict or accept the existing PLM1-focused mapping (which still covers en31).
    log.info("\n=== Cross-ortholog residue mapping (existing PLM1-focused) ===")
    if subprocess.call(
        [args.python, "scripts/map_residues_across_orthologs.py",
         "--output-dir", str(cross_out)],
        env=full_env,
    ) != 0:
        log.error("Cross-ortholog mapping failed")
        return 1

    log.info("\n=== All %s homology analyses written ===", args.label)
    log.info("  %s", seq_out)
    log.info("  %s", struct_out)
    log.info("  %s", cross_out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
