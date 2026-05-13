"""Cas9-family conservation scorer.

Builds a small MSA by pairwise-aligning Cas9 orthologs to FnCas9 (star alignment
with FnCas9 as the center), then computes per-FnCas9-position conservation as
either (a) fraction of orthologs sharing the FnCas9 residue at the homologous
column, or (b) normalised Shannon entropy.

The two metrics are reported together for transparency. Conservation ∈ [0, 1]
with 0 = fully variable and 1 = fully conserved.

Note that "conservation" here is computed over only 5 Cas9 sequences — a tiny
MSA by phylogenetic standards. Real conservation analysis uses hundreds of
homologs (MMseqs2 + UniRef). The values produced here are a coarse but useful
filter: a position that varies across these 5 distant orthologs is almost
certainly free to vary in any future engineered design; a position conserved
across all 5 is much more likely to be functionally important.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

from Bio.Align import PairwiseAligner, substitution_matrices

from nuclease_design.io import load_fasta

log = logging.getLogger(__name__)


AA_CLASSES: dict[str, str] = {
    # Positively charged
    "K": "pos", "R": "pos", "H": "pos",
    # Negatively charged
    "D": "neg", "E": "neg",
    # Polar uncharged
    "S": "polar", "T": "polar", "N": "polar", "Q": "polar", "Y": "polar",
    # Hydrophobic aliphatic
    "A": "hydro", "V": "hydro", "L": "hydro", "I": "hydro", "M": "hydro",
    # Aromatic
    "F": "aromatic", "W": "aromatic",
    # Special
    "G": "gly", "P": "pro", "C": "cys",
}


def _class_of(aa: str) -> str:
    return AA_CLASSES.get(aa.upper(), "other")


@dataclass(frozen=True)
class ConservationScore:
    """Per-position conservation summary.

    Three conservation metrics:
      - identity_conservation: fraction of orthologs sharing the exact FnCas9 WT residue.
      - class_conservation: fraction of orthologs sharing FnCas9's physicochemical class
        (positive / negative / polar / hydrophobic / aromatic / glycine / proline / cysteine).
      - normalised_conservation: 1 - Shannon_entropy / log2(N+1), bounded [0, 1].

    A position that has R in FnCas9 and K in two orthologs has identity_conservation = 0
    but class_conservation = 1.0 (all positive). This catches family-conserved properties
    that simple identity misses.
    """

    position: int
    fncas9_residue: str
    column: dict[str, str]  # ortholog_name -> residue or "-" for gap
    identity_conservation: float  # fraction of orthologs identical to FnCas9 WT, [0, 1]
    class_conservation: float  # fraction sharing FnCas9's AA class, [0, 1]
    shannon_entropy: float  # bits (0 = uniform conserved, higher = more variable)
    normalised_conservation: float  # 1 - H/log2(N+1), in [0, 1], 1 = fully conserved


def _star_align(fncas9_seq: str, orthologs: dict[str, str]) -> dict[str, list[str | None]]:
    """Return per-ortholog mapping FnCas9 position (1-indexed) -> aligned residue (or None for gap)."""
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0

    out: dict[str, list[str | None]] = {}
    for name, oseq in orthologs.items():
        log.info("Aligning FnCas9 vs %s (%d aa)", name, len(oseq))
        aln = aligner.align(fncas9_seq, oseq)[0]
        mapping: list[str | None] = [None] * len(fncas9_seq)
        aligned = aln.aligned  # shape (2, n_segments, 2)
        if aligned.shape[1] == 0:
            out[name] = mapping
            continue
        for (t_lo, t_hi), (q_lo, q_hi) in zip(aligned[0], aligned[1]):
            for offset, t_pos in enumerate(range(t_lo, t_hi)):
                q_pos = q_lo + offset
                if 0 <= q_pos < len(oseq):
                    mapping[t_pos] = oseq[q_pos]
        out[name] = mapping
    return out


def compute_conservation(
    fncas9_seq: str,
    orthologs: dict[str, str],
) -> list[ConservationScore]:
    """Compute conservation at every FnCas9 position.

    Args:
        fncas9_seq: WT FnCas9 amino-acid sequence.
        orthologs: name -> sequence dict of orthologous Cas9 proteins.

    Returns:
        One ConservationScore per FnCas9 position (1-indexed in the .position field).
    """
    mappings = _star_align(fncas9_seq, orthologs)
    n_orthologs = len(orthologs)
    if n_orthologs == 0:
        raise ValueError("Need at least one ortholog for conservation")

    # Maximum entropy: uniform over the union of (20 AA + gap) but bounded by n_orthologs
    max_entropy = math.log2(min(21, n_orthologs + 1)) if n_orthologs > 0 else 1.0

    out: list[ConservationScore] = []
    for i, fn_res in enumerate(fncas9_seq):
        col: dict[str, str] = {}
        for name in orthologs:
            res = mappings[name][i]
            col[name] = res if res is not None else "-"

        # Identity conservation: fraction of orthologs with same residue as FnCas9 WT
        n_matching = sum(1 for r in col.values() if r == fn_res)
        identity_conservation = n_matching / n_orthologs

        # Class conservation: fraction with the same physicochemical class as FnCas9 WT
        # (ignores gaps in the denominator)
        fn_class = _class_of(fn_res)
        non_gap_residues = [r for r in col.values() if r != "-"]
        if non_gap_residues:
            n_class = sum(1 for r in non_gap_residues if _class_of(r) == fn_class)
            class_conservation = n_class / len(non_gap_residues)
        else:
            class_conservation = 0.0

        # Shannon entropy over the multiset of (n_orthologs + 1: the FnCas9 residue + ortholog residues)
        # Including FnCas9 itself ensures a single conserved column has H = 0.
        residues = [fn_res] + list(col.values())
        counts: dict[str, int] = {}
        for r in residues:
            counts[r] = counts.get(r, 0) + 1
        total = len(residues)
        H = 0.0
        for c in counts.values():
            p = c / total
            if p > 0:
                H -= p * math.log2(p)
        normalised = 1.0 - (H / max_entropy if max_entropy > 0 else 0.0)
        normalised = max(0.0, min(1.0, normalised))

        out.append(
            ConservationScore(
                position=i + 1,
                fncas9_residue=fn_res,
                column=col,
                identity_conservation=identity_conservation,
                class_conservation=class_conservation,
                shannon_entropy=H,
                normalised_conservation=normalised,
            )
        )
    return out


def load_orthologs_from_dir(
    raw_dir: Path,
    files: dict[str, str],
) -> dict[str, str]:
    """Convenience loader for the project's data/raw/ structure."""
    out: dict[str, str] = {}
    for name, fname in files.items():
        path = raw_dir / fname
        if not path.exists():
            log.warning("Missing FASTA: %s", path)
            continue
        out[name] = load_fasta(path)[0].sequence
    return out


DEFAULT_ORTHOLOG_FILES: dict[str, str] = {
    "SpCas9": "Q99ZW2_spcas9.fasta",
    "SaCas9": "J7RUA5_sacas9.fasta",
    "Nme1Cas9": "C9X1G5_nme1cas9.fasta",
    "CjCas9": "Q0P897_cjcas9.fasta",
}
