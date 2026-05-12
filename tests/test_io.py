from __future__ import annotations

from pathlib import Path

import pytest

from nuclease_design.io import FastaRecord, iter_fasta, load_fasta, parse_fasta, write_fasta


SAMPLE = """\
>sp|A0Q5Y3|CAS9_FRATN dummy header
MNFKILPIAIDLGVKNTGVFSAFYQKGTDLE
TLKK
>sp|Q99ZW2|CAS9_STRP1 another
MDKKYSIGLDIGTNS

>sp|EMPTY|EMPTY
A
"""


class TestParseFasta:
    def test_three_records(self) -> None:
        recs = parse_fasta(SAMPLE)
        assert len(recs) == 3

    def test_first_record_content(self) -> None:
        recs = parse_fasta(SAMPLE)
        assert recs[0].sequence == "MNFKILPIAIDLGVKNTGVFSAFYQKGTDLETLKK"
        assert recs[0].header.startswith("sp|A0Q5Y3")

    def test_accession_extraction(self) -> None:
        recs = parse_fasta(SAMPLE)
        assert recs[0].accession == "sp|A0Q5Y3|CAS9_FRATN"

    def test_blank_lines_tolerated(self) -> None:
        recs = parse_fasta(SAMPLE)
        assert recs[2].sequence == "A"

    def test_sequence_before_header_raises(self) -> None:
        with pytest.raises(ValueError, match="before any header"):
            parse_fasta("ACGT\n>h\nACGT")


class TestRoundTrip:
    def test_write_then_load(self, tmp_path: Path) -> None:
        recs_in = [
            FastaRecord(header="seq1", sequence="ACDEFGHIKLMNPQRSTVWY" * 5),
            FastaRecord(header="seq2 with description", sequence="MAAA"),
        ]
        path = tmp_path / "out.fasta"
        write_fasta(recs_in, path)
        recs_out = load_fasta(path)
        assert recs_out == recs_in

    def test_iter_streaming(self, tmp_path: Path) -> None:
        recs_in = [
            FastaRecord(header=f"r{i}", sequence="A" * 10) for i in range(5)
        ]
        path = tmp_path / "out.fasta"
        write_fasta(recs_in, path)
        recs_out = list(iter_fasta(path))
        assert recs_out == recs_in
