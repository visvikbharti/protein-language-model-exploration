"""Sequence-guided 3D structural alignment of Cas9 proteins.

For two PDB structures of homologous proteins (different sequence identity),
this module:
  1. Extracts the longest protein chain from each
  2. Pairwise-aligns the protein sequences with BLOSUM62 + NW global alignment
  3. Identifies the residue pairs in the aligned non-gap segments
  4. Applies a single Kabsch superposition on the corresponding CA atoms
  5. Reports backbone RMSD, the number of aligned CA pairs, and the fraction
     of CA pairs within 4 Å after superposition (a TM-score-like quality)

NOTE: a true TM-align / DALI would iteratively refine the residue
correspondence to optimise structural similarity. This module does a
*sequence-guided* superposition, which is fast, deterministic, and produces
a meaningful single-number RMSD for closely-related homologs (e.g. across
Cas9 orthologs). For very distantly related proteins, true structural
alignment would be preferable but requires an external tool.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from Bio.Align import PairwiseAligner, substitution_matrices

import biotite.structure as struc
import biotite.structure.io.pdb as pdb

log = logging.getLogger(__name__)


# Three-letter to one-letter amino acid map for sequence extraction.
THREE_TO_ONE: dict[str, str] = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
    "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
    "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
    "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
}


@dataclass(frozen=True)
class StructuralAlignment:
    """Output of a sequence-guided structural superposition.

    Two RMSDs are reported:
      - rmsd_all: over every aligned CA pair (large for distantly-related orthologs
        because misaligned regions dominate)
      - rmsd_core: over the iteratively-trimmed structural core (the "TM-align-like"
        meaningful number — RMSD on the well-superimposed substructure)
    """

    ref_pdb: str
    mob_pdb: str
    ref_chain: str
    mob_chain: str
    n_ref_residues: int
    n_mob_residues: int
    n_aligned_residues: int  # number of aligned CA pairs from sequence alignment
    n_core_residues: int     # number of residues in the converged structural core
    rmsd_all: float          # RMSD over every aligned CA pair
    rmsd_core: float         # RMSD over the structural core only
    fraction_within_4A: float
    sequence_identity: float


def _longest_protein_chain(structure) -> tuple[str, struc.AtomArray]:
    """Return (chain_id, chain_atoms) for the longest amino-acid chain."""
    protein = structure[struc.filter_amino_acids(structure)]
    chain_residue_counts = {
        c: len(set(protein[protein.chain_id == c].res_id))
        for c in sorted(set(protein.chain_id))
    }
    if not chain_residue_counts:
        raise ValueError("No protein chains in structure")
    best_chain = max(chain_residue_counts, key=lambda c: chain_residue_counts[c])
    return best_chain, protein[protein.chain_id == best_chain]


def _extract_sequence_and_ca(chain_atoms: struc.AtomArray) -> tuple[str, dict[int, np.ndarray]]:
    """Return (sequence_string, mapping from index in sequence -> CA xyz).

    Residues in the PDB without a CA atom or with non-standard amino acids
    are excluded. The output sequence positions are 0-indexed and SEQUENTIAL,
    NOT the PDB residue numbers (so they match what the pairwise aligner sees).
    """
    seq_chars: list[str] = []
    ca_by_seq_index: dict[int, np.ndarray] = {}
    seen_res_ids: list[int] = []
    for res_id in sorted(set(chain_atoms.res_id)):
        if res_id in seen_res_ids:
            continue
        seen_res_ids.append(res_id)
        res = chain_atoms[chain_atoms.res_id == res_id]
        if res.array_length() == 0:
            continue
        res_name = str(res.res_name[0])
        one = THREE_TO_ONE.get(res_name)
        if one is None:
            continue
        ca = res[res.atom_name == "CA"]
        if ca.array_length() == 0:
            continue
        idx = len(seq_chars)
        seq_chars.append(one)
        ca_by_seq_index[idx] = ca.coord[0]
    return "".join(seq_chars), ca_by_seq_index


def superimpose_homologs(
    ref_pdb_path: Path,
    mob_pdb_path: Path,
) -> StructuralAlignment:
    """Sequence-guided structural superposition of two PDB files.

    Args:
        ref_pdb_path: PDB to keep fixed (reference frame).
        mob_pdb_path: PDB to be rotated/translated onto the reference.

    Returns:
        A StructuralAlignment with backbone RMSD and aligned-residue counts.
    """
    ref_file = pdb.PDBFile.read(str(ref_pdb_path))
    mob_file = pdb.PDBFile.read(str(mob_pdb_path))

    ref_struct = ref_file.get_structure(model=1)
    mob_struct = mob_file.get_structure(model=1)

    ref_chain_id, ref_chain = _longest_protein_chain(ref_struct)
    mob_chain_id, mob_chain = _longest_protein_chain(mob_struct)

    ref_seq, ref_ca = _extract_sequence_and_ca(ref_chain)
    mob_seq, mob_ca = _extract_sequence_and_ca(mob_chain)
    log.info("  Reference: %s chain %s, %d residues",
             ref_pdb_path.name, ref_chain_id, len(ref_seq))
    log.info("  Mobile:    %s chain %s, %d residues",
             mob_pdb_path.name, mob_chain_id, len(mob_seq))

    # Pairwise sequence alignment (global, BLOSUM62)
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0
    aln = aligner.align(ref_seq, mob_seq)[0]
    aligned = aln.aligned  # (2, n_segments, 2)

    # Build the list of corresponding CA pairs
    ref_xyz_list: list[np.ndarray] = []
    mob_xyz_list: list[np.ndarray] = []
    n_identical = 0
    n_total = 0
    if aligned.shape[1] > 0:
        for (r_lo, r_hi), (m_lo, m_hi) in zip(aligned[0], aligned[1]):
            for offset in range(r_hi - r_lo):
                r_idx = r_lo + offset
                m_idx = m_lo + offset
                if r_idx in ref_ca and m_idx in mob_ca:
                    ref_xyz_list.append(ref_ca[r_idx])
                    mob_xyz_list.append(mob_ca[m_idx])
                    n_total += 1
                    if ref_seq[r_idx] == mob_seq[m_idx]:
                        n_identical += 1

    if not ref_xyz_list:
        raise ValueError("No aligned CA pairs found between the two structures")

    ref_arr = np.asarray(ref_xyz_list)
    mob_arr = np.asarray(mob_xyz_list)

    def kabsch_rmsd(ref: np.ndarray, mob: np.ndarray) -> tuple[float, np.ndarray]:
        ref_centroid = ref.mean(axis=0)
        mob_centroid = mob.mean(axis=0)
        ref_centered = ref - ref_centroid
        mob_centered = mob - mob_centroid
        H = mob_centered.T @ ref_centered
        U, _, Vt = np.linalg.svd(H)
        d = float(np.linalg.det(Vt.T @ U.T))
        D = np.eye(3)
        D[2, 2] = 1.0 if d > 0 else -1.0
        R = Vt.T @ D @ U.T
        mob_aligned = (mob_centered @ R.T) + ref_centroid
        rmsd = float(np.sqrt(np.mean(np.sum((ref - mob_aligned) ** 2, axis=1))))
        return rmsd, mob_aligned

    # Step 1: full-alignment superposition
    rmsd_all, _ = kabsch_rmsd(ref_arr, mob_arr)

    # Step 2: graduated iterative refinement. Start with a permissive threshold
    # (15 Å, large enough to capture the entire structural core even from a poor
    # initial superposition) and gradually tighten to 4 Å. At each threshold,
    # superpose using only the current inlier set, then re-evaluate inliers.
    # This is the canonical TM-align-like refinement, simplified.
    deltas = np.full(len(ref_arr), np.inf)

    def superpose_and_score(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Superpose using points in mask; return aligned mobile coords (all points) + deltas."""
        if mask.sum() < 3:
            return mob_arr.copy(), np.full(len(ref_arr), np.inf)
        ref_in = ref_arr[mask]
        mob_in = mob_arr[mask]
        ref_centroid = ref_in.mean(axis=0)
        mob_centroid = mob_in.mean(axis=0)
        ref_centered = ref_in - ref_centroid
        mob_centered = mob_in - mob_centroid
        H = mob_centered.T @ ref_centered
        U, _, Vt = np.linalg.svd(H)
        d = float(np.linalg.det(Vt.T @ U.T))
        D = np.eye(3)
        D[2, 2] = 1.0 if d > 0 else -1.0
        R = Vt.T @ D @ U.T
        mob_all_aligned = (mob_arr - mob_centroid) @ R.T + ref_centroid
        return mob_all_aligned, np.linalg.norm(ref_arr - mob_all_aligned, axis=1)

    # Start with all aligned residues as inliers
    inlier_mask = np.ones(len(ref_arr), dtype=bool)
    thresholds = [15.0, 10.0, 8.0, 6.0, 5.0, 4.0]
    for threshold in thresholds:
        for _ in range(5):
            _, deltas = superpose_and_score(inlier_mask)
            new_mask = deltas < threshold
            if new_mask.sum() < 10:
                break
            if (new_mask == inlier_mask).all():
                break
            inlier_mask = new_mask

    n_core = int(inlier_mask.sum())
    if n_core >= 3:
        rmsd_core = float(np.sqrt(np.mean(deltas[inlier_mask] ** 2)))
    else:
        rmsd_core = float("nan")
    fraction_4A = float((deltas < 4.0).mean())

    identity = (n_identical / n_total) if n_total else 0.0

    return StructuralAlignment(
        ref_pdb=ref_pdb_path.name,
        mob_pdb=mob_pdb_path.name,
        ref_chain=ref_chain_id,
        mob_chain=mob_chain_id,
        n_ref_residues=len(ref_seq),
        n_mob_residues=len(mob_seq),
        n_aligned_residues=n_total,
        n_core_residues=n_core,
        rmsd_all=rmsd_all,
        rmsd_core=rmsd_core,
        fraction_within_4A=fraction_4A,
        sequence_identity=identity,
    )
