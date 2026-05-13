"""Build FnCas9-PLM1 candidate variant from the ESM-2 saturation scan.

Strategy:
  1. Read scores.tsv from a saturation run.
  2. From each of the four hotspot windows, pick the single highest-LLR mutation.
  3. Form a 4-mutation candidate "FnCas9-PLM1" (one mutation per region —
     parallels enFnCas9 en31 which has three but one is in each region).
  4. Apply to WT, save as FASTA.
  5. Compare to en31 sequence (also constructed) and report.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import FastaRecord, load_fasta, write_fasta
from nuclease_design.variants import Variant, apply_mutant, mutant_str, parse_mutant


HOTSPOT_WINDOWS = {
    "WED_PLL_G1243": (1233, 1253),
    "PI_E1369": (1359, 1379),
    "PI_E1449": (1439, 1459),
    "PI_WED_E1603": (1593, 1613),
}


def load_scores(tsv_path: Path) -> list[tuple[Variant, float]]:
    out: list[tuple[Variant, float]] = []
    with tsv_path.open() as f:
        next(f)  # header
        for line in f:
            pos, wt, mut, _vname, llr = line.rstrip().split("\t")
            out.append((Variant(wt=wt, pos=int(pos), mut=mut), float(llr)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True, help="Path to scores.tsv from saturation scan")
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_candidates",
    )
    args = parser.parse_args()

    records = load_fasta(Path(args.fasta))
    wt_seq = records[0].sequence
    scores = load_scores(Path(args.scores))
    score_by_var = {str(v): llr for v, llr in scores}

    # Top mutation in each window
    chosen: list[Variant] = []
    log.info("=== Selecting top mutation per window ===")
    for window_name, (lo, hi) in HOTSPOT_WINDOWS.items():
        candidates = [(v, s) for v, s in scores if lo <= v.pos <= hi]
        if not candidates:
            log.warning("No candidates in window %s (%d-%d)", window_name, lo, hi)
            continue
        candidates.sort(key=lambda x: -x[1])
        top_var, top_llr = candidates[0]
        log.info("  %-15s  top: %s  LLR=%+.3f", window_name, top_var, top_llr)
        chosen.append(top_var)

    # Build PLM1
    plm1_mutant = tuple(chosen)
    plm1_seq = apply_mutant(wt_seq, plm1_mutant)
    plm1_str = mutant_str(plm1_mutant)
    log.info("\nFnCas9-PLM1 mutations: %s", plm1_str)
    log.info("FnCas9-PLM1 length: %d", len(plm1_seq))

    # Construct reference variants for comparison
    en1 = parse_mutant("E1369R")
    en15 = parse_mutant("E1603H")
    en31 = parse_mutant("G1243T/E1369R/E1449H")

    en1_seq = apply_mutant(wt_seq, en1)
    en15_seq = apply_mutant(wt_seq, en15)
    en31_seq = apply_mutant(wt_seq, en31)

    # Output
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_fasta(
        [
            FastaRecord(
                header=f"FnCas9-PLM1 PLM-designed FnCas9 variant; mutations={plm1_str}",
                sequence=plm1_seq,
            ),
            FastaRecord(
                header="FnCas9-WT canonical FnCas9 from UniProt A0Q5Y3",
                sequence=wt_seq,
            ),
            FastaRecord(
                header="FnCas9-en1 E1369R (Acharya 2024)",
                sequence=en1_seq,
            ),
            FastaRecord(
                header="FnCas9-en15 E1603H (Acharya 2024)",
                sequence=en15_seq,
            ),
            FastaRecord(
                header="FnCas9-en31 G1243T/E1369R/E1449H (Acharya 2024)",
                sequence=en31_seq,
            ),
        ],
        out_dir / "fncas9_variants.fasta",
    )
    log.info("\nWrote %s", out_dir / "fncas9_variants.fasta")

    # ESM scores of the en mutations for context
    log.info("\n=== Reference variant scores (from same saturation scan) ===")
    for v_str in ["G1243T", "E1369R", "E1449H", "E1603H"]:
        if v_str in score_by_var:
            log.info("  %s  LLR=%+.3f", v_str, score_by_var[v_str])

    # Sum LLR of PLM1 vs en31
    plm1_total = sum(score_by_var[str(v)] for v in plm1_mutant)
    en31_total = sum(score_by_var[str(v)] for v in en31 if str(v) in score_by_var)
    log.info("\n=== PLM1 vs en31 (sum of single-mutant LLRs; independence approx) ===")
    log.info("  FnCas9-PLM1 sum LLR: %+.3f  (%s)", plm1_total, plm1_str)
    log.info("  FnCas9-en31 sum LLR: %+.3f  (G1243T/E1369R/E1449H)", en31_total)
    log.info("  Δ (PLM1 - en31):     %+.3f", plm1_total - en31_total)

    # Meta
    meta = {
        "candidate_name": "FnCas9-PLM1",
        "mutations": plm1_str,
        "per_mutation_llr": {str(v): score_by_var[str(v)] for v in plm1_mutant},
        "sum_llr": plm1_total,
        "en31_sum_llr": en31_total,
        "source_scan": str(Path(args.scores).parent.name),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "FnCas9-PLM1.meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Wrote %s", out_dir / "FnCas9-PLM1.meta.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
