"""Cross-validation: compare ESM-2 35M vs 650M zero-shot scoring on positive,
negative, and neutral control mutations, with cross-reference to conservation.

Positive controls: en31, en15, en1 published functional mutations.
Negative controls: predicted-disruptive single mutations drawn from the same
    saturation scan — chosen for biophysical implausibility:
    - Glycine at structurally tight positions (loss of sidechain at conserved residues)
    - Tryptophan at positions where it would be sterically excluded
    - Charge reversal at family-conserved charged positions
Neutral controls: conservative substitutions at clearly variable surface
    positions (low conservation, BLOSUM-positive substitution).

The script tabulates each control's LLR under both 35M and 650M, the
class-conservation score, and assigns category labels. The expected pattern:
    positive_mean > neutral_mean > negative_mean  (one-sided)
with 650M producing a stronger separation than 35M.
"""
from __future__ import annotations

import argparse
import logging
import statistics
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


# Categories. Format: variant_str -> rationale.
POSITIVE = {
    "G1243T": "en31, WED-PLL (functional, +cleavage)",
    "E1369R": "en1+en31, PI PAM (functional, expanded PAM)",
    "E1449H": "en31, PI PAM (functional, PAM stabilisation)",
    "E1603H": "en15, PI/WED (functional, single-mutation variant)",
}

NEGATIVE = {
    # Charge loss/reversal at PAM-contact (should disrupt PAM readout)
    "E1369A": "loss of PAM-contact charge",
    "E1369K": "PAM-contact charge reversal (E→K, unlike en31's E→R)",
    "R1367E": "reverse PI conserved positive charge",
    # Aromatic loss at conserved tryptophan (should disrupt RNA stacking)
    "W1459A": "loss of conserved aromatic at RNA contact",
    "W1459G": "extreme loss of conserved aromatic at RNA contact",
    # Glycine introduction at structured residues (should break local fold)
    "L1450G": "Gly in PI helix (presumed structured)",
    "V1366G": "Gly at conserved residue near PAM contact",
    # Proline in helix center (helix-breaker)
    "K1370P": "Pro after PAM-contact E1369",
}

NEUTRAL = {
    # Conservative substitutions at presumed-variable positions
    # (we'll require class_conservation ≤ 0.4 to confirm)
    "S1242T": "conservative S→T",
    "K1244R": "conservative K→R (same charge class)",
    "N1448D": "conservative N→D (similar polarity)",
    "T1607S": "conservative T→S",
}


def load_scores(tsv_path: Path) -> dict[str, float]:
    """Load scores.tsv → {variant_str: llr} dict."""
    out: dict[str, float] = {}
    with tsv_path.open() as f:
        next(f)
        for line in f:
            parts = line.rstrip().split("\t")
            v_name = parts[3]
            llr = float(parts[4])
            out[v_name] = llr
    return out


def position_rank(scores: dict[str, float], variant: str) -> tuple[int, int]:
    """Return (position_rank_1indexed, n_at_position) for the variant.

    Among all 19 substitutions at this position, what's the rank of this variant?
    """
    pos = int(variant[1:-1])
    same_pos = [(v, s) for v, s in scores.items() if int(v[1:-1]) == pos]
    same_pos.sort(key=lambda x: -x[1])
    for i, (v, _) in enumerate(same_pos):
        if v == variant:
            return i + 1, len(same_pos)
    return -1, len(same_pos)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores-35m", required=True)
    parser.add_argument("--scores-650m", required=True)
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_cross_validation",
    )
    args = parser.parse_args()

    s35 = load_scores(Path(args.scores_35m))
    s650 = load_scores(Path(args.scores_650m))
    log.info("35M: %d variants; 650M: %d variants", len(s35), len(s650))

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)
    log.info("Computing conservation across %d orthologs...", len(orthologs))
    cons = compute_conservation(fncas9, orthologs)

    rows: list[dict] = []
    for category, group in [("POSITIVE", POSITIVE), ("NEGATIVE", NEGATIVE), ("NEUTRAL", NEUTRAL)]:
        for variant, rationale in group.items():
            pos = int(variant[1:-1])
            llr35 = s35.get(variant)
            llr650 = s650.get(variant)
            rank35 = position_rank(s35, variant) if llr35 is not None else (-1, -1)
            rank650 = position_rank(s650, variant) if llr650 is not None else (-1, -1)
            c = cons[pos - 1]
            rows.append({
                "category": category,
                "variant": variant,
                "rationale": rationale,
                "pos": pos,
                "wt": variant[0],
                "mut": variant[-1],
                "llr_35M": llr35,
                "llr_650M": llr650,
                "rank_35M_at_pos": rank35[0],
                "rank_650M_at_pos": rank650[0],
                "id_conservation": c.identity_conservation,
                "class_conservation": c.class_conservation,
            })

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tsv = out_dir / "cross_validation.tsv"
    with tsv.open("w") as f:
        cols = ["category", "variant", "wt", "mut", "pos",
                "llr_35M", "rank_35M_at_pos",
                "llr_650M", "rank_650M_at_pos",
                "id_conservation", "class_conservation", "rationale"]
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(
                f"{r[c]:.3f}" if isinstance(r[c], float)
                else "" if r[c] is None
                else str(r[c])
                for c in cols
            ) + "\n")
    log.info("Wrote %s", tsv)

    # Print summary
    log.info("\n=== Cross-validation table ===")
    log.info(f"{'Variant':<8} {'Cat':<8} {'WT':<3} {'LLR_35M':>10} {'r/19':>5} "
             f"{'LLR_650M':>10} {'r/19':>5} {'id_c':>6} {'cls_c':>6}")
    log.info("-" * 90)
    for r in rows:
        v = r["variant"]
        cat = r["category"][:3]
        llr35 = "    n/a" if r["llr_35M"] is None else f"{r['llr_35M']:+8.3f}"
        llr650 = "    n/a" if r["llr_650M"] is None else f"{r['llr_650M']:+8.3f}"
        r35 = f"{r['rank_35M_at_pos']}/19" if r["rank_35M_at_pos"] > 0 else " n/a"
        r650 = f"{r['rank_650M_at_pos']}/19" if r["rank_650M_at_pos"] > 0 else " n/a"
        log.info(f"{v:<8} {cat:<8} {r['wt']:<3} {llr35:>10} {r35:>5} "
                 f"{llr650:>10} {r650:>5} "
                 f"{r['id_conservation']:>6.2f} {r['class_conservation']:>6.2f}")

    # Statistics per category
    log.info("\n=== Category statistics ===")
    for cat in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        cat_rows = [r for r in rows if r["category"] == cat]
        llrs_35 = [r["llr_35M"] for r in cat_rows if r["llr_35M"] is not None]
        llrs_650 = [r["llr_650M"] for r in cat_rows if r["llr_650M"] is not None]
        log.info("%s (n=%d):", cat, len(cat_rows))
        if llrs_35:
            log.info("  35M  LLR mean=%+0.3f  stdev=%0.3f  min=%+0.3f  max=%+0.3f",
                     statistics.mean(llrs_35),
                     statistics.stdev(llrs_35) if len(llrs_35) > 1 else 0.0,
                     min(llrs_35), max(llrs_35))
        if llrs_650:
            log.info("  650M LLR mean=%+0.3f  stdev=%0.3f  min=%+0.3f  max=%+0.3f",
                     statistics.mean(llrs_650),
                     statistics.stdev(llrs_650) if len(llrs_650) > 1 else 0.0,
                     min(llrs_650), max(llrs_650))

    # Pre-registered hypothesis check (Phase 2 plan §H1)
    log.info("\n=== Pre-registered hypothesis check (H1: 650M improves over 35M) ===")
    pos_650 = [r["llr_650M"] for r in rows
               if r["category"] == "POSITIVE" and r["llr_650M"] is not None]
    neg_650 = [r["llr_650M"] for r in rows
               if r["category"] == "NEGATIVE" and r["llr_650M"] is not None]
    pos_35 = [r["llr_35M"] for r in rows
              if r["category"] == "POSITIVE" and r["llr_35M"] is not None]
    neg_35 = [r["llr_35M"] for r in rows
              if r["category"] == "NEGATIVE" and r["llr_35M"] is not None]
    if pos_35 and neg_35:
        log.info("35M separation (pos_mean − neg_mean): %+.3f",
                 statistics.mean(pos_35) - statistics.mean(neg_35))
    if pos_650 and neg_650:
        log.info("650M separation (pos_mean − neg_mean): %+.3f",
                 statistics.mean(pos_650) - statistics.mean(neg_650))
    log.info("Pass criterion: 650M separation > 1.0 and > 35M separation.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
