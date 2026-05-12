# ProteinGym — Indels Benchmark

**Last surveyed:** 2026-05-12
**Benchmark home:** https://proteingym.org/
**Repo:** https://github.com/OATML-Markslab/ProteinGym
**Original paper:** Notin et al., NeurIPS 2023 D&B ([OpenReview](https://openreview.net/forum?id=URoZHqAohf))
**Indels CSV path:** `benchmarks/DMS_zero_shot/indels/Spearman/Summary_performance_DMS_indels_Spearman.csv`

## What this benchmark is

Protein fitness prediction over insertion and deletion mutants — **74 DMS assays / ~300k mutants** in the v1.3 indels track. Models predict Spearman correlation between predicted and measured fitness. **Zero-shot only** — there is no supervised indels track, because indel data is too sparse for the standard CV splits.

## Zero-shot SOTA — official leaderboard (as of 2026-05-12)

From the official v1.3 indels CSV (last updated Apr 28, 2025):

| Rank | Model | Avg Spearman | Paper | Code |
|---|---|---|---|---|
| 1 | PoET (200M) | 0.517 | [NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/file/f4366126eba252699b280e8f93c0ab2f-Paper-Conference.pdf) | [OpenProteinAI/PoET](https://github.com/OpenProteinAI/PoET) |
| 2 | ProGen2 M | 0.465 | [arXiv:2206.13517](https://arxiv.org/abs/2206.13517) | [salesforce/progen](https://github.com/salesforce/progen) |
| 3 | ProGen2 Base | 0.464 | (same) | (same) |
| 4 | RITA L | 0.457 | [arXiv:2205.05789](https://arxiv.org/abs/2205.05789) | lightonai/RITA |
| 5 | Tranception M (no retrieval) | 0.453 | [arXiv:2205.13760](https://arxiv.org/abs/2205.13760) | [OATML-Markslab/Tranception](https://github.com/OATML-Markslab/Tranception) |

## Vendor-claimed SOTA (not yet on official CSV)

**PoET-2 — 0.566 Avg Spearman** (Truong & Bepler, [arXiv:2508.04724](https://arxiv.org/abs/2508.04724), Aug 2025 / Feb 2026 revision). Would be #1 by Δρ ≈ 0.05 over PoET-1 if independently confirmed. Status:

- **Preprint:** confirmed on arXiv
- **Code:** [github.com/OpenProteinAI/PoET-2](https://github.com/OpenProteinAI/PoET-2), Apache-2.0 code, non-commercial weights
- **Weights deposit:** [Zenodo 10.5281/zenodo.16815645](https://zenodo.org/records/16815645)
- **Number:** 0.566 (paper Table 1), 182M params
- **Independent confirmation:** **none.** Official ProteinGym v1.3 CSV does not include PoET-2 (April 2025 cutoff predates the preprint). Treat as author-reported pending the next benchmark refresh.

## Per-model notes

- **PoET / PoET-2** — Hierarchical "sequences-of-sequences" autoregressive transformers conditioned on a retrieved family context. Length-flexible by construction, so they natively score indels. PoET-2 adds structure conditioning, a dual causal+masked decoder, and a length bias correction. The length-adjusted log-likelihood ratio is now the standard scoring rule for autoregressive indels.
- **ProGen2 / RITA** — Pure decoder-only autoregressive PLMs on UniRef. Length-flexible but no retrieval. Trail PoET by ~5 Spearman points.
- **Tranception (no retrieval)** — Grouped-attention autoregressive. The *with-retrieval* and *TranceptEVE* variants score *worse* on indels than the no-retrieval base because MSA priors don't align cleanly across length changes.
- **SCISOR** ([arXiv:2511.07390](https://arxiv.org/abs/2511.07390), Nov 2025) — Discrete diffusion model with insertion-forward / deletion-reverse process. Claims ~0.573 Spearman, **but only on a filtered deletion-only subset** (1-3 deletions where the mutant is a strict subsequence). Not apples-to-apples with the headline 0.517 / 0.566 numbers.

## Substitutions vs. indels: what changes

**Absolute Spearmans are lower on indels** (~0.45–0.57) than on substitutions (~0.50–0.55 for top zero-shot, ~0.65+ supervised). Indels alter length and disrupt MSA alignment.

**Model rankings are nearly disjoint.** The substitutions leaderboard is dominated by structure-aware masked LMs and MSA-conditioned hybrids (VenusREM, S3F-MSA, ProSST, TranceptEVE) — *most of these literally cannot score indels* because masked-LM heads operate over fixed length. The indels leaderboard is therefore monopolized by autoregressive models.

**Models that excel on indels but underperform on substitutions:** PoET (top on indels, mid-pack on subs). Pure ProGen2/RITA rank higher relatively on indels.

**Reverse:** VenusREM, ProSST, SaProt, TranceptEVE — strong on substitutions, N/A or weak on indels.

## What's changed in the last year

1. **PoET-2 (Aug 2025)** displaced PoET-1 as the autoregressive indels leader (pending official re-scoring). Structure-conditioning and length-bias correction are the two technical levers.
2. **Protriever ([arXiv:2506.08954](https://arxiv.org/abs/2506.08954))** — end-to-end differentiable homology retrieval. Strong on substitutions; not indels-focused.
3. **SCISOR (Nov 2025)** introduced discrete diffusion for deletions — but on a redefined subset, not the canonical metric. Watch this paradigm.
4. **ProteinGym v1.3 (Apr 2025)** added substitution baselines (ESM3, ESM C, ProGen3, xTrimoPGLM) but **did not refresh the indels CSV** — so leaderboard rankings predate PoET-2.

## Caveats

- **Small assay count (~74)** — high variance, single-assay swings move the average noticeably.
- **Autoregressive length bias** — unadjusted log-likelihoods favor shorter sequences; PoET-2's length-adjusted ratio is now standard.
- **MSA-based methods are structurally excluded** — comparison set is intrinsically narrower than substitutions.
- **No public PoET-2 re-score** by ProteinGym maintainers — vendor numbers are preliminary.
- **SCISOR's 0.573 is on a filtered deletions-only subset** — not the canonical 0.517/0.566 metric.
- Benchmark conflates insertions and deletions; per-mutation-type breakdowns aren't standard.

## Recommended reading order

1. **PoET-2 paper** — [arXiv:2508.04724](https://arxiv.org/abs/2508.04724). Cleanest current statement of indels SOTA, the length-adjustment trick, and direct comparisons to PoET-1 and ProGen2.
2. **ProteinGym paper** — Notin et al., NeurIPS 2023 D&B ([OpenReview](https://openreview.net/forum?id=URoZHqAohf)). The framing of why indels are hard and the first systematic comparison; essential before reading any newer claim.

## Sources

- [ProteinGym site](https://proteingym.org/)
- [ProteinGym GitHub](https://github.com/OATML-Markslab/ProteinGym)
- [Indels CSV (raw)](https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_zero_shot/indels/Spearman/Summary_performance_DMS_indels_Spearman.csv)
- [PoET-2 arXiv:2508.04724](https://arxiv.org/abs/2508.04724)
- [PoET-2 GitHub](https://github.com/OpenProteinAI/PoET-2)
- [PoET-2 Zenodo](https://zenodo.org/records/16815645)
- [OpenProtein.AI PoET-2 blog](https://www.openprotein.ai/a-multimodal-foundation-model-for-controllable-protein-generation-and-representation-learning)
- [SCISOR arXiv:2511.07390](https://arxiv.org/abs/2511.07390)
- [Protriever arXiv:2506.08954](https://arxiv.org/abs/2506.08954)

## Related notes

- [[proteingym-substitutions]] — the companion benchmark; very different leaderboard, different winners
- [[autoregressive-plms]] — *not yet written, candidate for next survey* (PoET, ProGen2, RITA, Tranception family)
