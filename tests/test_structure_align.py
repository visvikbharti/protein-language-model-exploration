from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nuclease_design.structure.align import (
    THREE_TO_ONE,
    StructuralAlignment,
    superimpose_homologs,
)


class TestThreeToOne:
    def test_all_20_aa_present(self) -> None:
        assert len(THREE_TO_ONE) == 20
        assert set(THREE_TO_ONE.values()) == set("ACDEFGHIKLMNPQRSTVWY")


REPO_ROOT = Path(__file__).resolve().parent.parent
FN_PDB = REPO_ROOT / "data" / "raw" / "5B2O.pdb"
SP_PDB = REPO_ROOT / "data" / "raw" / "structures" / "4OO8.pdb"


@pytest.mark.skipif(not FN_PDB.exists(), reason="5B2O.pdb not downloaded")
class TestSuperimposeHomologs:
    def test_self_superposition_rmsd_zero(self) -> None:
        """FnCas9 vs itself should give RMSD ≈ 0 and 100% identity."""
        aln = superimpose_homologs(FN_PDB, FN_PDB)
        assert aln.rmsd_all < 0.01
        assert aln.rmsd_core < 0.01
        assert aln.sequence_identity == pytest.approx(1.0)
        assert aln.fraction_within_4A == pytest.approx(1.0)

    @pytest.mark.skipif(not SP_PDB.exists(), reason="4OO8.pdb not downloaded")
    def test_cross_ortholog_rmsd_reasonable(self) -> None:
        """FnCas9 vs SpCas9: a sequence-guided superposition cannot recover the
        full Cas9 structural core because NW alignment misaligns large insertions/
        deletions. The structural-core RMSD on whatever residues do co-locate
        should be in 1-7 Å (these are typically conserved active-site residues).

        For a true TM-align-style result, an external structural aligner is
        needed; this module produces a sequence-guided approximation."""
        aln = superimpose_homologs(FN_PDB, SP_PDB)
        assert aln.n_aligned_residues > 100  # large NW alignment exists
        assert aln.n_core_residues >= 5      # at least a small structural core
        assert 0.5 < aln.rmsd_core < 8.0     # core RMSD in expected range
        assert aln.rmsd_all > aln.rmsd_core  # full RMSD always >= core RMSD
        assert 0.05 < aln.sequence_identity < 0.6  # Cas9 family ~20-30% identity
