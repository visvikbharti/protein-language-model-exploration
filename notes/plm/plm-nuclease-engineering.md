# PLM-guided nuclease engineering — landscape

**Last verified:** 2026-05-12 (round 1; see `verification-log.md`)

## Headline

The published precedent for **PLM-designed CRISPR nucleases** is small but concrete. Profluent has the two clearest demonstrations — **OpenCRISPR-1** (full-sequence generative, *Nature* 2025) and **Protein2PAM / NmeN4G.1** (in-silico PAM evolution, *Nat Biotechnol* 2026). Caixia Gao's **AiCE** framework demonstrates the inverse-folding-plus-evolutionary-constraint approach for base-editor enzyme components. **No published paper has applied PLM-guided design to FnCas9 specifically** as of 2026-05-12.

## Published PLM-/ML-designed nuclease variants — verified

| Variant / design | Method | Headline result | Primary source |
|---|---|---|---|
| **OpenCRISPR-1** | ProGen2-base fine-tuned on the CRISPR-Cas Atlas (>1M operons, 26 Tb (meta)genomes); sequences generated and ~200 tested* | 403 aa differences from SpCas9; on-target **55.7% vs SpCas9 48.3%** in HEK293T; **~95% off-target reduction** (0.32% vs 6.07%); reduced immunogenicity (iELISA) | Ruffolo, Nayfach, Gallagher, Bhatnagar et al., *Nature* 645:518-525 (2025), DOI [10.1038/s41586-025-09298-z](https://doi.org/10.1038/s41586-025-09298-z); bioRxiv [2024.04.22.590591](https://www.biorxiv.org/content/10.1101/2024.04.22.590591v1) |
| **NmeN4G.1 (Protein2PAM)** | Transformer trained on 45k+ Cas-PAM pairs → PAM oracle → in-silico evolution of Nme1Cas9 PI domain | **Up to 50× higher in-vitro cleavage** vs WT; broadened PAM recognition | Nayfach et al. (first author Nayfach; Ruffolo et al.), *Nat Biotechnol* (online 2 Feb 2026), DOI [10.1038/s41587-025-02995-0](https://doi.org/10.1038/s41587-025-02995-0); bioRxiv [2025.01.06.631536](https://www.biorxiv.org/content/10.1101/2025.01.06.631536v1) |
| **enABE8e, enSdd6-CBE, enDdd1-DdCBE (AiCE)** | Sample mutations from ESM-IF1 / ProteinMPNN; intersect with evolutionary constraints (no DMS oracle needed) | enABE8e: 5-bp editing window (narrowed); enSdd6-CBE: 1.3× fidelity; enDdd1-DdCBE: 14.3× mitochondrial editing | Gao lab, *Cell* (2025), DOI [10.1016/j.cell.2025.06.014](https://doi.org/10.1016/j.cell.2025.06.014), PMID [40628259](https://pubmed.ncbi.nlm.nih.gov/40628259/) |
| **PAMmla SpCas9 variants** (KRHWMR / MRRWMR + ~1000 others) | Neural net trained on HT-PAMDA experimental data (supervised, not PLM strictly) → custom PAMs for allele-selective editing | Allele-selective editing demonstrated | Silverstein et al. (Kleinstiver lab), *Nature* (2025), DOI [10.1038/s41586-025-09021-y](https://doi.org/10.1038/s41586-025-09021-y), PMID [40262634](https://pubmed.ncbi.nlm.nih.gov/40262634/) |
| **enFnCas9** | Rational, structure-guided — **NOT PLM-designed** | PAM relaxation NGG→NRG/NGR; ~3.5× site expansion; ~1,300× lower off-targets than SpCas9 | Acharya et al., *Nat Commun* 15:5471 (2024); see [[enFnCas9-overview]] |

\* Quantitative details of OpenCRISPR's screen (~240k Cas9s in atlas, ~4M generated, ~200 tested in mammalian cells) are reported in summaries but were not independently verifiable from the open abstract — full-text access needed.

> **Gap:** there is **no published PLM-designed FnCas9 variant** to date. Our project would be the first credible attempt.

## Adjacent industry / lab efforts (verified)

- **Profluent** — dominant in published work. Two key papers above + tooling at [Profluent-AI](https://github.com/Profluent-AI). Their pipeline is **sequence-only** — no structure-conditioned step in the published OpenCRISPR-1 paper.
- **EvolutionaryScale (ESM3)** — model released ([github.com/evolutionaryscale/esm](https://github.com/evolutionaryscale/esm)); **no published nuclease design paper** found in searches.
- **Arc Institute (Evo / Evo 2)** — DNA language models. Evo (Nguyen et al., *Science* 2024, DOI [10.1126/science.ado9336](https://doi.org/10.1126/science.ado9336)); **Evo 2** (Brixi et al., *Nature* 2026, DOI [10.1038/s41586-026-10176-5](https://doi.org/10.1038/s41586-026-10176-5)). Not yet published applied to Cas9 redesign.
- **DeepMind / Isomorphic** — AlphaFold3 for complex prediction; no nuclease-design papers found.
- **Inceptive, Cradle Bio, Microsoft, Macrogen** — no public nuclease-design publications found in searches.

## Standard methods we'll use

### Structure-conditioned design
- **LigandMPNN** (Dauparas et al., *Nat Methods* 22:717-723, 2025, DOI [10.1038/s41592-025-02626-1](https://doi.org/10.1038/s41592-025-02626-1)) — ProteinMPNN extension that respects DNA/RNA/ligand atoms. **The current best choice for Cas9 PI-domain redesign** because the sgRNA + target DNA atoms enter the conditioning.
- **ProteinMPNN** (Dauparas et al., *Science* 2022) — fallback / sgRNA-only context.
- **RFdiffusion** (Watson et al., *Nature* 2023, DOI [10.1038/s41586-023-06415-8](https://doi.org/10.1038/s41586-023-06415-8)) — backbone motif scaffolding. No published functional de-novo Cas9 yet; **do not expect "RFdiffusion → working Cas9" off the shelf.**
- **RFdiffusion-AA** (Krishna et al., *Science* 2024, DOI [10.1126/science.adl2528](https://doi.org/10.1126/science.adl2528)) — atomistic extension; useful for active-site detailing.

### Zero-shot fitness prediction
- **ESM-2** (Lin et al., *Science* 2023) — masked-LM likelihood ratios. Repo archived in 2024 (still functional, no updates). For our purposes adequate; for new work consider ESM-3.
- **ESM-3 / ESM Cambrian** (EvolutionaryScale 2024 / 2025) — multimodal sequence + structure + function. Repo active.
- **ESM-IF1** — inverse folding scoring. Context-window: practical limit around several hundred to ~1000 residues from prior literature; **the often-quoted "1024-aa limit" is not stated in the GitHub README** — chunk FnCas9 (1629 aa) by domain.

### Complex prediction
- **Boltz / Boltz-2** ([github.com/jwohlwend/boltz](https://github.com/jwohlwend/boltz), MIT) — handles protein + DNA + RNA + ligand. Active development. **Our primary choice** for predicting FnCas9-sgRNA-DNA complexes.
- **Chai-1** ([github.com/chaidiscovery/chai-lab](https://github.com/chaidiscovery/chai-lab), **Apache-2.0**) — comparable scope; alternative to Boltz.
- **AlphaFold3** — server-only access for predictions; weights restricted. Useful for cross-validation of Boltz output.

### Stability / ΔΔG
- **proteinmpnn_ddg** (Peptone Ltd, [github.com/PeptoneLtd/proteinmpnn_ddg](https://github.com/PeptoneLtd/proteinmpnn_ddg)) — saturation ΔΔG from PDB.
- **METL** (Mutational Effects Transfer Learning, [github.com/gitter-lab/metl](https://github.com/gitter-lab/metl)) — fine-tunable fitness head.

### Supervised PAM oracle
- **Protein2PAM** ([github.com/Profluent-AI/Protein2PAM](https://github.com/Profluent-AI/protein2pam)) — the exact recipe used for NmeN4G.1. **Polyform-NC license** (non-commercial only).

### Sequence-level generative
- **ProGen2** ([github.com/salesforce/progen](https://github.com/salesforce/progen), BSD-3, stale since 2023) — basis for OpenCRISPR-1 fine-tuning.
- **ESM-3** for multimodal generation if structure conditioning is desired.

## Reference / training data

- **CRISPR-Cas Atlas** ([github.com/Profluent-AI/CRISPR-Cas-Atlas](https://github.com/Profluent-AI/CRISPR-Cas-Atlas)) — >1M operons. **License: CC BY-NC 4.0** (non-commercial). Best Cas-family training set.
- **SpCas9 DMS** — Spencer & Zhang, *Sci Rep* 7:16836 (2017), DOI [10.1038/s41598-017-17081-y](https://doi.org/10.1038/s41598-017-17081-y) — only published Cas9 DMS by primary author; homology basis for FnCas9 priors.
- **No public DMS of FnCas9** — gap to fill (or work around with homology to SpCas9 DMS).

## Recommended workflow for FnCas9 → enFnCas9-like redesign (small lab, 2026)

1. **Define one dominant metric** for screening. E.g.: keep WT-FnCas9 specificity (≤2× off-target rate over WT), expand PAM beyond NRG/NGR, raise HEK293T cleavage rate at one canonical locus (HBB, EMX1, RUNX1).
2. **Predict FnCas9-sgRNA-DNA complex with Boltz-2 or Chai-1**. Validate the structure matches PDB 5B2O before any downstream design step.
3. **Domain-scope the redesign.** Restrict to **WED–PI domain + phosphate-lock loop**, matching the enFnCas9 paradigm. The SpCas9 DMS (Spencer 2017) confirms this region tolerates mutations; HNH and RuvC catalytic cores do not.
4. **Three parallel candidate-library generators**:
   - **LigandMPNN** on the predicted complex (DNA + sgRNA as ligand context) — 1,000–5,000 sequences per fixed-residue mask.
   - **ESM-2 / ESM-IF1 / ESM-3 zero-shot** masked likelihood across the PI domain (single + double mutants).
   - **Protein2PAM-style oracle** trained on Cas-PAM data → in-silico evolve toward NRG/NGR or broader (the Profluent recipe).
5. **Filter computationally**:
   - Boltz/Chai-1 pLDDT and ipTM for the Cas9-sgRNA-DNA complex (stability proxy)
   - ProteinMPNN / LigandMPNN sequence log-likelihood
   - ESM-2 perplexity
   - proteinmpnn_ddg or METL for predicted ΔΔG
   - Solvent accessibility filter (avoid burying charged residues)
6. **Synthesize 96–384 variants** via oligo pool / Twist; assay (a) HT-PAMDA in vitro, (b) ~10 endogenous in-cell sites for editing rate.
7. **Active-learning round 2**: fine-tune an ESM-2 fitness head on round-1 assay data; pick 96 more variants.
8. **Validate top hits** with GUIDE-seq / Digenome-seq off-target profiling, thermostability, and base-editing compatibility if downstream.

## Reading order for the project

1. **Acharya et al. 2024 (enFnCas9)** — the target we're trying to match or exceed. [[enFnCas9-overview]]
2. **Ruffolo et al. 2025 (OpenCRISPR-1)** — the canonical PLM-generated-nuclease precedent. DOI 10.1038/s41586-025-09298-z.
3. **Nayfach et al. 2026 (Protein2PAM)** — the directly relevant in-silico PAM evolution recipe. DOI 10.1038/s41587-025-02995-0.
4. **AiCE (*Cell* 2025)** — small-lab-friendly inverse-folding + evolutionary filter. DOI 10.1016/j.cell.2025.06.014.
5. **Dauparas et al. 2025 (LigandMPNN)** — required because Cas9 binds DNA. DOI 10.1038/s41592-025-02626-1.
6. **Silverstein et al. 2025 (PAMmla)** — best ML+HT-PAMDA loop example. DOI 10.1038/s41586-025-09021-y.
7. **Spencer & Zhang 2017 (SpCas9 DMS)** — only published Cas9 DMS; homology prior for FnCas9. DOI 10.1038/s41598-017-17081-y.

## Critical gaps (verified)

- No PLM-designed FnCas9 published
- No functional de-novo nuclease from RFdiffusion published (binders yes; nucleases no)
- No public DMS of FnCas9
- AF3 / Boltz-2 not benchmarked on Cas9-sgRNA-DNA in published work
- OpenCRISPR-1 weights not publicly released — only sequence + license
- Evo 2 not yet applied to Cas9 engineering (gap and opportunity)
- No Cas9-MAVE benchmark analogous to ProteinGym

## Related notes

- [[enFnCas9-overview]]
- [[verification-log]]
- [[tools-inventory]] (in `docs/`)
- [[proteingym-substitutions]], [[proteingym-indels]] — PLM scoring benchmarks
