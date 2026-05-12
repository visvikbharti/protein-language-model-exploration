from __future__ import annotations

import pytest

from nuclease_design.variants import (
    Variant,
    apply_mutant,
    expand_saturation,
    mutant_str,
    parse_mutant,
)


class TestVariant:
    def test_parse_basic(self) -> None:
        v = Variant.parse("E1369R")
        assert v.wt == "E"
        assert v.pos == 1369
        assert v.mut == "R"

    def test_str_round_trip(self) -> None:
        s = "K42A"
        assert str(Variant.parse(s)) == s

    def test_parse_strips_whitespace(self) -> None:
        assert Variant.parse("  K42A  ") == Variant("K", 42, "A")

    @pytest.mark.parametrize(
        "bad",
        ["", "E1369", "1369R", "E1369RR", "B1369R", "E1369B", "E0R", "E-5R", "elephant"],
    )
    def test_parse_rejects_malformed(self, bad: str) -> None:
        with pytest.raises(ValueError):
            Variant.parse(bad)

    def test_identity_rejected(self) -> None:
        with pytest.raises(ValueError, match="identity"):
            Variant("E", 1369, "E")

    def test_invalid_aa_rejected(self) -> None:
        with pytest.raises(ValueError):
            Variant("B", 10, "A")
        with pytest.raises(ValueError):
            Variant("A", 10, "Z")

    def test_invalid_position_rejected(self) -> None:
        with pytest.raises(ValueError):
            Variant("A", 0, "G")


class TestMutant:
    def test_single(self) -> None:
        m = parse_mutant("E1369R")
        assert m == (Variant("E", 1369, "R"),)

    def test_multi_default_separator(self) -> None:
        m = parse_mutant("E1369R/E1449H/R1556A")
        assert len(m) == 3
        assert m[0].pos == 1369
        assert m[1].pos == 1449
        assert m[2].pos == 1556

    def test_round_trip_str(self) -> None:
        s = "E1369R/E1449H/R1556A"
        assert mutant_str(parse_mutant(s)) == s

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError):
            parse_mutant("")
        with pytest.raises(ValueError):
            parse_mutant("/")


class TestApplyMutant:
    def test_single_substitution(self) -> None:
        seq = "MAAAEKKK"
        mutant = parse_mutant("E5R")
        assert apply_mutant(seq, mutant) == "MAAARKKK"

    def test_multi_substitution(self) -> None:
        seq = "MAAAEKKK"
        mutant = parse_mutant("A2G/E5R")
        assert apply_mutant(seq, mutant) == "MGAARKKK"

    def test_wt_mismatch_raises(self) -> None:
        seq = "MAAAEKKK"
        mutant = parse_mutant("K5R")
        with pytest.raises(ValueError, match="WT mismatch"):
            apply_mutant(seq, mutant)

    def test_out_of_range_raises(self) -> None:
        seq = "MAAAEKKK"
        mutant = parse_mutant("E99R")
        with pytest.raises(ValueError, match="out of range"):
            apply_mutant(seq, mutant)


class TestSaturation:
    def test_single_position(self) -> None:
        seq = "MAAA"
        muts = expand_saturation(seq, [2])
        assert len(muts) == 19
        assert all(len(m) == 1 for m in muts)
        assert all(m[0].pos == 2 and m[0].wt == "A" for m in muts)
        assert {m[0].mut for m in muts} == set("CDEFGHIKLMNPQRSTVWY")

    def test_multiple_positions(self) -> None:
        seq = "MAAA"
        muts = expand_saturation(seq, [2, 3])
        assert len(muts) == 38

    def test_deduplicates_positions(self) -> None:
        seq = "MAAA"
        muts = expand_saturation(seq, [2, 2, 2])
        assert len(muts) == 19

    def test_out_of_range_raises(self) -> None:
        seq = "MAAA"
        with pytest.raises(ValueError, match="out of range"):
            expand_saturation(seq, [99])
