"""ESM-2 zero-shot mask-marginal scoring.

This module wraps fair-esm's ESM-2 checkpoints for variant fitness prediction.

REQUIRES: fair-esm (pip install fair-esm), torch.
REQUIRES (weight download, first run only): ~150 MB for esm2_t12_35M_UR50D,
~650 MB for esm2_t33_650M_UR50D. Downloaded to ~/.cache/torch/hub/checkpoints/.

CPU is supported but slow. For 1629-aa FnCas9 with esm2_t12_35M, one forward
pass takes a few seconds on Apple-Silicon CPU. For the 650M model on CPU,
expect ~30 s per pass. Use GPU/MPS when available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from nuclease_design.variants import Mutant, Variant

log = logging.getLogger(__name__)

# Available checkpoints, smallest first. Tuple of (fair-esm checkpoint name, # params).
ESM2_CHECKPOINTS: dict[str, tuple[str, int]] = {
    "esm2_8M": ("esm2_t6_8M_UR50D", 8_000_000),
    "esm2_35M": ("esm2_t12_35M_UR50D", 35_000_000),
    "esm2_150M": ("esm2_t30_150M_UR50D", 150_000_000),
    "esm2_650M": ("esm2_t33_650M_UR50D", 650_000_000),
    "esm2_3B": ("esm2_t36_3B_UR50D", 3_000_000_000),
}


@dataclass
class ESMScorer:
    """ESM-2 mask-marginal log-likelihood-ratio scorer.

    Score for a single substitution V = WTposMUT is::

        LLR(V) = log P(MUT | seq with pos masked) - log P(WT | seq with pos masked)

    A multi-substitution Mutant is scored as the sum of single-substitution LLRs
    (the independence approximation; documented limitation when epistasis matters).
    """

    name: str = "esm2_35M"
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.name not in ESM2_CHECKPOINTS:
            raise ValueError(f"Unknown ESM checkpoint: {self.name!r}. Choose from {list(ESM2_CHECKPOINTS)}")
        # Lazy-load the model on first use so importing this module is cheap.
        self._model = None
        self._alphabet = None
        self._batch_converter = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        import torch  # noqa: F401  (will be needed)
        import esm

        ckpt_name, n_params = ESM2_CHECKPOINTS[self.name]
        log.info("Loading %s (%d params) on %s", ckpt_name, n_params, self.device)
        model, alphabet = esm.pretrained.load_model_and_alphabet(ckpt_name)
        model = model.eval().to(self.device)
        self._model = model
        self._alphabet = alphabet
        self._batch_converter = alphabet.get_batch_converter()

    def _mask_token(self) -> int:
        assert self._alphabet is not None
        return int(self._alphabet.mask_idx)

    def score_single(
        self,
        sequence: str,
        positions: Iterable[int],
    ) -> dict[int, np.ndarray]:
        """Return mask-marginal logits at each given position.

        Output maps 1-indexed position -> array of shape (20,), giving
        log-probability of each amino acid (ordered by alphabet) at that
        position after masking it.
        """
        import torch

        self._ensure_loaded()
        assert self._model is not None and self._alphabet is not None and self._batch_converter is not None

        out: dict[int, np.ndarray] = {}
        positions = sorted(set(positions))

        # The fair-esm batch_converter expects (name, seq) tuples. It prepends a CLS token,
        # so position p (1-indexed) becomes token index p in the model input.
        for pos in positions:
            idx = pos - 1
            if idx < 0 or idx >= len(sequence):
                raise ValueError(f"Position {pos} out of range for sequence length {len(sequence)}")
            masked = sequence[:idx] + "<mask>" + sequence[idx + 1:]
            # batch_converter wants the mask token spelled out via the alphabet, not via "<mask>"
            # — pass the raw sequence and patch the token id directly.
            _, _, tokens = self._batch_converter([("variant", sequence)])
            tokens = tokens.to(self.device)
            # token index for pos (1-indexed) in fair-esm is pos (CLS at 0)
            tok_idx = pos  # CLS prepended → 1-indexed pos maps to token index pos
            tokens[0, tok_idx] = self._mask_token()
            with torch.no_grad():
                out_dict = self._model(tokens)
            logits = out_dict["logits"][0, tok_idx]  # (vocab_size,)
            log_probs = torch.log_softmax(logits, dim=-1).cpu().numpy()
            out[pos] = log_probs

        return out

    def score(self, sequence: str, mutants: list[Mutant]) -> np.ndarray:
        """Score each Mutant against the reference sequence.

        Returns a (len(mutants),) array of log-likelihood ratios summed across
        the positions in each Mutant. Higher = better.
        """
        if not mutants:
            return np.zeros((0,), dtype=np.float64)

        # Collect every unique position across all mutants, score each once.
        all_positions = {v.pos for mut in mutants for v in mut}
        log.info("Scoring %d unique positions for %d mutants", len(all_positions), len(mutants))
        log_probs = self.score_single(sequence, all_positions)

        # alphabet token order — we'll index by token id.
        assert self._alphabet is not None
        tok_to_aa = {self._alphabet.get_idx(aa): aa for aa in "ACDEFGHIKLMNPQRSTVWY"}
        aa_to_tok = {aa: tok for tok, aa in tok_to_aa.items()}

        scores = np.zeros(len(mutants), dtype=np.float64)
        for i, mut in enumerate(mutants):
            total = 0.0
            for v in mut:
                lp = log_probs[v.pos]
                total += float(lp[aa_to_tok[v.mut]] - lp[aa_to_tok[v.wt]])
            scores[i] = total
        return scores


def score_saturation(
    scorer: ESMScorer,
    sequence: str,
    positions: Iterable[int],
) -> list[tuple[Variant, float]]:
    """Convenience: score every non-identity substitution at each position.

    Returns a list of (Variant, score) sorted by score descending.
    """
    from nuclease_design.variants import AA_CODES

    scorer._ensure_loaded()
    log_probs = scorer.score_single(sequence, positions)
    assert scorer._alphabet is not None
    aa_to_tok = {aa: scorer._alphabet.get_idx(aa) for aa in AA_CODES}

    results: list[tuple[Variant, float]] = []
    for pos, lp in log_probs.items():
        wt = sequence[pos - 1]
        if wt not in AA_CODES:
            continue
        wt_logp = float(lp[aa_to_tok[wt]])
        for mut in sorted(AA_CODES):
            if mut == wt:
                continue
            llr = float(lp[aa_to_tok[mut]]) - wt_logp
            results.append((Variant(wt=wt, pos=pos, mut=mut), llr))
    results.sort(key=lambda x: -x[1])
    return results
