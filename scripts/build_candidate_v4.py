"""Build FnCas9-PLM4: top-K design from LigandMPNN posterior over the PI region.

Reads the aggregate.tsv produced by scripts/ligandmpnn_aggregate.py and picks
the K mutations with highest composite score:

    composite = log( top_freq_pooled / wt_freq_pooled ) - lambda * class_cons

subject to the same hard filters as v3:
  - top_aa_pooled differs from WT
  - top_freq_pooled exceeds --min-top-freq (default 0.30 — i.e. LigandMPNN
    samples agree at least 30% of the time)
  - wt_freq_pooled below --max-wt-freq (default 0.40 — WT no longer dominant)
  - class_conservation < --max-class-conservation
  - distinct positions, spaced >= --min-spacing residues apart

This is the structure-conditioned counterpart of v3. Compare PLM4 to PLM3 to
see how much structure/ligand context changes which positions get picked.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import FastaRecord, load_fasta, write_fasta
from nuclease_design.scoring.conservation import (
    DEFAULT_ORTHOLOG_FILES,
    compute_conservation,
    load_orthologs_from_dir,
)
from nuclease_design.variants import Variant, apply_mutant, mutant_str, parse_mutant


EN31_REFERENCE = parse_mutant("G1243T/E1369R/E1449H")
EN15_REFERENCE = parse_mutant("E1603H")


def load_aggregate(tsv_path: Path) -> list[dict]:
    """Returns one dict per row of aggregate.tsv (pos, wt, top_aa_pooled, ...)."""
    rows: list[dict] = []
    with tsv_path.open() as f:
        header = f.readline().rstrip().split("\t")
        for line in f:
            parts = line.rstrip().split("\t")
            row = dict(zip(header, parts))
            row["pos"] = int(row["pos"])
            for k in row:
                if k.startswith(("wt_freq", "top_freq", "freq_pooled_")):
                    row[k] = float(row[k])
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate", required=True,
                        help="aggregate.tsv from ligandmpnn_aggregate.py")
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output-dir",
                        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_candidates_v4")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--min-top-freq", type=float, default=0.30,
                        help="Reject positions where the top non-WT aa has < this pooled freq")
    parser.add_argument("--max-wt-freq", type=float, default=0.40,
                        help="Reject positions where WT still has > this pooled freq")
    parser.add_argument("--max-class-conservation", type=float, default=0.5)
    parser.add_argument("--lambda-cons", type=float, default=1.0)
    parser.add_argument("--min-spacing", type=int, default=5)
    args = parser.parse_args()

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    log.info("FnCas9: %d aa", len(fncas9))

    rows = load_aggregate(Path(args.aggregate))
    log.info("Aggregate rows (design positions): %d", len(rows))

    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)
    cons_full = compute_conservation(fncas9, orthologs)
    cons_by_pos = {c.position: c.class_conservation for c in cons_full}

    # Candidate filtering
    candidates: list[tuple[Variant, float, float, float, float]] = []
    for row in rows:
        pos = row["pos"]
        wt = row["wt"]
        top_aa = row["top_aa_pooled"]
        top_freq = row["top_freq_pooled"]
        wt_freq = row["wt_freq_pooled"]
        if top_aa == wt:
            continue
        if top_freq < args.min_top_freq:
            continue
        if wt_freq > args.max_wt_freq:
            continue
        cc = cons_by_pos.get(pos, 0.0)
        if cc >= args.max_class_conservation:
            continue
        # Use log odds for scoring (more comparable across positions than raw freq)
        # Add 1e-3 floor on wt_freq to avoid log(0).
        log_odds = math.log(top_freq / max(wt_freq, 1e-3))
        composite = log_odds - args.lambda_cons * cc
        candidates.append((Variant(wt=wt, pos=pos, mut=top_aa),
                           top_freq, wt_freq, cc, composite))
    candidates.sort(key=lambda x: -x[4])
    log.info("After filters (top_freq>=%.2f, wt_freq<=%.2f, class_cons<%.2f): %d candidates",
             args.min_top_freq, args.max_wt_freq, args.max_class_conservation,
             len(candidates))

    chosen: list[tuple[Variant, float, float, float, float]] = []
    used_positions: list[int] = []
    for v, top_f, wt_f, cc, comp in candidates:
        if any(abs(v.pos - p) < args.min_spacing for p in used_positions):
            continue
        chosen.append((v, top_f, wt_f, cc, comp))
        used_positions.append(v.pos)
        if len(chosen) >= args.top_k:
            break

    log.info("\n=== FnCas9-PLM4 selection (LigandMPNN structure-conditioned) ===")
    for v, top_f, wt_f, cc, comp in chosen:
        log.info("  %-8s  top_freq=%.3f  wt_freq=%.3f  class_cons=%.2f  composite=%+.3f",
                 str(v), top_f, wt_f, cc, comp)

    if len(chosen) < args.top_k:
        log.warning("Only found %d candidates passing all filters (wanted %d)",
                    len(chosen), args.top_k)
        if not chosen:
            log.error("No candidates passed filters — try relaxing --min-top-freq or --max-wt-freq")
            return 1

    plm4_mutant = tuple(v for v, _, _, _, _ in chosen)
    plm4_seq = apply_mutant(fncas9, plm4_mutant)
    plm4_str = mutant_str(plm4_mutant)
    log.info("\nFnCas9-PLM4 mutations: %s", plm4_str)

    # Retrospective check: LigandMPNN's posterior on en31/en15 mutations
    log.info("\n=== en31/en15 mutations under LigandMPNN posterior ===")
    row_by_pos = {row["pos"]: row for row in rows}
    for ref in list(EN31_REFERENCE) + list(EN15_REFERENCE):
        row = row_by_pos.get(ref.pos)
        if row is None:
            log.info("  %s: position not in design region", ref)
            continue
        freq_target = row[f"freq_pooled_{ref.mut}"]
        freq_wt = row["wt_freq_pooled"]
        log.info("  %s: target_freq=%.3f, wt_freq=%.3f, top_aa=%s (freq=%.3f)",
                 ref, freq_target, freq_wt,
                 row["top_aa_pooled"], row["top_freq_pooled"])

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_fasta(
        [
            FastaRecord(header=f"FnCas9-PLM4 LigandMPNN structure-conditioned; {plm4_str}",
                        sequence=plm4_seq),
            FastaRecord(header="FnCas9-WT", sequence=fncas9),
            FastaRecord(header="FnCas9-en31 G1243T/E1369R/E1449H",
                        sequence=apply_mutant(fncas9, EN31_REFERENCE)),
            FastaRecord(header="FnCas9-en15 E1603H",
                        sequence=apply_mutant(fncas9, EN15_REFERENCE)),
        ],
        out_dir / "fncas9_variants_v4.fasta",
    )
    log.info("Wrote %s", out_dir / "fncas9_variants_v4.fasta")

    meta = {
        "candidate_name": "FnCas9-PLM4",
        "mutations": plm4_str,
        "source": "LigandMPNN structure-conditioned design",
        "aggregate_tsv": str(args.aggregate),
        "top_k": args.top_k,
        "min_top_freq": args.min_top_freq,
        "max_wt_freq": args.max_wt_freq,
        "max_class_conservation": args.max_class_conservation,
        "lambda_cons": args.lambda_cons,
        "min_spacing": args.min_spacing,
        "selection": [
            {"variant": str(v), "top_freq": tf, "wt_freq": wf,
             "class_cons": cc, "composite": comp}
            for v, tf, wf, cc, comp in chosen
        ],
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "FnCas9-PLM4.meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Wrote %s", out_dir / "FnCas9-PLM4.meta.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
