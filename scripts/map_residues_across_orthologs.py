"""For each FnCas9 mutation site (en1/en15/en31 + PLM1), identify the homologous
residue position and identity in SpCas9, SaCas9, Nme1Cas9, CjCas9 via pairwise
alignment.

The Cas9 fold is structurally conserved despite ~20-30% sequence identity across
orthologs, so the aligned position is a reasonable structural-equivalent
without doing explicit structural superposition (which would need TM-align or CE).
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


SITES = {
    "G1243T (en31, WED-PLL)": 1243,
    "E1369R (en1, en31; PI PAM)": 1369,
    "E1449H (en31, PI PAM)": 1449,
    "E1603H (en15, PI/WED)": 1603,
    "H1236L (PLM1, WED)": 1236,
    "R1367L (PLM1, PI)": 1367,
    "W1459K (PLM1, PI; RNA-contact)": 1459,
    "Q1596N (PLM1, PI surface)": 1596,
}

ORTHOLOG_FILES = {
    "SpCas9": "Q99ZW2_spcas9.fasta",
    "SaCas9": "J7RUA5_sacas9.fasta",
    "Nme1Cas9": "C9X1G5_nme1cas9.fasta",
    "CjCas9": "Q0P897_cjcas9.fasta",
}


def map_position_via_alignment(aln, fncas9_seq: str, ortholog_seq: str, pos: int) -> tuple[str | None, int | None]:
    """Given an alignment of FnCas9 (target) and ortholog (query), find the
    ortholog residue (identity + 1-indexed position) homologous to FnCas9 pos.

    Uses aln.aligned segment endpoints. Returns (None, None) if pos is in an
    unaligned region (i.e., gap in the ortholog vs FnCas9).
    """
    aligned = aln.aligned  # shape (2, n_segments, 2)
    if aligned.shape[1] == 0:
        return None, None
    target_segs = aligned[0]
    query_segs = aligned[1]
    idx = pos - 1  # 0-indexed
    for (t_lo, t_hi), (q_lo, q_hi) in zip(target_segs, query_segs):
        if t_lo <= idx < t_hi:
            offset = idx - t_lo
            q_idx = q_lo + offset
            if 0 <= q_idx < len(ortholog_seq):
                return ortholog_seq[q_idx], q_idx + 1
            return None, None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_cross_ortholog",
    )
    args = parser.parse_args()

    fncas9 = load_fasta(Path(args.fasta))[0].sequence
    log.info("FnCas9 length: %d", len(fncas9))

    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0

    orthologs: dict[str, str] = {}
    for name, fname in ORTHOLOG_FILES.items():
        path = Path(args.raw_dir) / fname
        if not path.exists():
            log.warning("Missing %s", path)
            continue
        orthologs[name] = load_fasta(path)[0].sequence

    # Align FnCas9 to each ortholog once
    alignments = {}
    for name, seq in orthologs.items():
        log.info("Aligning FnCas9 vs %s...", name)
        aln = aligner.align(fncas9, seq)[0]
        alignments[name] = aln

    # Build table
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tsv = out_dir / "site_mapping.tsv"
    cols = ["site_label", "fncas9_pos", "fncas9_residue"]
    for name in orthologs:
        cols.append(f"{name}_residue")
        cols.append(f"{name}_pos")
    with tsv.open("w") as f:
        f.write("\t".join(cols) + "\n")
        log.info("\n%-32s  %-6s  %-3s  %s", "Site", "FnCas9", "WT",
                 "  ".join(f"{n:>14}" for n in orthologs))
        for label, pos in SITES.items():
            row = [label, str(pos), fncas9[pos - 1]]
            display: list[str] = [f"{fncas9[pos - 1]}{pos}"]
            for name, seq in orthologs.items():
                aln = alignments[name]
                res, qpos = map_position_via_alignment(aln, fncas9, seq, pos)
                if res is None:
                    row.append("-")
                    row.append("-")
                    display.append("    GAP/unaligned")
                else:
                    row.append(res)
                    row.append(str(qpos))
                    is_conserved = "*" if res == fncas9[pos - 1] else " "
                    display.append(f"   {res}{qpos:>4}{is_conserved}")
            f.write("\t".join(row) + "\n")
            log.info("%-32s  %s", label, "".join(display))

    log.info("\nLegend: * = identical residue to FnCas9 WT at the aligned position\n")
    log.info("Wrote %s", tsv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
