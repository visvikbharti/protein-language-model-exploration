"""Score FnCas9 catalytic-residue mutations as a ground-truth negative control.

A well-calibrated PLM fitness scorer should produce strongly negative LLR for
mutations that destroy catalytic activity. We score loss-of-function variants
at FnCas9's two catalytic centres:

  - RuvC nuclease: D11 (canonical Mg2+-coordinating aspartate)
  - HNH nuclease:  H969 and H975 (canonical HNH motif "L-D-H..." starts at L967)

X→A and X→G mutations are the standard catalytic-dead substitutions.

If ESM-2 35M and 650M give strongly negative LLRs (< -1) for these mutations,
the model has some biology-awareness. If they score near zero or positive,
ESM-2 zero-shot is even less reliable than the Phase 2 cross-validation
already suggested.

Both models are used (no new big saturation scan — we just score these
specific mutations).
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta
from nuclease_design.scoring.esm import ESMScorer
from nuclease_design.variants import Variant


CATALYTIC_CONTROLS: list[tuple[str, str]] = [
    ("D11A",   "RuvC catalytic Asp → Ala (canonical loss-of-function)"),
    ("D11G",   "RuvC catalytic Asp → Gly"),
    ("D11N",   "RuvC catalytic Asp → Asn (similar shape, loses charge)"),
    ("H969A",  "HNH catalytic His → Ala"),
    ("H969N",  "HNH catalytic His → Asn"),
    ("H975A",  "HNH motif second His → Ala"),
]


def main() -> int:
    fasta = load_fasta(Path("data/raw/A0Q5Y3_fncas9.fasta"))
    seq = fasta[0].sequence
    log.info("FnCas9 length: %d", len(seq))

    # Sanity check WT identity
    for v_str, _ in CATALYTIC_CONTROLS:
        v = Variant.parse(v_str)
        actual_wt = seq[v.pos - 1]
        if actual_wt != v.wt:
            log.error("WT mismatch at %s: sequence has %s", v_str, actual_wt)
            return 1
    log.info("All catalytic-control WT residues match the sequence.")

    out_dir = Path(f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_catalytic_controls")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    for model_name in ["esm2_35M", "esm2_650M"]:
        log.info("\n=== Scoring with %s ===", model_name)
        scorer = ESMScorer(name=model_name, device="cpu")
        positions = sorted({Variant.parse(v).pos for v, _ in CATALYTIC_CONTROLS})
        log_probs = scorer.score_single(seq, positions)
        assert scorer._alphabet is not None
        aa_to_tok = {aa: scorer._alphabet.get_idx(aa) for aa in "ACDEFGHIKLMNPQRSTVWY"}
        for v_str, rationale in CATALYTIC_CONTROLS:
            v = Variant.parse(v_str)
            lp = log_probs[v.pos]
            wt_logp = float(lp[aa_to_tok[v.wt]])
            mut_logp = float(lp[aa_to_tok[v.mut]])
            llr = mut_logp - wt_logp
            # Position rank
            same_pos_llrs = sorted(
                [(aa, float(lp[aa_to_tok[aa]]) - wt_logp) for aa in "ACDEFGHIKLMNPQRSTVWY" if aa != v.wt],
                key=lambda x: -x[1],
            )
            rank = next(i for i, (aa, _) in enumerate(same_pos_llrs, start=1) if aa == v.mut)
            log.info("  %-7s  LLR=%+.3f  rank %d/19", v_str, llr, rank)
            key = f"{v_str}_{model_name}"
            results[key] = {"variant": v_str, "model": model_name, "llr": llr, "rank": rank}

    # Write summary
    tsv = out_dir / "catalytic_controls.tsv"
    with tsv.open("w") as f:
        f.write("variant\trationale\t35M_llr\t35M_rank\t650M_llr\t650M_rank\n")
        for v_str, rationale in CATALYTIC_CONTROLS:
            r35 = results[f"{v_str}_esm2_35M"]
            r650 = results[f"{v_str}_esm2_650M"]
            f.write(f"{v_str}\t{rationale}\t{r35['llr']:+.3f}\t{r35['rank']}\t"
                    f"{r650['llr']:+.3f}\t{r650['rank']}\n")
    log.info("\nWrote %s", tsv)

    # Verdict
    n_strongly_neg = sum(
        1 for v_str, _ in CATALYTIC_CONTROLS
        if results[f"{v_str}_esm2_650M"]["llr"] < -1.0
    )
    log.info("\n=== Verdict ===")
    log.info("%d / %d catalytic-control mutations have LLR < -1.0 under 650M.",
             n_strongly_neg, len(CATALYTIC_CONTROLS))
    if n_strongly_neg >= 4:
        log.info("✓ Most catalytic mutations are correctly dispreferred (LLR << 0).")
        log.info("  ESM-2 650M has some biology-awareness for active-site mutations.")
    else:
        log.info("✗ Most catalytic mutations are NOT dispreferred under ESM-2 650M.")
        log.info("  Confirms that ESM-2 sequence-only is unreliable for functional scoring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
