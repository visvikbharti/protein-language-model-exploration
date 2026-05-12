"""Sequence and structure I/O — FASTA, PDB, UniProt fetch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class FastaRecord:
    header: str
    sequence: str

    @property
    def accession(self) -> str:
        return self.header.split()[0] if self.header else ""


def parse_fasta(text: str) -> list[FastaRecord]:
    """Parse FASTA text into a list of records.

    Tolerant of blank lines and trailing whitespace; raises on malformed input
    (e.g. sequence before any header).
    """
    records: list[FastaRecord] = []
    header: str | None = None
    seq_chunks: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(header=header, sequence="".join(seq_chunks)))
            header = line[1:].strip()
            seq_chunks = []
        else:
            if header is None:
                raise ValueError("FASTA sequence line appears before any header")
            seq_chunks.append(line.replace(" ", ""))
    if header is not None:
        records.append(FastaRecord(header=header, sequence="".join(seq_chunks)))
    return records


def load_fasta(path: Path | str) -> list[FastaRecord]:
    """Load FASTA from a file path."""
    return parse_fasta(Path(path).read_text())


def iter_fasta(path: Path | str) -> Iterator[FastaRecord]:
    """Stream FASTA records one at a time (memory-friendly for very large files)."""
    header: str | None = None
    seq_chunks: list[str] = []
    with Path(path).open() as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield FastaRecord(header=header, sequence="".join(seq_chunks))
                header = line[1:].strip()
                seq_chunks = []
            else:
                if header is None:
                    raise ValueError("FASTA sequence line appears before any header")
                seq_chunks.append(line.replace(" ", ""))
    if header is not None:
        yield FastaRecord(header=header, sequence="".join(seq_chunks))


def write_fasta(records: list[FastaRecord], path: Path | str, *, line_width: int = 60) -> None:
    """Write FASTA records to a file with given line width."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for r in records:
            f.write(f">{r.header}\n")
            seq = r.sequence
            for i in range(0, len(seq), line_width):
                f.write(seq[i : i + line_width] + "\n")
