"""ESM-2 zero-shot saturation scan over the FnCas9 WED-PI engineering hotspots.

Scans every non-identity substitution at four 21-residue windows centered on the
mutations defining en1 / en15 / en31:
    - G1243 ± 10  (WED, phosphate-lock loop region)
    - E1369 ± 10  (PI, PAM-contact 1)
    - E1449 ± 10  (PI, PAM-contact 2)
    - E1603 ± 10  (PI/WED interface, en15)

Total: 84 positions × 19 substitutions = 1596 single mutants.

Saves results to a Parquet file with columns: pos, wt, mut, llr.
Also writes meta.json with run provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta
from nuclease_design.scoring.esm import ESMScorer, score_saturation


HOTSPOT_WINDOWS = {
    "WED_PLL_G1243": (1233, 1253),
    "PI_E1369": (1359, 1379),
    "PI_E1449": (1439, 1459),
    "PI_WED_E1603": (1593, 1613),
}

EN31_MUTATIONS = ["G1243T", "E1369R", "E1449H"]
EN15_MUTATIONS = ["E1603H"]
EN1_MUTATIONS = ["E1369R"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="esm2_35M", help="ESM-2 checkpoint name")
    parser.add_argument("--device", default="cpu", help="cpu / cuda / mps")
    parser.add_argument(
        "--fasta",
        default="data/raw/A0Q5Y3_fncas9.fasta",
        help="WT FnCas9 FASTA",
    )
    parser.add_argument("--output-dir", default=None, help="Run output directory")
    args = parser.parse_args()

    fasta_path = Path(args.fasta)
    records = load_fasta(fasta_path)
    if len(records) != 1:
        log.error("Expected exactly 1 FASTA record, got %d", len(records))
        return 1
    seq = records[0].sequence
    log.info("WT FnCas9 length: %d", len(seq))

    # Build position list
    positions: list[int] = []
    for name, (lo, hi) in HOTSPOT_WINDOWS.items():
        positions.extend(range(lo, hi + 1))
    positions = sorted(set(positions))
    log.info("Scanning %d positions across 4 hotspot windows", len(positions))

    # Sanity check
    for v_str in EN31_MUTATIONS + EN15_MUTATIONS:
        from nuclease_design.variants import Variant
        v = Variant.parse(v_str)
        if seq[v.pos - 1] != v.wt:
            log.error("WT mismatch at %s: sequence has %s", v_str, seq[v.pos - 1])
            return 1
    log.info("All known reference mutations are consistent with the WT sequence.")

    # Load model and score
    scorer = ESMScorer(name=args.model, device=args.device)
    log.info("Starting ESM-2 saturation. This will load ~%s MB of weights on first run.",
             {"esm2_8M": 30, "esm2_35M": 150, "esm2_150M": 600, "esm2_650M": 2600}.get(args.model, "?"))
    sat = score_saturation(scorer, seq, positions)
    log.info("Scored %d variants", len(sat))

    # Write output
    out_dir_name = args.output_dir or f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_esm_saturation"
    out_dir = Path(out_dir_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    # TSV is more portable than parquet for our small dataset
    rows = [(v.pos, v.wt, v.mut, str(v), score) for v, score in sat]
    tsv_path = out_dir / "scores.tsv"
    with tsv_path.open("w") as f:
        f.write("pos\twt\tmut\tvariant\tllr\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]:.6f}\n")
    log.info("Wrote %s", tsv_path)

    # Print en31/en15/en1 ranks
    var_to_rank = {row[3]: i + 1 for i, row in enumerate(rows)}
    log.info("=== Reference-variant ranks (out of %d) ===", len(rows))
    for v_str in EN31_MUTATIONS + EN15_MUTATIONS:
        rank = var_to_rank.get(v_str, None)
        if rank:
            llr = next(r[4] for r in rows if r[3] == v_str)
            same_pos = [r for r in rows if r[0] == int(v_str[1:-1])]
            pos_rank = sorted(same_pos, key=lambda r: -r[4]).index(
                next(r for r in same_pos if r[3] == v_str)
            ) + 1
            log.info("  %s: global rank %d/%d, LLR=%+.3f, position rank %d/19",
                     v_str, rank, len(rows), llr, pos_rank)
        else:
            log.warning("  %s NOT found in results (position not scanned?)", v_str)

    # Top 20
    log.info("=== Top 20 PLM-suggested single mutations ===")
    for r in rows[:20]:
        is_en = ""
        if r[3] in EN31_MUTATIONS:
            is_en = "  ← en31"
        elif r[3] in EN15_MUTATIONS:
            is_en = "  ← en15"
        log.info("  %s  LLR=%+.3f%s", r[3], r[4], is_en)

    # Meta
    meta = {
        "run_name": out_dir.name,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "device": args.device,
        "fasta": str(fasta_path),
        "fasta_sha256": sha256_file(fasta_path),
        "n_positions": len(positions),
        "positions": positions,
        "windows": {k: list(v) for k, v in HOTSPOT_WINDOWS.items()},
        "n_variants_scored": len(rows),
    }
    meta_path = out_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    log.info("Wrote %s", meta_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
