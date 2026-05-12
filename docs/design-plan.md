# Design plan — PLM-guided redesign of FnCas9 toward enFnCas9-class performance

**Project:** `protein-language-model-exploration`
**Last updated:** 2026-05-12
**Authoritative source notes:** `notes/plm/enFnCas9-overview.md`, `notes/plm/plm-nuclease-engineering.md`, `notes/plm/verification-log.md`
**Tools inventory:** `docs/tools-inventory.md`

---

## 0. Why we are doing this

The enFnCas9 paper (Acharya et al., *Nat Commun* 2024) shows that **three carefully chosen mutations** (G1243T / E1369R / E1449H, en31) restore FnCas9's mammalian-cell activity and relax PAM, while retaining the ~1,300× off-target advantage over SpCas9 (`notes/plm/enFnCas9-overview.md`). The design was rational and structure-guided — no PLM was used.

**No published paper applies PLMs to FnCas9 engineering** (`notes/plm/plm-nuclease-engineering.md`, verified). PLM-designed nucleases that *are* published — OpenCRISPR-1 (Profluent, *Nature* 2025) and NmeN4G.1 (Profluent, *Nat Biotechnol* 2026) — target SpCas9 / Nme1Cas9, not FnCas9. The Profluent recipe (sequence-only ProGen2 fine-tune; supervised PAM oracle + in-silico evolution) is publicly reproducible.

Our project therefore has a clear question: **can PLM-guided design produce an FnCas9 variant matching or exceeding en31 on at least one axis (activity, PAM scope, or specificity), at lower cost than rational design?**

## 1. Success criterion (single sentence)

**By end of campaign**, we have ≤ 96 ranked FnCas9 variants for wet-lab testing, each predicted to either (a) match en31's HBB-locus cleavage rate while broadening PAM beyond NRG/NGR, OR (b) match en31's PAM scope while exceeding en31's K_d for the canonical VEGFA3 substrate by ≥ 1.5×. Predictions must come with quantified confidence (LigandMPNN log-likelihood + ESM-2 score + Boltz pLDDT) and a falsification plan (the assay that would refute the prediction).

Anything else (de-novo Cas9, smaller-than-FnCas9 scaffold, etc.) is **out of scope** for this campaign. Defer to follow-up.

## 2. Scope — explicit constraints

- **In scope:** Point and small-combination (≤ 5) mutations in the **WED–PI domain plus phosphate-lock loop** of FnCas9. The same region engineered in en1/en15/en31. Spencer & Zhang 2017 DMS confirms this region is mutation-tolerant in SpCas9 (homology prior).
- **Out of scope:** RuvC and HNH catalytic residues (D11, H979 in FnCas9 — verify exact numbers from PDB 5B2O before any design step). Off-limits unless we deliberately make a nickase.
- **Out of scope:** AAV-compatible truncation (this is a different, harder project).
- **Out of scope:** Wet-lab execution. We end at "ranked list of variants + falsification plan."

## 3. Milestone map

```
M0 ── Target definition  ────────► M1 ── Baseline characterization
                                     │
                                     ▼
                                   M2 ── Variant pool generation (3 parallel methods)
                                     │
                                     ▼
                                   M3 ── Single-mutant scoring & filter
                                     │
                                     ▼
                                   M4 ── Multi-mutant combination & epistasis check
                                     │
                                     ▼
                                   M5 ── Complex-structure validation
                                     │
                                     ▼
                                   M6 ── Final ranked list + wet-lab handoff doc
```

Each milestone has: **inputs · procedure · outputs · verification gate · decision rule**.

---

## 4. Milestones

### M0 — Target definition

**Inputs:**
- `notes/plm/enFnCas9-overview.md` (en31 baseline numbers)
- Design constraints from §1, §2

**Procedure:**
1. Decide single dominant design axis: **activity**, **PAM scope**, or **specificity**.
2. Write the assay that would falsify the prediction. Without an assay, do not start.
3. Define the **reference variant** for comparison (we use en31 as the public-state-of-the-art baseline).
4. Write `docs/design-objective.md` (1 page) capturing the above.

**Outputs:**
- `docs/design-objective.md`

**Verification gate:**
- Can a third party read the objective and reproduce the assay protocol? If no, refine.
- Is the assay measurement meaningful given expected experimental noise? (Aim for predicted effect ≥ 2× the technical CV.)

**Decision rule to proceed:** objective doc written + reviewed.

---

### M1 — Baseline characterization

**Inputs:**
- WT FnCas9 sequence (UniProt A0Q5Y3)
- PDB 5B2O (WT + sgRNA + DNA, TGG PAM, 1.7 Å)
- en31 sequence (G1243T / E1369R / E1449H applied to WT)

**Procedure:**
1. Download WT FASTA + PDB 5B2O.
2. Predict WT FnCas9-sgRNA-DNA complex with **Boltz-2**. Validate against PDB 5B2O.
3. Predict en31 complex (using `apply_mutant` on WT sequence) with Boltz-2.
4. Run **ESM-2** zero-shot scoring (mask-marginal LLR) on WT and en31; record the per-residue score deltas at the three en31 positions.
5. Run **LigandMPNN** scoring on PDB 5B2O fixing all residues except the three en31 positions; record the predicted residue probabilities at those positions. Expected: G1243T, E1369R, E1449H all in the top-5 sampled identities if LigandMPNN is well-calibrated.
6. Record all results to `results/runs/2026-05-XX_baseline/` with a `meta.json`.

**Outputs:**
- `results/runs/<date>_baseline/complex_wt.cif`
- `results/runs/<date>_baseline/complex_en31.cif`
- `results/runs/<date>_baseline/esm2_scores.parquet`
- `results/runs/<date>_baseline/mpnn_scores.parquet`
- `results/runs/<date>_baseline/baseline_report.md` (numerical comparison + verdict)

**Verification gate (CRITICAL):**
- **Boltz-2 predicted WT complex must align to PDB 5B2O with backbone RMSD ≤ 3 Å** at residues 1100–1629 (WED+PI region). If not, **stop the pipeline** — Boltz-2 isn't reliable for our system and we need to either use AF3 server or limit to sequence-only methods.
- **LigandMPNN must rank the en31 mutations within top-10 sampled identities at each site** when fixing the rest. If not, LigandMPNN isn't calibrated for our context — flag and consider sequence-only fallback.
- **ESM-2 LLR for en31 mutations should be ≥ 0** (favored over WT). If strongly negative, ESM-2 has the wrong evolutionary signal for engineered Cas9 — flag and downweight ESM-2 in the ensemble.

**Decision rule to proceed:** Boltz RMSD gate passes; at least one of LigandMPNN or ESM-2 endorses en31 mutations. If both fail, document this as a finding (PLMs disagree with rational design) and consult before proceeding.

---

### M2 — Variant pool generation (three parallel methods)

**Inputs:**
- WT FnCas9 sequence + PDB 5B2O
- Predicted WT and en31 complex structures (from M1)
- Decision from M0 (which axis to tune)

**Procedure — three parallel sources, all targeting WED–PI + PLL:**

**M2.1 — LigandMPNN sampling**
- On the predicted FnCas9-sgRNA-DNA complex from M1, mask residues in WED (~1230–1300) and PI (~1340–1610), fix everything else.
- Sample 5,000 sequences with LigandMPNN. Temperature 0.1, 0.2, 0.3 (three sweeps).
- Decompose sampled sequences into per-position mutation lists; rank by per-position frequency.

**M2.2 — ESM-2 zero-shot saturation**
- Saturation mutagenesis grid over the same WED–PI + PLL residue set (~400 positions × 19 substitutions = ~7,600 single mutants).
- Score each with ESM-2 mask-marginal LLR.
- Top 1,000 by LLR retained.

**M2.3 — Protein2PAM-guided in-silico evolution** (if axis is "PAM scope")
- Use Profluent's PAM oracle to evolve toward a target PAM PWM (e.g., 5'-NNG-3' or 5'-NN-3' for PAM-less).
- 50 generations, population 256, mutation rate 1–3 substitutions per generation.
- Final population: 256 candidate sequences with predicted target PAM.

**Outputs:**
- `results/runs/<date>_pool/ligandmpnn_samples.parquet` (5,000 × 3 temps)
- `results/runs/<date>_pool/esm2_saturation.parquet` (~7,600 rows)
- `results/runs/<date>_pool/protein2pam_evolution.parquet` (if applicable)

**Verification gate:**
- LigandMPNN top sampled identities at the three en31 positions agree with en31 (cross-validation).
- ESM-2 saturation includes all three en31 mutations within the top 5% of WED-PI mutations.
- Protein2PAM final population's predicted PAM PWM has KL-divergence < 0.5 from target PWM.

**Decision rule:** at least 2 of 3 sources produce a pool. Drop sources that fail the gate; document why.

---

### M3 — Single-mutant scoring & filter

**Inputs:**
- Union of mutants from M2 (deduplicated single substitutions)

**Procedure:**
1. Score every unique single mutant with:
   - LigandMPNN log-likelihood (recompute on each, not just on M2.1's sampling)
   - ESM-2 mask-marginal LLR (from M2.2 if available; otherwise recompute)
   - **proteinmpnn_ddg** for predicted ΔΔG (stability filter)
   - Solvent accessibility from PDB 5B2O (filter out buried-residue charge reversals)
2. Compute a composite rank: `rank = mean_rank(LigandMPNN, ESM-2) + 0.5 * rank(−ΔΔG)`. Lower = better.
3. Filter:
   - ΔΔG > +3 kcal/mol → drop (destabilising)
   - solvent_acc < 20% AND charge_reversal → drop
   - LigandMPNN LL < threshold (defined as the 5th percentile of WT-position likelihoods) → drop

**Outputs:**
- `results/runs/<date>_filter/single_mutants_ranked.parquet`
- `results/runs/<date>_filter/filter_report.md`

**Verification gate:**
- After filtering, **all three en31 mutations should survive** (they are known to be functional). If any are filtered out, the filter is too strict — relax.
- Filtered list size should be 100–500. If < 100, too strict; if > 1000, too loose.

**Decision rule:** filtered list size in target range AND en31 mutations retained.

---

### M4 — Multi-mutant combination & epistasis check

**Inputs:**
- Top 100 single mutants from M3
- Predicted en31 complex (M1)

**Procedure:**
1. Combinatorial expansion: top 20 × top 20 doubles + top 10 × top 10 × top 10 triples = ~250 doubles + 1000 triples.
2. Re-score each combination with LigandMPNN (joint sampling, fixing only the combination positions as varied).
3. Re-score each with ESM-2 (apply both mutations, score the resulting sequence's likelihood).
4. **Epistasis flag:** if combined score < (sum of single-mutant scores − margin), flag as antagonistic; if > sum, flag as synergistic.
5. Predict ΔΔG for each combination with proteinmpnn_ddg.

**Outputs:**
- `results/runs/<date>_combine/combinations_ranked.parquet`
- `results/runs/<date>_combine/epistasis_report.md`

**Verification gate:**
- en31 itself (G1243T + E1369R + E1449H) is included as a positive control. Its composite score should rank in the **top 10%** of all evaluated triples.
- Predicted ΔΔG of en31 should be modestly positive (≤ +3 kcal/mol) — known to be experimentally stable.

**Decision rule:** en31 ranks well; epistasis pattern is interpretable.

---

### M5 — Complex-structure validation

**Inputs:**
- Top 50 combinations from M4

**Procedure:**
1. Predict the full FnCas9-sgRNA-DNA complex with **Boltz-2** for each top-50 combination.
2. Cross-validate ~10 with **Chai-1** (independent predictor).
3. Score each prediction:
   - pLDDT averaged over the variant residues
   - ipTM for the Cas9-DNA interface
   - All-atom RMSD vs. predicted en31 complex
4. Filter combinations with pLDDT < 0.7 at variant sites or ipTM < 0.6.

**Outputs:**
- `results/runs/<date>_structure/predicted_complexes/*.cif`
- `results/runs/<date>_structure/structure_scores.parquet`

**Verification gate:**
- For at least 5 variants, Boltz-2 and Chai-1 should agree on pLDDT within 0.1 (sanity check on structure-prediction reliability for FnCas9).
- The en31 control should pass all filters.

**Decision rule:** ≥ 20 variants survive all filters.

---

### M6 — Final ranked list + wet-lab handoff

**Inputs:**
- Final 20–96 variants from M5

**Procedure:**
1. Compose final ranking with weights:
   - 40% LigandMPNN composite
   - 30% ESM-2 LLR
   - 20% Boltz/Chai pLDDT+ipTM
   - 10% ΔΔG (inverted)
2. Sanity check: en31 should be in the top quartile of the final ranking (positive control); a randomly selected near-WT triple should be near the bottom (negative control).
3. Write **`docs/wet-lab-handoff.md`** containing:
   - Final variant list with sequences (FASTA) and one-line rationale
   - The assay protocol from M0
   - Predicted effect size + confidence per variant
   - Expected false-positive rate from cross-validation

**Outputs:**
- `results/runs/<date>_final/ranked_variants.fasta`
- `results/runs/<date>_final/ranked_variants.tsv`
- `docs/wet-lab-handoff.md`

**Verification gate:**
- en31 control in top 25% of final ranking
- Random near-WT control in bottom 25%
- Variant list has 20–96 entries

**Decision rule:** project complete; hand to wet-lab.

---

## 5. Risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Boltz-2 / Chai-1 predict the FnCas9 complex poorly (no Cas9-DNA benchmark exists) | Medium | High — would invalidate M1 gate | Mandatory M1 RMSD gate vs. PDB 5B2O; fallback to sequence-only methods |
| LigandMPNN is not calibrated for FnCas9 — long protein, unusual sgRNA scaffold | Medium | High | M1 cross-validation step; downweight if calibration fails |
| ESM-2 zero-shot is misleading for engineered Cas9 (model trained on natural distribution) | Medium | Medium | Cross-check via LigandMPNN; don't rely on ESM-2 alone |
| PLM scores disagree with each other on most variants | High | Medium | This *is* the signal — pick variants with consensus, treat disagreement variants as exploratory |
| Compute budget exceeds what's available | Medium | High | Sizing in §6; lazy execution per milestone |
| en31 fails M3/M4 gates (positive control fails) | Low | Very high | Treat as a project-stopping result; revisit method choices, do not proceed |
| Designed variants are all close to en31 (no novelty) | Medium | Medium | Acceptable result — at minimum we'd have reproduced enFnCas9; flag in handoff |
| HDR knock-in % at DCX for en31 was never extracted from primary source | Confirmed gap | Low | Find supplementary tables OR run our own comparison via assay design in M0 |

## 6. Compute budget estimate

| Stage | Tool | Approx. wall time | Hardware |
|---|---|---|---|
| M1 baseline | Boltz-2 single complex | ~30–60 min | 1× H100 / A100 80GB |
| M1 ESM-2 scoring on WT | ESM-2 650M, ~1629 aa | ~2 min | any GPU |
| M2.1 LigandMPNN | 5000 samples × 3 temps × ~1629 aa | ~3–6 hr | 1× A100 |
| M2.2 ESM-2 saturation | 7600 single mutants on full sequence | ~4 hr | 1× A100 |
| M2.3 Protein2PAM evolution | 50 gen × 256 pop | ~2 hr | 1× A100 |
| M3 single-mutant rescoring + ΔΔG | ProteinMPNN ddg + filters | ~2 hr | 1× GPU |
| M4 combinations | ~1250 combos × 4 scorers | ~4 hr | 1× A100 |
| M5 structure validation | 50 Boltz + 10 Chai complexes | ~30 hr | 1× H100 |
| **Total** | | **~50 hr GPU** | 1× H100 + storage |

User-side prerequisites: GPU access (cloud or institutional), Hugging Face account for ESM-3 gated weights, ~50 GB local storage for weights + intermediate artefacts.

## 7. Reproducibility checklist

Every run directory must contain a `meta.json` with:
- ISO date + UTC time
- Tool versions (`pip freeze` snapshot)
- Git SHA of this project at run time
- Random seed
- Input file hashes (SHA-256)
- GPU model + driver version

See `docs/methods.md` (to be written) for the exact format.

## 8. What we won't do unless asked

- Wet-lab execution
- Constructs / cloning / DNA synthesis ordering
- AAV-compatible truncation (separate project)
- Antibody design against the variants
- Off-target sequencing analysis (we'll only predict)

## 9. Open questions for the project lead

1. **Which design axis** in M0 — activity, PAM, or specificity? Default: PAM scope, since it's the most computationally tractable and Profluent's NmeN4G.1 recipe is directly applicable.
2. **Which canonical locus** for in-cell editing predictions? Default: HBB g21 (matches Acharya 2024 enFnCas9 number).
3. **What's the wet-lab cap** (number of variants)? Default: 96 (one 96-well plate).
4. **Use Protein2PAM** despite non-commercial license? Default: yes for academic; flag for any commercial follow-up.
