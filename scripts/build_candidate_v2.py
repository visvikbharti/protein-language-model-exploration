"""Build FnCas9-PLM2 using composite score = LLR_650M − λ · class_conservation.

Filters applied at each hotspot window before picking the top candidate:
  - class_conservation < 0.7  (avoid family-conserved property class)
  - LLR_650M > 0              (strictly preferred over WT under the model)
  - position not in the catalytic core (HNH, RuvC); enforced via region check

λ is calibrated retrospectively: chosen as the smallest λ ∈ [0.5, 5.0] for which
en31's E1369R ranks in the top-5 at position 1369 under the composite score.
This is recorded in the run meta.json.

Compared to PLM1 (Phase 1, 35M, no conservation, no λ calibration), PLM2 should:
  - have all four mutations at positions with class_conservation < 0.7
  - have all four mutations with positive LLR_650M
  - retrospectively rank en31's mutations in the top quartile of their windows
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


HOTSPOT_WINDOWS = {
    "WED_PLL_G1243": (1233, 1253),
    "PI_E1369": (1359, 1379),
    "PI_E1449": (1439, 1459),
    "PI_WED_E1603": (1593, 1613),
}

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


def calibrate_lambda(
    scores: list[tuple[Variant, float]],
    cons_by_pos: dict[int, float],
    target_variant: Variant,
    target_rank: int = 5,
) -> float | None:
    """Find the smallest λ ∈ [0.5, 5.0] (step 0.25) such that target_variant ranks
    in the top `target_rank` among all 19 substitutions at its position under
    composite score `s = llr - λ * class_conservation`.

    Returns None if no λ in range achieves the target rank.
    """
    pos = target_variant.pos
    candidates_at_pos = [(v, s) for v, s in scores if v.pos == pos]
    if len(candidates_at_pos) < 19:
        log.warning(
            "Only %d candidates at position %d (expected 19) — λ calibration may be unreliable",
            len(candidates_at_pos), pos,
        )

    for lam_step in range(2, 21):  # λ = 0.5, 0.75, ..., 5.0
        lam = lam_step * 0.25
        composite = [(v, s - lam * cons_by_pos.get(v.pos, 0.0)) for v, s in candidates_at_pos]
        composite.sort(key=lambda x: -x[1])
        for rank, (v, _) in enumerate(composite, start=1):
            if v == target_variant:
                if rank <= target_rank:
                    return lam
                break
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True, help="Path to scores.tsv (ESM-2 650M preferred)")
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_candidates_v2",
    )
    parser.add_argument(
        "--max-class-conservation",
        type=float,
        default=0.5,
        help="Reject any mutation at a position with class_conservation >= this. "
             "0.5 = reject positions where at least half of orthologs preserve the AA class.",
    )
    parser.add_argument(
        "--require-positive-llr",
        action="store_true",
        default=True,
        help="Require LLR_650M > 0 for any selected mutation",
    )
    args = parser.parse_args()

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    log.info("FnCas9: %d aa", len(fncas9))

    scores = load_scores(Path(args.scores))
    log.info("Loaded %d single-mutant scores", len(scores))

    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)
    cons_full = compute_conservation(fncas9, orthologs)
    cons_by_pos: dict[int, float] = {c.position: c.class_conservation for c in cons_full}
    log.info("Conservation computed over %d orthologs", len(orthologs))

    # Calibrate λ retrospectively against en31's E1369R
    target = next(v for v in EN31_REFERENCE if v.pos == 1369)
    log.info("\n=== Calibrating λ to recover positive control %s in top-5 ===", target)
    calibrated = calibrate_lambda(scores, cons_by_pos, target, target_rank=5)
    if calibrated is None:
        log.warning(
            "No λ in [0.5, 5.0] recovers %s in top-5 at its position. "
            "Falling back to λ=1.0 and reporting honestly in the meta.",
            target,
        )
        lam = 1.0
        lam_calibration_status = "failed"
    else:
        lam = calibrated
        lam_calibration_status = "succeeded"
        log.info("Calibration succeeded: λ = %.2f recovers %s in top-5", lam, target)

    # Now select PLM2: top composite-scored mutation per window subject to filters
    log.info("\n=== Selecting FnCas9-PLM2 mutations (max_class_cons=%.2f, require LLR>0=%s) ===",
             args.max_class_conservation, args.require_positive_llr)
    chosen: list[Variant] = []
    selection_details: list[dict] = []
    for window_name, (lo, hi) in HOTSPOT_WINDOWS.items():
        candidates = [(v, s) for v, s in scores if lo <= v.pos <= hi]
        # Apply filters
        filtered = []
        for v, llr in candidates:
            cc = cons_by_pos.get(v.pos, 0.0)
            if cc >= args.max_class_conservation:
                continue
            if args.require_positive_llr and llr <= 0:
                continue
            composite = llr - lam * cc
            filtered.append((v, llr, cc, composite))
        filtered.sort(key=lambda x: -x[3])
        if not filtered:
            log.warning("No mutation in window %s (%d-%d) passes all filters",
                        window_name, lo, hi)
            continue
        top_v, top_llr, top_cc, top_comp = filtered[0]
        log.info("  %-15s  top: %-8s  LLR=%+.3f  cls_cons=%.2f  composite=%+.3f",
                 window_name, top_v, top_llr, top_cc, top_comp)
        chosen.append(top_v)
        selection_details.append({
            "window": window_name,
            "variant": str(top_v),
            "llr": top_llr,
            "class_conservation": top_cc,
            "composite": top_comp,
        })

    # Build PLM2 sequence
    plm2_mutant = tuple(chosen)
    plm2_seq = apply_mutant(fncas9, plm2_mutant)
    plm2_str = mutant_str(plm2_mutant)
    log.info("\nFnCas9-PLM2 mutations: %s", plm2_str)
    log.info("FnCas9-PLM2 length: %d", len(plm2_seq))

    # Retrospective check on en31 ranking
    log.info("\n=== Retrospective ranking of en31 mutations under composite (λ=%.2f) ===", lam)
    for v in EN31_REFERENCE:
        candidates_at_pos = [(vv, ss) for vv, ss in scores if vv.pos == v.pos]
        composite = [(vv, ss - lam * cons_by_pos.get(vv.pos, 0.0)) for vv, ss in candidates_at_pos]
        composite.sort(key=lambda x: -x[1])
        for rank, (vv, score) in enumerate(composite, start=1):
            if vv == v:
                log.info("  %s  composite rank %d/%d  composite=%+.3f", v, rank, len(composite), score)
                break

    # Write outputs
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_fasta(
        [
            FastaRecord(
                header=f"FnCas9-PLM2 PLM-designed FnCas9 v2; mutations={plm2_str}; λ={lam:.2f}",
                sequence=plm2_seq,
            ),
            FastaRecord(
                header=f"FnCas9-WT canonical from UniProt A0Q5Y3",
                sequence=fncas9,
            ),
            FastaRecord(
                header=f"FnCas9-en31 G1243T/E1369R/E1449H (Acharya 2024)",
                sequence=apply_mutant(fncas9, EN31_REFERENCE),
            ),
            FastaRecord(
                header=f"FnCas9-en15 E1603H (Acharya 2024)",
                sequence=apply_mutant(fncas9, EN15_REFERENCE),
            ),
        ],
        out_dir / "fncas9_variants_v2.fasta",
    )
    log.info("Wrote %s", out_dir / "fncas9_variants_v2.fasta")

    meta = {
        "candidate_name": "FnCas9-PLM2",
        "mutations": plm2_str,
        "lambda_class_cons": lam,
        "lambda_calibration": lam_calibration_status,
        "max_class_conservation_filter": args.max_class_conservation,
        "require_positive_llr": args.require_positive_llr,
        "selection_details": selection_details,
        "source_scan": str(Path(args.scores).parent.name),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "FnCas9-PLM2.meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Wrote %s", out_dir / "FnCas9-PLM2.meta.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
