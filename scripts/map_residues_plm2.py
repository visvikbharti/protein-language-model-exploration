"""Cross-ortholog residue mapping for the PLM2 mutation sites.

Same algorithm as map_residues_across_orthologs.py, but the SITES dict is built
from the PLM2 meta file and the en31 reference.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from Bio.Align import PairwiseAligner, substitution_matrices

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta
from nuclease_design.scoring.conservation import (
    DEFAULT_ORTHOLOG_FILES,
    compute_conservation,
    load_orthologs_from_dir,
)


def map_pos(aln, fncas9_seq: str, ortholog_seq: str, pos: int) -> tuple[str | None, int | None]:
    aligned = aln.aligned
    if aligned.shape[1] == 0:
        return None, None
    idx = pos - 1
    for (t_lo, t_hi), (q_lo, q_hi) in zip(aligned[0], aligned[1]):
        if t_lo <= idx < t_hi:
            q_idx = q_lo + (idx - t_lo)
            if 0 <= q_idx < len(ortholog_seq):
                return ortholog_seq[q_idx], q_idx + 1
            return None, None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plm2-meta", required=True)
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_cross_ortholog_PLM2",
    )
    args = parser.parse_args()

    plm2 = json.loads(Path(args.plm2_meta).read_text())
    muts = plm2["mutations"].split("/")
    log.info("PLM2 mutations: %s", muts)

    sites = {f"{m}  (PLM2)": int(m[1:-1]) for m in muts}
    # Add en31 + en15 reference sites for comparison
    sites["G1243T  (en31, WED-PLL)"] = 1243
    sites["E1369R  (en1+en31, PI PAM)"] = 1369
    sites["E1449H  (en31, PI PAM)"] = 1449
    sites["E1603H  (en15, PI/WED)"] = 1603

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    orthologs = load_orthologs_from_dir(Path(args.raw_dir), DEFAULT_ORTHOLOG_FILES)

    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0

    cons = compute_conservation(fncas9, orthologs)
    cons_by_pos = {c.position: c for c in cons}

    alignments = {}
    for name, seq in orthologs.items():
        log.info("Aligning FnCas9 vs %s...", name)
        alignments[name] = aligner.align(fncas9, seq)[0]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tsv = out_dir / "site_mapping.tsv"
    cols = ["site_label", "fncas9_pos", "fncas9_residue", "id_cons", "class_cons"]
    for name in orthologs:
        cols += [f"{name}_residue", f"{name}_pos"]

    with tsv.open("w") as f:
        f.write("\t".join(cols) + "\n")
        log.info("\n%-32s  %-6s  %-3s  %s  %s  %s",
                 "Site", "FnCas9", "WT", "id_c", "cls_c",
                 "  ".join(f"{n:>14}" for n in orthologs))
        for label, pos in sites.items():
            wt = fncas9[pos - 1]
            c = cons_by_pos[pos]
            row = [label, str(pos), wt, f"{c.identity_conservation:.2f}",
                   f"{c.class_conservation:.2f}"]
            display = [f"{wt}{pos}"]
            for name, seq in orthologs.items():
                aln = alignments[name]
                res, qpos = map_pos(aln, fncas9, seq, pos)
                if res is None:
                    row += ["-", "-"]
                    display.append("    GAP")
                else:
                    row += [res, str(qpos)]
                    star = "*" if res == wt else " "
                    display.append(f"   {res}{qpos:>4}{star}")
            f.write("\t".join(row) + "\n")
            log.info("%-32s  %s  %.2f  %.2f  %s",
                     label, f"{wt}{pos}",
                     c.identity_conservation, c.class_conservation,
                     "".join(display[1:]))

    log.info("\nLegend: * = identical to FnCas9 WT at aligned position\n")
    log.info("Wrote %s", tsv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
