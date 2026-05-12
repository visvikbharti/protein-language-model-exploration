# ProteinGym — Substitutions Benchmark

**Last surveyed:** 2026-05-12
**Benchmark home:** https://proteingym.org/
**Repo:** https://github.com/OATML-Markslab/ProteinGym
**Original paper:** Notin et al., NeurIPS 2023 (Datasets & Benchmarks track)

## What this benchmark is

Protein fitness prediction over Deep Mutational Scanning (DMS) data — 217 assays in the v1.3 substitutions track. Models predict Spearman correlation between predicted and measured fitness for single-amino-acid mutants. Two tracks reported separately: **zero-shot** (no labels) and **supervised** (CV with Random / Modulo / Contiguous splits).

## Zero-shot SOTA (as of 2026-05-12)

| Rank | Model | Avg Spearman | Paper | Code |
|---|---|---|---|---|
| 1 (tied) | AIDO.Protein-RAG (16B) | 0.518 | [bioRxiv 2024.12.02.626519](https://www.biorxiv.org/content/10.1101/2024.12.02.626519v1) | [genbio-ai/ModelGenerator](https://github.com/genbio-ai/ModelGenerator) |
| 1 (tied) | VenusREM | 0.518 | [arXiv:2410.21127](https://arxiv.org/abs/2410.21127) (ISMB/ECCB 2025) | [ai4protein/VenusREM](https://github.com/ai4protein/VenusREM) |
| 3 | ProSST (K=2048) | 0.507 | NeurIPS 2024 | [ai4protein/ProSST](https://github.com/ai4protein/ProSST) |
| 4 | ProSST (K=4096) | 0.498 | (same) | (same) |
| 5 | S3F-MSA | 0.496 | [arXiv:2412.01108](https://arxiv.org/abs/2412.01108) | [DeepGraphLearning/S3F](https://github.com/DeepGraphLearning/S3F) |

Top 10 honorable mentions: S2F-MSA (0.488), Protriever (0.479, [arXiv:2506.08954](https://arxiv.org/abs/2506.08954)), ESCOTT (0.476), PoET-200M (0.470).

**Unverified vendor claim:** PoET-2 (OpenProtein.AI, 2025) — claimed at-or-near VenusREM with 182M params, SOTA on indels + higher-order mutations + supervised. No arXiv ID located; not yet a distinct leaderboard row.

## Supervised SOTA

| Rank | Model | Avg Spearman | Paper |
|---|---|---|---|
| 1 | Kermut | 0.657 | [arXiv:2407.00002](https://arxiv.org/abs/2407.00002) (NeurIPS 2024 Spotlight) |
| 2 | ProteinNPT | 0.619 | NeurIPS 2023 |
| 3 | MSA Transformer embeddings + head | 0.581 | ICML 2021 |
| 4 | Tranception embeddings | 0.548 | ICML 2022 |
| 5 | ESM-1v embeddings | 0.535 | NeurIPS 2021 |

Supervised Spearman is averaged across Random / Modulo / Contiguous CV schemes.

## Architectures of the top models

- **AIDO.Protein-RAG (16B)** — 16B sparse MoE PLM (8 experts, top-2 routing) trained on ~1.2T amino acids of UniRef90 + ColabFoldDB. RAG variant cross-attends to retrieved MSAs at inference.
- **VenusREM** — Retrieval-enhanced fusion of ProSST logits with PSSM evolutionary signal from retrieved homologs. Logits-level (not embedding-level) fusion. Compact and fast. Held #1 from ~April 2025 through early 2026.
- **ProSST** — Masked-LM Transformer with disentangled attention over sequence tokens + quantized structure tokens (learned codebook over local 3D environments). K = codebook size.
- **S3F-MSA** — Sequence + Structure + Surface: sequence PLM combined with GVP networks encoding backbone and surface topology, ensembled with EVE z-scores ("-MSA" suffix).
- **Kermut (supervised winner)** — Gaussian-process composite kernel fusing ESM-2 embeddings, structural neighborhood kernels, mutation-similarity priors. Trains in ~10 min vs. hundreds of GPU-hours for ProteinNPT.

## The current narrative

**Scale has plateaued; retrieval has taken over.** Per Notin's ["Scaling Wall" essay](https://pascalnotin.substack.com/p/have-we-hit-the-scaling-wall-for), PLM perf saturates ~1–4B params and *degrades* past ~5B. The only billion-param model in the top 10 (AIDO-RAG 16B) wins via its retrieval head, not its scale. SaProt — 2024's leader — has fallen out of the top 10.

Three flavors of "PLM + structure + retrieved evolution" are competing:
1. MSA-conditioned cross-attention (AIDO-RAG)
2. Logits-level PSSM fusion (VenusREM)
3. Differentiable end-to-end retrieval (Protriever, ICML 2025) — removes JackHMMER preprocessing, ~100× faster, matches PoET-200M

## Caveats when reading the leaderboard

- **MSA leakage is real and uncontrolled.** Retrieval pulls from UniRef/ColabFoldDB. If a test assay's close homologs are in the index, scores inflate. The Random/Modulo/Contiguous splits split *mutations*, not homolog availability.
- **0.518 headline hides huge per-assay variance.** Top 5 cluster within ~0.02 globally but flip rank on individual assays. Per-DMS Spearman ranges ~0 (low-MSA viral) to >0.7 (conserved enzymes).
- **Test-set tuning risk.** No hidden test split; several top models were tuned against the public leaderboard.
- **Zero-shot vs. supervised numbers are not on the same axis.** Kermut 0.657 ≠ "better than" VenusREM 0.518 — Kermut sees labels via CV.
- **Random split is the easiest.** Modulo and Contiguous drop scores ~0.05–0.10. Single-number quotes usually mean Random.

## Recommended reading order

1. [Notin, "Have We Hit the Scaling Wall for Protein Language Models?"](https://pascalnotin.substack.com/p/have-we-hit-the-scaling-wall-for) — cleanest narrative on the retrieval-over-scale shift, by the benchmark's lead author.
2. [Protriever (arXiv:2506.08954)](https://arxiv.org/abs/2506.08954) — most architecturally interesting; makes homolog retrieval differentiable and end-to-end trainable.

## Sources

- [ProteinGym site](https://proteingym.org/)
- [Zero-shot CSV (raw)](https://github.com/OATML-Markslab/ProteinGym/blob/main/benchmarks/DMS_zero_shot/substitutions/Spearman/Summary_performance_DMS_substitutions_Spearman.csv)
- [VenusREM repo](https://github.com/ai4protein/VenusREM)
- [AIDO.Protein-RAG HF card](https://huggingface.co/genbio-ai/AIDO.Protein-RAG-16B)
- [PoET-2 OpenProtein.AI blog](https://www.openprotein.ai/a-multimodal-foundation-model-for-controllable-protein-generation-and-representation-learning)

## Related notes

- [[proteingym-indels]] — companion benchmark; nearly disjoint leaderboard (autoregressive models dominate; PoET / PoET-2 lead)
- [[plm-landscape-2026]] — *not yet written, candidate for next survey*
- [[retrieval-augmented-plms]] — *not yet written*
