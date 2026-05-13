"""Pairwise sequence homology of FnCas9-PLM1 vs Cas9 orthologs + engineered variants.

Uses Bio.Align.PairwiseAligner with BLOSUM62 substitution matrix, global mode.

Outputs:
  - results/runs/<date>_homology/sequence_identity_matrix.tsv
  - results/runs/<date>_homology/sequence_similarity_matrix.tsv
  - results/runs/<date>_homology/pairwise_alignments.fasta (paired alignments)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from Bio.Align import PairwiseAligner, substitution_matrices

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta


class SeqEntry(NamedTuple):
    name: str
    sequence: str


def load_all_orthologs(variants_fasta: Path, raw_dir: Path) -> list[SeqEntry]:
    """Combine the variant FASTA (PLM1 + WT + ens) with the ortholog FASTAs."""
    entries: list[SeqEntry] = []
    for r in load_fasta(variants_fasta):
        # Header looks like "FnCas9-PLM1 PLM-designed ..." — take first whitespace token
        short = r.header.split()[0]
        entries.append(SeqEntry(name=short, sequence=r.sequence))

    ortholog_files = {
        "SpCas9": "Q99ZW2_spcas9.fasta",
        "SaCas9": "J7RUA5_sacas9.fasta",
        "Nme1Cas9": "C9X1G5_nme1cas9.fasta",
        "CjCas9": "Q0P897_cjcas9.fasta",
    }
    for name, fname in ortholog_files.items():
        path = raw_dir / fname
        if not path.exists():
            log.warning("Missing ortholog FASTA %s — skipping", path)
            continue
        recs = load_fasta(path)
        entries.append(SeqEntry(name=name, sequence=recs[0].sequence))

    return entries


def make_aligner() -> PairwiseAligner:
    """BLOSUM62, global, biologically sensible gap penalties."""
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0
    return aligner


def alignment_stats(aln, seq_a: str, seq_b: str) -> tuple[float, float, int, int]:
    """Return (% identity, % similarity, aligned length without gaps, mismatches).

    Iterates the segment endpoints in aln.aligned (shape (2, n_segments, 2))
    and tallies identities + BLOSUM62-positive matches across aligned residues.
    """
    blosum = substitution_matrices.load("BLOSUM62")
    aligned = aln.aligned  # shape (2, n_segments, 2)
    if aligned.shape[1] == 0:
        return 0.0, 0.0, 0, 0
    a_segs, b_segs = aligned[0], aligned[1]
    ident = 0
    sim = 0
    total = 0
    for (a_lo, a_hi), (b_lo, b_hi) in zip(a_segs, b_segs):
        a_chunk = seq_a[a_lo:a_hi].upper()
        b_chunk = seq_b[b_lo:b_hi].upper()
        for x, y in zip(a_chunk, b_chunk):
            if not (x.isalpha() and y.isalpha()):
                continue
            total += 1
            if x == y:
                ident += 1
                sim += 1
            else:
                try:
                    if blosum[x, y] > 0:
                        sim += 1
                except (KeyError, IndexError):
                    pass
    if total == 0:
        return 0.0, 0.0, 0, 0
    return (
        100.0 * ident / total,
        100.0 * sim / total,
        total,
        total - ident,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variants",
        required=True,
        help="FASTA with FnCas9-PLM1 + WT + en1/en15/en31",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directory with Cas9 ortholog FASTAs",
    )
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_homology",
    )
    args = parser.parse_args()

    entries = load_all_orthologs(Path(args.variants), Path(args.raw_dir))
    log.info("Loaded %d sequences:", len(entries))
    for e in entries:
        log.info("  %-15s  length=%d", e.name, len(e.sequence))

    aligner = make_aligner()

    # Pairwise all-vs-all
    n = len(entries)
    identity = [[0.0] * n for _ in range(n)]
    similarity = [[0.0] * n for _ in range(n)]
    aligned_len = [[0] * n for _ in range(n)]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pair_fasta = out_dir / "pairwise_alignments.fasta"
    pair_fasta.unlink(missing_ok=True)

    log.info("\nRunning %d pairwise alignments...", n * (n + 1) // 2)
    with pair_fasta.open("w") as pf:
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    identity[i][j] = 100.0
                    similarity[i][j] = 100.0
                    aligned_len[i][j] = len(entries[i].sequence)
                    continue
                alns = aligner.align(entries[i].sequence, entries[j].sequence)
                aln = alns[0]
                pid, psim, alen, mm = alignment_stats(aln, entries[i].sequence, entries[j].sequence)
                identity[i][j] = identity[j][i] = pid
                similarity[i][j] = similarity[j][i] = psim
                aligned_len[i][j] = aligned_len[j][i] = alen
                log.info(
                    "  %-15s vs %-15s   identity=%5.1f%%   similarity=%5.1f%%   aligned=%4d",
                    entries[i].name, entries[j].name, pid, psim, alen,
                )

    # Identity matrix
    id_tsv = out_dir / "sequence_identity_matrix.tsv"
    with id_tsv.open("w") as f:
        f.write("\t" + "\t".join(e.name for e in entries) + "\n")
        for i, e in enumerate(entries):
            f.write(e.name + "\t" + "\t".join(f"{identity[i][j]:.2f}" for j in range(n)) + "\n")
    log.info("Wrote %s", id_tsv)

    # Similarity matrix
    sim_tsv = out_dir / "sequence_similarity_matrix.tsv"
    with sim_tsv.open("w") as f:
        f.write("\t" + "\t".join(e.name for e in entries) + "\n")
        for i, e in enumerate(entries):
            f.write(e.name + "\t" + "\t".join(f"{similarity[i][j]:.2f}" for j in range(n)) + "\n")
    log.info("Wrote %s", sim_tsv)

    # Aligned-length matrix
    al_tsv = out_dir / "aligned_length_matrix.tsv"
    with al_tsv.open("w") as f:
        f.write("\t" + "\t".join(e.name for e in entries) + "\n")
        for i, e in enumerate(entries):
            f.write(e.name + "\t" + "\t".join(str(aligned_len[i][j]) for j in range(n)) + "\n")
    log.info("Wrote %s", al_tsv)

    # Compact summary
    log.info("\n=== Identity vs FnCas9-PLM1 ===")
    plm1_idx = next(i for i, e in enumerate(entries) if e.name == "FnCas9-PLM1")
    for j in range(n):
        if j == plm1_idx:
            continue
        log.info("  %-15s   identity=%5.2f%%   similarity=%5.2f%%",
                 entries[j].name, identity[plm1_idx][j], similarity[plm1_idx][j])

    return 0


if __name__ == "__main__":
    sys.exit(main())
