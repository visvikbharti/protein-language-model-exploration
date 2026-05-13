"""Build FnCas9-PLM3: top-K design over the entire PI/WED design space.

Differences from build_candidate_v2.py:
  - No 21-residue hotspot windows. The design space is the full WED+PI
    region (residues 1230-1620 by default), letting the model propose
    mutations anywhere within that 391-residue range.
  - Picks the top-K mutations (default K=4) under the composite score
    `LLR - lambda * class_conservation`, subject to:
        * each picked position is distinct (no two muts at the same residue)
        * class_conservation < --max-class-conservation
        * LLR > 0  (strictly preferred over WT by the model)
  - Optionally enforces a "minimum-spacing" constraint so picks aren't all
    clumped at one local hotspot — default 5 residues apart.

This is the right candidate-builder to use with the full PI-domain ESM-2
650M scan from results/runs/<date>_esm2_650M_full_PI_hpc/scores.tsv.
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
from nuclease_design.scoring.conservation import (
    DEFAULT_ORTHOLOG_FILES,
    compute_conservation,
    load_orthologs_from_dir,
)
from nuclease_design.variants import Variant, apply_mutant, mutant_str, parse_mutant


EN31_REFERENCE = parse_mutant("G1243T/E1369R/E1449H")
EN15_REFERENCE = parse_mutant("E1603H")


def load_scores(tsv_path: Path) -> list[tuple[Variant, float]]:
    out: list[tuple[Variant, float]] = []
    with tsv_path.open() as f:
        next(f)
        for line in f:
            pos, wt, mut, _vname, llr = line.rstrip().split("\t")
            out.append((Variant(wt=wt, pos=int(pos), mut=mut), float(llr)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True,
                        help="scores.tsv from the broad ESM-2 scan")
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output-dir",
                        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_candidates_v3")
    parser.add_argument("--design-region", default="1230-1620",
                        help="Allowed residue range, e.g. 1230-1620")
    parser.add_argument("--top-k", type=int, default=4,
                        help="How many mutations to combine into the candidate")
    parser.add_argument("--max-class-conservation", type=float, default=0.5,
                        help="Reject mutations at positions with class_cons >= this")
    parser.add_argument("--lambda-cons", type=float, default=1.0,
                        help="Weight on class_conservation in the composite score")
    parser.add_argument("--min-spacing", type=int, default=5,
                        help="Minimum residue spacing between selected positions")
    parser.add_argument("--require-positive-llr", action="store_true", default=True)
    args = parser.parse_args()

    region_lo, region_hi = (int(x) for x in args.design_region.split("-"))
    log.info("Design region: %d-%d (%d positions)", region_lo, region_hi, region_hi - region_lo + 1)

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    log.info("FnCas9: %d aa", len(fncas9))

    scores = load_scores(Path(args.scores))
    log.info("Loaded %d scored variants", len(scores))

    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)
    cons_full = compute_conservation(fncas9, orthologs)
    cons_by_pos = {c.position: c.class_conservation for c in cons_full}

    # Filter and rank
    region_scores = [
        (v, llr) for v, llr in scores
        if region_lo <= v.pos <= region_hi
    ]
    log.info("Scores in design region: %d", len(region_scores))

    candidates = []
    for v, llr in region_scores:
        cc = cons_by_pos.get(v.pos, 0.0)
        if cc >= args.max_class_conservation:
            continue
        if args.require_positive_llr and llr <= 0:
            continue
        composite = llr - args.lambda_cons * cc
        candidates.append((v, llr, cc, composite))
    candidates.sort(key=lambda x: -x[3])
    log.info("After filter (class_cons<%.2f, llr>0): %d candidates",
             args.max_class_conservation, len(candidates))

    # Top-K with distinct positions and minimum spacing
    chosen: list[tuple[Variant, float, float, float]] = []
    used_positions: list[int] = []
    for v, llr, cc, comp in candidates:
        if any(abs(v.pos - p) < args.min_spacing for p in used_positions):
            continue
        chosen.append((v, llr, cc, comp))
        used_positions.append(v.pos)
        if len(chosen) >= args.top_k:
            break

    log.info("\n=== FnCas9-PLM3 selection ===")
    for v, llr, cc, comp in chosen:
        log.info("  %-8s  LLR=%+.3f  class_cons=%.2f  composite=%+.3f",
                 str(v), llr, cc, comp)

    if len(chosen) < args.top_k:
        log.warning("Could only find %d candidates passing all filters (wanted %d)",
                    len(chosen), args.top_k)

    plm3_mutant = tuple(v for v, _, _, _ in chosen)
    plm3_seq = apply_mutant(fncas9, plm3_mutant)
    plm3_str = mutant_str(plm3_mutant)
    log.info("\nFnCas9-PLM3 mutations: %s", plm3_str)

    # Retrospective check on en31 ranking IN THIS BROADER POOL
    log.info("\n=== Retrospective rank of reference mutations in broader pool ===")
    composite_all = [
        (v, llr - args.lambda_cons * cons_by_pos.get(v.pos, 0.0))
        for v, llr in region_scores
    ]
    composite_all.sort(key=lambda x: -x[1])
    rank_map = {str(v): i + 1 for i, (v, _) in enumerate(composite_all)}
    n_total = len(composite_all)
    for ref in list(EN31_REFERENCE) + list(EN15_REFERENCE):
        r = rank_map.get(str(ref), None)
        if r:
            quartile = "top quartile" if r <= n_total / 4 else "Q2" if r <= n_total / 2 else "Q3" if r <= 3 * n_total / 4 else "bottom"
            log.info("  %s  composite rank %d/%d  (%s)", ref, r, n_total, quartile)

    # Write outputs
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_fasta(
        [
            FastaRecord(
                header=f"FnCas9-PLM3 broad-PI design; {plm3_str}",
                sequence=plm3_seq,
            ),
            FastaRecord(header="FnCas9-WT", sequence=fncas9),
            FastaRecord(
                header="FnCas9-en31 G1243T/E1369R/E1449H",
                sequence=apply_mutant(fncas9, EN31_REFERENCE),
            ),
            FastaRecord(
                header="FnCas9-en15 E1603H",
                sequence=apply_mutant(fncas9, EN15_REFERENCE),
            ),
        ],
        out_dir / "fncas9_variants_v3.fasta",
    )
    log.info("Wrote %s", out_dir / "fncas9_variants_v3.fasta")

    meta = {
        "candidate_name": "FnCas9-PLM3",
        "mutations": plm3_str,
        "design_region": args.design_region,
        "top_k": args.top_k,
        "max_class_conservation": args.max_class_conservation,
        "lambda_cons": args.lambda_cons,
        "min_spacing": args.min_spacing,
        "selection": [
            {"variant": str(v), "llr": llr, "class_cons": cc, "composite": comp}
            for v, llr, cc, comp in chosen
        ],
        "source_scan": str(Path(args.scores).parent.name),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "FnCas9-PLM3.meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Wrote %s", out_dir / "FnCas9-PLM3.meta.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
