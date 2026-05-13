"""Cross-Cas9 structural homology via sequence-guided 3D superposition.

For each pair (Cas9_A, Cas9_B) in {FnCas9, SpCas9, SaCas9, Nme1Cas9, CjCas9},
compute backbone RMSD using nuclease_design.structure.align.superimpose_homologs.

Output:
  - Pairwise table with RMSD_all, RMSD_core, core size, sequence identity
  - Distance matrix (RMSD_core) for tree building
  - Notes about the sequence-guided approximation limitation
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

from nuclease_design.structure.align import superimpose_homologs


CAS9_STRUCTURES: dict[str, str] = {
    "FnCas9":   "data/raw/5B2O.pdb",
    "SpCas9":   "data/raw/structures/4OO8.pdb",
    "SaCas9":   "data/raw/structures/5CZZ.pdb",
    "Nme1Cas9": "data/raw/structures/6JDQ.pdb",
    "CjCas9":   "data/raw/structures/5X2H.pdb",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_structural_homology",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    names = list(CAS9_STRUCTURES)
    paths = {n: Path(p) for n, p in CAS9_STRUCTURES.items()}
    for n, p in paths.items():
        if not p.exists():
            log.error("Missing structure: %s (%s)", n, p)
            return 1

    pairwise_table = out_dir / "structural_alignments.tsv"
    rmsd_matrix_path = out_dir / "rmsd_core_matrix.tsv"

    n = len(names)
    rmsd_core_mat: list[list[float]] = [[0.0] * n for _ in range(n)]

    with pairwise_table.open("w") as f:
        f.write("\t".join([
            "ref", "mob", "ref_chain", "mob_chain",
            "n_ref_residues", "n_mob_residues",
            "n_aligned_residues", "n_core_residues",
            "rmsd_all_A", "rmsd_core_A", "fraction_within_4A",
            "sequence_identity",
        ]) + "\n")
        log.info("\n=== Pairwise structural alignment (sequence-guided + iterative refinement) ===")
        log.info(f"{'Ref':<10} {'Mob':<10} {'#core':>6} {'RMSD_all':>10} {'RMSD_core':>10} "
                 f"{'seqID':>6}")
        log.info("-" * 70)
        for i in range(n):
            for j in range(n):
                if i == j:
                    rmsd_core_mat[i][j] = 0.0
                    continue
                aln = superimpose_homologs(paths[names[i]], paths[names[j]])
                rmsd_core_mat[i][j] = aln.rmsd_core
                log.info("%-10s %-10s %6d %10.3f %10.3f %6.2f",
                         names[i], names[j], aln.n_core_residues,
                         aln.rmsd_all, aln.rmsd_core, aln.sequence_identity)
                f.write("\t".join([
                    names[i], names[j], str(aln.ref_chain), str(aln.mob_chain),
                    str(aln.n_ref_residues), str(aln.n_mob_residues),
                    str(aln.n_aligned_residues), str(aln.n_core_residues),
                    f"{aln.rmsd_all:.3f}", f"{aln.rmsd_core:.3f}",
                    f"{aln.fraction_within_4A:.3f}",
                    f"{aln.sequence_identity:.3f}",
                ]) + "\n")

    # RMSD-core matrix
    with rmsd_matrix_path.open("w") as f:
        f.write("\t" + "\t".join(names) + "\n")
        for i in range(n):
            f.write(names[i] + "\t" +
                    "\t".join(f"{rmsd_core_mat[i][j]:.3f}" for j in range(n)) + "\n")
    log.info("\nWrote %s", pairwise_table)
    log.info("Wrote %s", rmsd_matrix_path)

    log.info("\n=== Caveat ===")
    log.info("These RMSDs come from sequence-guided superposition with iterative outlier")
    log.info("trimming. Sequence alignment between distantly-related Cas9 orthologs (~25%%")
    log.info("identity) misaligns long insertions/deletions, so the structural core that")
    log.info("can be recovered is smaller than a true TM-align result. For a definitive")
    log.info("cross-Cas9 structural alignment, use an external TM-align or DALI.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
