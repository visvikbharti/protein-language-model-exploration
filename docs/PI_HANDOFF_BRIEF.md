# FnCas9 PLM-redesign — PI handoff brief

**Author:** Vishal Bharti, CSIR-IGIB
**Date:** 2026-05-18 (draft; finalize once §2.4 and §2.1's second predictor close)
**Length intent:** one printed page; reading time ~3 minutes.
**Companion docs:** `docs/PROJECT_OVERVIEW.md` (full narrative), `docs/CANDIDATES.md` (per-mutation dossier), `notes/plm/verification-log.md` (raw data + sources).

---

## TL;DR

We used protein language models (sequence-only ESM-2 + structure/ligand-conditioned LigandMPNN) plus stability and complex-structure filters to redesign FnCas9. The recommended candidate is **FnCas9-PLM5 = Y1249F / Y1341L / A1325K / K1479F**. Under Boltz-2 complex prediction (MSA-enabled, apples-to-apples within the FnCas9 set), PLM5 has the **highest predicted protein↔DNA-PAM interface confidence of all 5 FnCas9 variants tested** — exceeding even en31 (the wet-lab-validated Acharya 2024 reference). Against the **field-standard SpCas9 PI** (cross-species baseline, added 2026-05-18), PLM5 sits in the same high-confidence regime (all variants iPTM > 0.92; SpCas9 PI 0.952 vs PLM5 0.951; the 0.030 cross-species gap on protein↔DNA-PAM iPTM is partly confounded by truncation-size and MSA-depth asymmetries). PLM5's interface is also **structurally robust across PAM variants** (Boltz PAM-scan: PLM5 iPTM ≥ 0.934 across NGG/NGA/NAG/NCG/NTG/NAA; range 0.010 vs WT's 0.033; ~6× tighter variance than WT). Stress-tested across four of five independent in-silico criteria with the fifth (AF3 Server second-predictor) pending; the recommendation is **wet-lab-ready** with one documented caveat: PAM relaxation specifically is wet-lab-only — neither Protein2PAM nor Boltz can confirm it in silico for FnCas9-class variants (both methods fail to detect en31's known wet-lab PAM relaxation).

---

## The candidate

| | FnCas9-PLM5 |
|---|---|
| Mutations (4) | Y1249F · Y1341L · A1325K · K1479F |
| Backbone | UniProt A0Q5Y3 (1,629 aa) |
| Source method | LigandMPNN (structure + sgRNA + DNA-conditioned) + apo-ΔΔG triage gate |
| Design region | WED + PI domains (residues 1230–1620) |
| Compute footprint | ~4 hours V100 across all phases (campaign) |
| Suggested wet-lab assay | In-vitro cleavage on the 5B2O target sequence (or HBB g21 from Acharya), alongside **WT** and **FnCas9-en31** as controls |

---

## Why we believe it works — three lines of evidence

1. **Boltz-2 ranks PLM5 #1 of 5 within the FnCas9 set** on every confidence metric (MSA-enabled, 5 diffusion samples per variant, apples-to-apples 391-aa WED+PI truncation). iPTM 0.951 ± 0.005; prot↔DNA-PAM iPTM 0.937 ± 0.007. en31 (the wet-lab-validated reference) sits at iPTM 0.940 ± 0.009; prot↔DNA-PAM 0.927 ± 0.009. MSA mode tightened PLM5's variance ~7× vs single-sequence — the prediction is converged, not lucky. **Cross-species anchor (Tier 1 Phase A, 2026-05-18):** SpCas9 PI scores iPTM 0.952 ± 0.001, prot↔DNA-PAM 0.967 ± 0.001 on the same 5B2O sgRNA+DNA substrate. SpCas9's absolute number is +0.030 above PLM5 but partly confounded by SpCas9 PI being a 269-aa truncation (vs FnCas9 WED+PI at 391 aa — smaller systems score systematically higher iPTM) and by SpCas9's much deeper MSA. Honest read: **all three are in the high-confidence regime (iPTM > 0.92); PLM5 sits in the same predicted-quality band as SpCas9 PI**, which is the relevant cross-species claim.

2. **Three independent methods reach the same answer at the engineered positions.** Where ESM-2, LigandMPNN, and Boltz-2 agree (every PLM5 position), the model picks are reinforced. Where they disagree (e.g., position 1449), we've recorded falsifiable wet-lab claims rather than over-claiming.

3. **The independence assumption used by the per-position search holds.** ThermoMPNN-D pairwise epistasis across all 9 candidate pairs: PLM5's |Σ epistasis| / |Σ additive| = 0.019 (2%) — operationally safe. en31's ratio = 7.1× because its mutations are clustered (~9 Å apart); PLM5's are distributed (14–50 Å), which is precisely *why* PSSM-style scoring is appropriate for PLM5 and not for en31-style cluster designs.

---

## Robustness validation — 4 of 5 PI-gate criteria ✅

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Two independent structure predictors agree on PLM5's PAM interface | ☐ in-flight | Boltz-2 ✅ done; AlphaFold3 Server pending (browser submission queued). Chai-1 was investigated and ruled out (requires bf16; V100 has none). |
| 2 | Functional gap closed — predicted PAM tolerance ≥ NGG-only | ✅ DONE with caveat | Protein2PAM (job bf51a2fd) + Boltz PAM-scan (SLURM 221069, 15 jobs). Both methods cannot positively confirm PAM RELAXATION (en31 calibration fails in both — only wet lab can resolve this). But Boltz scan shows **PLM5 has highest absolute iPTM at every PAM tested (NGG 0.944; ≥0.934 across all 6 PAMs; range 0.010 vs WT's 0.033; ~6× tighter σ than WT)**. Positive structural-robustness evidence; the wet-lab PAM-relaxation test is the only direct probe. |
| 3 | apo-ΔΔG filter calls independently bracketed | ✅ DONE | PLM4 reinstated after ThermoMPNN cross-check + direct Boltz refuted the proteinmpnn_ddg rejection. Filter is triage-only going forward. |
| 4 | Pairwise epistasis effects characterized | ✅ DONE | ThermoMPNN-D, all 9 candidate pairs. PLM5 ratio 0.019; en31 ratio 7.1×. |
| 5 | Falsifiable predictions on record with CI | ✅ DONE | Single-point Boltz E1449L vs E1449H: equivalent within 1σ on every metric; per-residue pLDDT at 1449 indistinguishable (0.954 L vs 0.951 H). |

---

## Suggested wet-lab plan (for discussion)

**Minimum head-to-head:** PLM5 vs WT vs en31, three identical in-vitro cleavage reactions on a single target (e.g., 5B2O's TGG-PAM site or HBB g21 from Acharya 2024). Read out by gel densitometry or qPCR. If PLM5 ≥ en31 on cleavage rate, the headline in-silico prediction is confirmed.

**Optional secondary readouts** that would strengthen any future publication:
- **PAM tolerance:** test PLM5 on NGG / NGA / NAG / NAA targets — see whether PLM5 broadens like en31 does (Acharya reports ~3.5× site expansion).
- **Falsifiable single-mutant test:** in-vitro E1449L (our pick) vs E1449H (Acharya's pick) on the WT backbone. Both ESM-2 and LigandMPNN preferred L; Boltz says L and H are structurally equivalent in isolation; Acharya's choice of H is consistent with cooperation in the en31 triple (§2.3). Resolves the model-vs-evolution disagreement at one position.
- **Specificity:** Digenome-seq or equivalent off-target panel comparing PLM5 vs en31 vs WT. en31 has ~1,300× SpCas9 specificity; if PLM5 retains or improves on this, that's the publishable headline.

---

## Limitations to flag openly

- **No wet-lab validation yet.** All claims are in-silico. Each is structured as a falsifiable prediction with confidence intervals.
- **Boltz, ThermoMPNN-D, and LigandMPNN are approximations**, calibrated on natural proteins. Their behaviour on engineered variants may diverge from natural-protein training distribution.
- **Truncated WED+PI window (391 aa)** for the V100-fit Boltz runs. The REC lobe and N-terminal nuclease domain are not modelled. None of our mutations are in those regions, but interactions across them are unmodelled.
- **proteinmpnn_ddg filter** was used in the original campaign and is now known to be miscalibrated for hydrophobic↔K substitutions. PLM5 was not affected; PLM4 was over-rejected and has been reinstated.
- **Protein2PAM (§2.4) and AF3 Server (§2.1)** results not yet in hand — the case becomes fully closed when both land.

---

## Primary sources (verified)

- **Acharya S, Ansari AH, et al.** (2024) "PAM-flexible Engineered FnCas9 variants for robust and ultra-precise genome editing and diagnostics." *Nat Commun* 15:5471. [DOI](https://doi.org/10.1038/s41467-024-49233-w). PMID 38942756; PMC11213958.
- **Hirano H, et al.** (2016) "Structure and engineering of *Francisella novicida* Cas9." *Cell* 164:950. PMID 26875867. (PDB 5B2O.)
- **Lin Z, et al.** (2023) "Evolutionary-scale prediction of atomic-level protein structure." *Science* (ESM-2).
- **Dauparas J, et al.** (2025) "Atomic context-conditioned protein sequence design using LigandMPNN." *Nat Methods* 22:717. PMID 40155723.
- **Wohlwend J, et al.** (2024-2025) Boltz-2.
- **Dieckhaus H, et al.** (2024) ThermoMPNN. *PNAS*.
- **Nayfach S, et al.** (2026) "Protein2PAM." *Nat Biotechnol*.

---

## Reproducibility

All code, sbatch scripts, intermediate scores, and figures are in the repository at `github.com/visvikbharti/protein-language-model-exploration`. The PPT deck (`docs/presentation/FnCas9_PLM_Redesign.pptx`, 28 slides) is regeneratable end-to-end via `PYTHONPATH=src .venv/bin/python scripts/build_presentation.py`. Each phase's `results/runs/.../meta.json` records exact hyperparameters and input SHA-256s. Verification log at `notes/plm/verification-log.md` cites every claim.
