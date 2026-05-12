# PLM-guided nuclease engineering — DRAFT survey (pending verification)

**Status:** DRAFT — every paper, repo, and number below must be cross-checked. Verification log at `notes/plm/verification-log.md`.
**Surveyed by:** background literature agent, 2026-05-12
**Promoted to:** `notes/plm/plm-nuclease-engineering.md` after verification

---

## Published PLM-/ML-designed nuclease variants (CLAIMED — VERIFY EACH)

| Variant | Method | Result claim | Source claim | Verified? |
|---|---|---|---|---|
| **OpenCRISPR-1** | ProGen2 fine-tuned on CRISPR-Cas Atlas; ~4M generated, ~200 tested | 403 aa diffs vs SpCas9; on-target ~55.7% vs SpCas9 ~48.3%; ~95% off-target reduction | Ruffolo et al., *Nature* 2025, DOI 10.1038/s41586-025-09298-z; bioRxiv 2024.04.22.590591 | [UNVERIFIED] |
| **NmeN4G.1** (Protein2PAM) | Transformer trained on Cas-PAM pairs; in-silico evolution of Nme1Cas9 PI | 42 N4G PAMs (vs 7 WT); 50× cleavage; matches SpCas9 in human cells | Ruffolo et al., *Nat Biotechnol* 2026, DOI 10.1038/s41587-025-02995-0; bioRxiv 2025.01.06.631536; repo Profluent-AI/protein2pam | [UNVERIFIED] |
| **enABE8e, enSdd6-CBE, enDdd1-DdCBE** (AiCE) | ESM-IF1/ProteinMPNN sample + evolutionary constraint | Smaller editing window; 1.3× fidelity; 14.3× mtDNA editing | Caixia Gao lab, *Cell* Aug 2025, S0092-8674(25)00680-4; PMID 40628259 | [UNVERIFIED] |
| **PAMmla SpCas9 variants** (MRRWMR/KRHWMR + ~1000) | Neural net on HT-PAMDA data (not strictly PLM) | Custom PAMs for allele-selective editing | Walton/Joung, *Nature* July 2025, PMID 40262634 | [UNVERIFIED] |
| **enFnCas9** | Rational, structure-guided — **no PLM** | NGG→NGR/NRG; 3.5× broader; better than SpCas9 derivatives | Chakraborty lab, *Nat Commun* 2024 49233-w; PMID 38942756 | [UNVERIFIED] |

**No published paper reports a PLM-designed FnCas9 variant as of 2026-05-12** [VERIFY — search Nature/Cell/bioRxiv]

## Tools claimed available (open-source)

| Tool | Function | Repo (claimed) | License (claimed) | Verify |
|---|---|---|---|---|
| ESM-2 | masked-LM zero-shot fitness | github.com/facebookresearch/esm | MIT | [UNVERIFIED] |
| ESM-IF1 | Inverse folding | facebookresearch/esm/examples/inverse_folding | MIT (CC-BY-NC weights) | [UNVERIFIED] |
| ESM3 / ESM Cambrian | Multimodal generative | github.com/evolutionaryscale/esm | Non-commercial open / API | [UNVERIFIED] |
| ProGen2 | AR PLM (OpenCRISPR basis) | github.com/salesforce/progen | BSD-3 | [UNVERIFIED] |
| ProteinMPNN | Backbone → sequence | github.com/dauparas/ProteinMPNN | MIT | [UNVERIFIED] |
| LigandMPNN | MPNN + ligand/DNA/RNA context | github.com/dauparas/LigandMPNN | MIT | [UNVERIFIED] |
| RFdiffusion | Backbone diffusion | github.com/RosettaCommons/RFdiffusion | BSD-style (non-commercial) | [UNVERIFIED] |
| Boltz | Protein-DNA-RNA-ligand fold | github.com/jwohlwend/boltz | MIT | [UNVERIFIED] |
| Chai-1 | Same | github.com/chaidiscovery/chai-lab | MIT | [UNVERIFIED] |
| Protein2PAM | Predicts PAM from Cas | github.com/Profluent-AI/protein2pam | Apache-2.0 | [UNVERIFIED] |
| OpenCRISPR-1 | Sequence + sgRNA only | github.com/Profluent-AI/OpenCRISPR | Bespoke "ethical use" | [UNVERIFIED] |
| CRISPR-Cas Atlas | 1M+ curated operons | github.com/Profluent-AI/CRISPR-Cas-Atlas | Open | [UNVERIFIED] |

## Industrial efforts (CLAIMED)

- **Profluent**: OpenCRISPR-1 (Nature 2025, pure sequence) + Protein2PAM (Nat Biotechnol 2026, supervised). Dominant in published PLM-nuclease work. [UNVERIFIED]
- **EvolutionaryScale (ESM3)**: released; no public nuclease design paper [VERIFY]
- **Cradle Bio, Inceptive, DeepMind, Microsoft, Macrogen**: no published nuclease work [VERIFY]
- **Arc Institute**: Evo / Evo2 DNA LMs (Nguyen et al., *Science* 2024 / 2025); not applied to Cas9 redesign in published work [UNVERIFIED]

## Workflow recommended by survey agent

1. Define objective precisely (one dominant metric)
2. Predict Cas9-sgRNA-DNA structure with Boltz-2 / AF3 — validate vs PDB 5B2O / 6I2J
3. Domain-scope to WED-PI + phosphate-lock loop (Spencer & Zhang DMS supports tolerance there)
4. Generate libraries via three parallel methods:
   - LigandMPNN on the complex (sample 1000–5000)
   - ESM-2 / ESM-1v / ESM3 zero-shot mask scoring (rank singles/doubles)
   - Train Protein2PAM-style PAM classifier; in-silico evolve toward desired PAM
5. Filter on AF3/Boltz-2 pLDDT, ipTM, MPNN seq probability, ESM perplexity, predicted ΔΔG (proteinmpnn_ddg or METL)
6. Order 96–384 variants (oligo pool / Twist); HT-PAMDA + ~10 endogenous in-cell sites
7. Active-learning loop: ESM-2 fitness head finetuned on assay results
8. Validate hits with GUIDE-seq / Digenome-seq, thermostability, base-editor compatibility

## Key papers (CLAIMED)

1. Ruffolo et al., *Nature* 2025 — OpenCRISPR-1 — DOI 10.1038/s41586-025-09298-z [UNVERIFIED]
2. Ruffolo et al., *Nat Biotechnol* 2026 — Protein2PAM — DOI 10.1038/s41587-025-02995-0 [UNVERIFIED]
3. Wang/Gao et al., *Cell* 2025 — AiCE — PMID 40628259 [UNVERIFIED]
4. Dauparas et al., *Nat Methods* 2025 — LigandMPNN — DOI 10.1038/s41592-025-02626-1 [UNVERIFIED]
5. Walton et al., *Nature* 2025 — PAMmla — PMID 40262634 [UNVERIFIED]
6. Spencer & Zhang, *Sci Rep* 2017 — SpCas9 DMS — DOI 10.1038/s41598-017-17081-y [UNVERIFIED]
7. Watson et al., *Nature* 2023 — RFdiffusion + Krishna et al., *Science* 2024 — RFdiffusion-AA [UNVERIFIED]

## Critical gaps (CLAIMED)

- No PLM-designed FnCas9 published
- No functional de novo RFdiffusion nuclease published
- No public DMS of FnCas9
- ESM-IF1 ~1024-aa limit (FnCas9 ~1629 aa) [VERIFY exact limit]
- AF3 / Boltz-2 accuracy on Cas9-sgRNA-DNA not formally benchmarked
- OpenCRISPR-1 weights not released, only sequence + license
- Tranception, Evo, Evo2 not applied to Cas9 in published work
- No Cas9-MAVE benchmark analogous to ProteinGym
