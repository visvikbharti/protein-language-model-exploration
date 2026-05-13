from __future__ import annotations

import pytest

from nuclease_design.scoring.conservation import compute_conservation


class TestConservation:
    def test_fully_conserved_position(self) -> None:
        # FnCas9 has 'M' at position 1; all orthologs also have 'M' at position 1 (homologous)
        fncas9 = "MAAAGEKK"
        orthologs = {
            "X": "MAAGEK",  # same start
            "Y": "MAGEKK",
        }
        scores = compute_conservation(fncas9, orthologs)
        # Position 1 should be conserved
        s = scores[0]
        assert s.fncas9_residue == "M"
        assert s.identity_conservation == 1.0
        assert s.class_conservation == 1.0
        assert s.normalised_conservation > 0.9

    def test_class_conservation_catches_RK(self) -> None:
        """R conserved to K should be identity=0 but class_conservation=1.0
        (both positive). This is the case that motivated adding class_conservation."""
        fncas9 = "MR"
        orthologs = {
            "X": "MK",   # R → K (both positive)
            "Y": "MK",
        }
        scores = compute_conservation(fncas9, orthologs)
        s = scores[1]  # position 2 = R
        assert s.fncas9_residue == "R"
        assert s.identity_conservation == 0.0
        assert s.class_conservation == 1.0  # both K are positive class

    def test_variable_position(self) -> None:
        fncas9 = "MAGEKK"
        orthologs = {
            "X": "MTGEKK",  # G→T at pos 2
            "Y": "MSGEKK",  # G→S at pos 2
            "Z": "MAGEKK",  # G conserved
        }
        scores = compute_conservation(fncas9, orthologs)
        # Position 2 has 1 of 3 orthologs matching (Z), so identity_conservation = 1/3
        s = scores[1]
        assert s.fncas9_residue == "A"
        # Position 2 actually has 'A' in FnCas9; orthologs are T, S, A
        # 1 out of 3 matches → 0.333
        assert abs(s.identity_conservation - 1 / 3) < 1e-6

    def test_position_count(self) -> None:
        fncas9 = "MAGEKK"
        orthologs = {"X": "MAGEKK"}
        scores = compute_conservation(fncas9, orthologs)
        assert len(scores) == len(fncas9)
        for i, s in enumerate(scores):
            assert s.position == i + 1
            assert s.fncas9_residue == fncas9[i]

    def test_empty_orthologs_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one ortholog"):
            compute_conservation("MAGEKK", {})

    def test_normalisation_in_unit_interval(self) -> None:
        fncas9 = "MAGEKK"
        orthologs = {"X": "AAAA", "Y": "GGGG", "Z": "EEEE"}
        scores = compute_conservation(fncas9, orthologs)
        for s in scores:
            assert 0.0 <= s.normalised_conservation <= 1.0
            assert 0.0 <= s.identity_conservation <= 1.0
            assert s.shannon_entropy >= 0.0
