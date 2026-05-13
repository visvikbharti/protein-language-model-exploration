"""Build a phylogenetic tree from the structural-core RMSD matrix and compare
its topology with the sequence-based tree from build_phylogeny.py.

The structural RMSD matrix is symmetric and zero on the diagonal — feed it
directly to the BioPython NJ or UPGMA constructor.
"""
from __future__ import annotations

import argparse
import io
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from Bio.Phylo import draw_ascii, write
from Bio.Phylo.TreeConstruction import DistanceMatrix, DistanceTreeConstructor

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def load_rmsd_matrix(tsv_path: Path) -> tuple[list[str], list[list[float]]]:
    with tsv_path.open() as f:
        header = f.readline().rstrip().split("\t")[1:]
        rows = []
        for line in f:
            parts = line.rstrip().split("\t")
            rows.append([float(x) for x in parts[1:]])
    return header, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix",
        default="results/runs/2026-05-13_structural_homology/rmsd_core_matrix.tsv",
    )
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_structural_phylogeny",
    )
    parser.add_argument("--method", default="upgma", choices=["nj", "upgma"])
    args = parser.parse_args()

    names, mat = load_rmsd_matrix(Path(args.matrix))
    log.info("Loaded structural RMSD matrix over %d structures: %s", len(names), names)

    # Lower-triangular for BioPython DistanceMatrix
    lt: list[list[float]] = []
    for i in range(len(names)):
        row: list[float] = []
        for j in range(i + 1):
            row.append(float(mat[i][j]) if i != j else 0.0)
        lt.append(row)

    dm = DistanceMatrix(names=names, matrix=lt)

    constructor = DistanceTreeConstructor()
    if args.method == "nj":
        tree = constructor.nj(dm)
    else:
        tree = constructor.upgma(dm)
    for clade in tree.find_clades():
        if clade.name and clade.name.startswith("Inner"):
            clade.name = None

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    newick_path = out_dir / f"tree_{args.method}.newick"
    write(tree, str(newick_path), "newick")
    log.info("Wrote %s", newick_path)

    ascii_io = io.StringIO()
    draw_ascii(tree, file=ascii_io)
    ascii_str = ascii_io.getvalue()
    txt_path = out_dir / f"tree_{args.method}.txt"
    txt_path.write_text(ascii_str)
    log.info("Wrote %s\n", txt_path)
    log.info("=== ASCII tree (%s, distance = RMSD_core) ===\n%s", args.method.upper(), ascii_str)

    try:
        import matplotlib
        matplotlib.use("Agg")
        from Bio.Phylo import draw
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5))
        draw(tree, axes=ax, do_show=False)
        ax.set_title(f"Cas9 structural phylogeny ({args.method.upper()} on 3D backbone RMSD)")
        png_path = out_dir / f"tree_{args.method}.png"
        fig.savefig(png_path, dpi=150, bbox_inches="tight")
        log.info("Wrote %s", png_path)
    except Exception as e:  # noqa: BLE001
        log.warning("Could not produce PNG: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
