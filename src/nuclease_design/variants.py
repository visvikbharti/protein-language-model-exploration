"""Variant representation and parsing.

A Variant is a single amino-acid substitution; a "mutant" is a tuple of one or more Variants.
String format follows the standard literature convention: ``WTpositionMUT`` (e.g., ``E1369R``),
1-indexed against the canonical reference sequence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

AA_CODES = frozenset("ACDEFGHIKLMNPQRSTVWY")
VARIANT_RE = re.compile(r"^([ACDEFGHIKLMNPQRSTVWY])(\d+)([ACDEFGHIKLMNPQRSTVWY])$")


@dataclass(frozen=True, slots=True)
class Variant:
    wt: str
    pos: int
    mut: str

    def __post_init__(self) -> None:
        if self.wt not in AA_CODES:
            raise ValueError(f"Invalid WT amino acid: {self.wt!r}")
        if self.mut not in AA_CODES:
            raise ValueError(f"Invalid mutant amino acid: {self.mut!r}")
        if self.pos < 1:
            raise ValueError(f"Position must be 1-indexed positive: {self.pos}")
        if self.wt == self.mut:
            raise ValueError(f"Variant is identity (not a mutation): {self}")

    def __str__(self) -> str:
        return f"{self.wt}{self.pos}{self.mut}"

    @classmethod
    def parse(cls, s: str) -> Variant:
        """Parse a variant string like ``E1369R`` into a Variant."""
        m = VARIANT_RE.match(s.strip())
        if m is None:
            raise ValueError(f"Could not parse variant string: {s!r}")
        wt, pos, mut = m.group(1), int(m.group(2)), m.group(3)
        return cls(wt=wt, pos=pos, mut=mut)


Mutant = tuple[Variant, ...]


def parse_mutant(s: str, separator: str = "/") -> Mutant:
    """Parse a multi-mutation string like ``E1369R/E1449H/R1556A`` into a Mutant tuple.

    Single mutations parse to a length-1 tuple.
    """
    parts = [p.strip() for p in s.split(separator) if p.strip()]
    if not parts:
        raise ValueError(f"Empty mutant string: {s!r}")
    return tuple(Variant.parse(p) for p in parts)


def apply_mutant(sequence: str, mutant: Mutant) -> str:
    """Apply a Mutant to a reference sequence, validating that WT residues match.

    Raises ValueError if any Variant's WT identity disagrees with the sequence at that position.
    """
    chars = list(sequence)
    for v in mutant:
        idx = v.pos - 1
        if idx < 0 or idx >= len(chars):
            raise ValueError(f"Position {v.pos} out of range for sequence length {len(chars)}")
        if chars[idx] != v.wt:
            raise ValueError(
                f"WT mismatch at position {v.pos}: sequence has {chars[idx]!r}, variant claims {v.wt!r}"
            )
        chars[idx] = v.mut
    return "".join(chars)


def mutant_str(mutant: Mutant, separator: str = "/") -> str:
    """Format a Mutant tuple as a string."""
    return separator.join(str(v) for v in mutant)


def expand_saturation(sequence: str, positions: Iterable[int]) -> list[Mutant]:
    """Enumerate every non-identity single substitution at each given position.

    Returns a list of length-1 Mutants, 19 per position.
    """
    pos_list = sorted(set(positions))
    mutants: list[Mutant] = []
    for pos in pos_list:
        idx = pos - 1
        if idx < 0 or idx >= len(sequence):
            raise ValueError(f"Position {pos} out of range for sequence length {len(sequence)}")
        wt = sequence[idx]
        for mut in sorted(AA_CODES):
            if mut == wt:
                continue
            mutants.append((Variant(wt=wt, pos=pos, mut=mut),))
    return mutants
