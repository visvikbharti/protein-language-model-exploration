"""Build a neighbor-joining phylogenetic tree from pairwise BLOSUM62 distances.

Input: all FnCas9 variants (PLM1, PLM2, WT, en1, en15, en31) + 4 Cas9 orthologs.
Distance metric: 1 - (BLOSUM62-identity / 100) using global pairwise alignment.

Output:
  - Newick file (tree.newick)
  - ASCII tree (tree.txt)
  - matplotlib PNG (tree.png) if matplotlib available
  - Distance matrix TSV (distance_matrix.tsv)
"""
from __future__ import annotations

import argparse
import io
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.Phylo import draw_ascii, write
from Bio.Phylo.TreeConstruction import DistanceMatrix, DistanceTreeConstructor

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.io import load_fasta


class SeqEntry(NamedTuple):
    name: str
    sequence: str


def collect_sequences(
    variants_v1: Path,
    variants_v2: Path,
    raw_dir: Path,
) -> list[SeqEntry]:
    """Combine PLM1 + PLM2 + en-variants + WT + 4 orthologs into one list."""
    entries: list[SeqEntry] = []
    seen: set[str] = set()

    def add(name: str, seq: str) -> None:
        if name not in seen:
            entries.append(SeqEntry(name=name, sequence=seq))
            seen.add(name)

    # From PLM1 candidates FASTA: PLM1 + WT + en1 + en15 + en31
    for rec in load_fasta(variants_v1):
        short = rec.header.split()[0]
        add(short, rec.sequence)

    # From PLM2 candidates FASTA: PLM2 + (duplicates of WT, en31, en15)
    for rec in load_fasta(variants_v2):
        short = rec.header.split()[0]
        if short.startswith("FnCas9-PLM2"):
            add(short, rec.sequence)

    # Orthologs
    ortholog_files = {
        "SpCas9": "Q99ZW2_spcas9.fasta",
        "SaCas9": "J7RUA5_sacas9.fasta",
        "Nme1Cas9": "C9X1G5_nme1cas9.fasta",
        "CjCas9": "Q0P897_cjcas9.fasta",
    }
    for name, fname in ortholog_files.items():
        path = raw_dir / fname
        if not path.exists():
            log.warning("Missing ortholog FASTA: %s", path)
            continue
        rec = load_fasta(path)[0]
        add(name, rec.sequence)

    return entries


def pairwise_distance(seq_a: str, seq_b: str, aligner: PairwiseAligner) -> float:
    """Return 1 - (% identity / 100) as the pairwise distance."""
    aln = aligner.align(seq_a, seq_b)[0]
    aligned = aln.aligned
    if aligned.shape[1] == 0:
        return 1.0
    total = 0
    ident = 0
    for (a_lo, a_hi), (b_lo, b_hi) in zip(aligned[0], aligned[1]):
        for x, y in zip(seq_a[a_lo:a_hi], seq_b[b_lo:b_hi]):
            if x.isalpha() and y.isalpha():
                total += 1
                if x == y:
                    ident += 1
    if total == 0:
        return 1.0
    return 1.0 - ident / total


def build_distance_matrix(entries: list[SeqEntry]) -> DistanceMatrix:
    """Build a lower-triangular distance matrix in the format BioPython expects."""
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0

    names = [e.name for e in entries]
    n = len(entries)
    # BioPython DistanceMatrix lower-triangular format: [[0], [d10, 0], [d20, d21, 0], ...]
    matrix: list[list[float]] = []
    for i in range(n):
        row: list[float] = []
        for j in range(i + 1):
            if i == j:
                row.append(0.0)
            else:
                d = pairwise_distance(entries[i].sequence, entries[j].sequence, aligner)
                row.append(d)
                log.info("  d(%s, %s) = %.4f", names[i], names[j], d)
        matrix.append(row)
    return DistanceMatrix(names=names, matrix=matrix)


def save_distance_matrix(dm: DistanceMatrix, path: Path) -> None:
    with path.open("w") as f:
        f.write("\t" + "\t".join(dm.names) + "\n")
        for i, name in enumerate(dm.names):
            row = [f"{dm[i, j]:.4f}" for j in range(len(dm.names))]
            f.write(name + "\t" + "\t".join(row) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variants-v1",
        default="results/runs/2026-05-13_candidates/fncas9_variants.fasta",
    )
    parser.add_argument(
        "--variants-v2",
        default="results/runs/2026-05-13_candidates_v2/fncas9_variants_v2.fasta",
    )
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_phylogeny",
    )
    parser.add_argument("--method", default="nj", choices=["nj", "upgma"],
                        help="Tree construction method")
    args = parser.parse_args()

    entries = collect_sequences(
        Path(args.variants_v1),
        Path(args.variants_v2),
        Path(args.raw_dir),
    )
    log.info("Collected %d sequences:", len(entries))
    for e in entries:
        log.info("  %-15s  length=%d", e.name, len(e.sequence))

    log.info("\n=== Computing pairwise BLOSUM62 distances ===")
    dm = build_distance_matrix(entries)

    log.info("\n=== Building %s tree ===", args.method.upper())
    constructor = DistanceTreeConstructor()
    if args.method == "nj":
        tree = constructor.nj(dm)
    else:
        tree = constructor.upgma(dm)
    # Optional: drop the internal node names that BioPython auto-assigns
    for clade in tree.find_clades():
        if clade.name and clade.name.startswith("Inner"):
            clade.name = None

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_distance_matrix(dm, out_dir / "distance_matrix.tsv")
    log.info("Wrote %s", out_dir / "distance_matrix.tsv")

    newick_path = out_dir / f"tree_{args.method}.newick"
    write(tree, str(newick_path), "newick")
    log.info("Wrote %s", newick_path)

    # ASCII tree
    ascii_io = io.StringIO()
    draw_ascii(tree, file=ascii_io)
    ascii_str = ascii_io.getvalue()
    txt_path = out_dir / f"tree_{args.method}.txt"
    txt_path.write_text(ascii_str)
    log.info("Wrote %s", txt_path)
    log.info("\n=== ASCII tree (%s) ===\n%s", args.method.upper(), ascii_str)

    # PNG via matplotlib if available
    try:
        import matplotlib  # noqa
        matplotlib.use("Agg")
        from Bio.Phylo import draw
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 6))
        draw(tree, axes=ax, do_show=False)
        ax.set_title(f"Cas9 family phylogeny ({args.method.upper()} on BLOSUM62 pairwise identity)")
        png_path = out_dir / f"tree_{args.method}.png"
        fig.savefig(png_path, dpi=150, bbox_inches="tight")
        log.info("Wrote %s", png_path)
    except Exception as e:  # noqa: BLE001
        log.warning("Could not produce PNG: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
