"""Variant scoring backends.

All scorers obey the :class:`Scorer` Protocol: given a reference sequence and a list of mutants,
return a 1-D NumPy array of scalar scores where higher = better (favored).

Implementations are kept in separate modules so that a user only needs to install the deps
for the scorers they intend to run. Importing this package does not pull in torch/transformers.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from nuclease_design.variants import Mutant


@runtime_checkable
class Scorer(Protocol):
    """A callable that ranks mutants by predicted desirability."""

    name: str

    def score(self, sequence: str, mutants: list[Mutant]) -> np.ndarray:
        """Return a (len(mutants),) array of scalar scores. Higher = better."""
        ...
