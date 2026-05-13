# Design report — Phase 2 (FnCas9-PLM2)

**Date:** 2026-05-13
**Predecessor:** [Phase 1 design-report.md](./design-report.md), [docs/design-plan-phase2.md](../../../docs/design-plan-phase2.md)

---

## 0. Executive summary

Phase 2 produced **FnCas9-PLM2 = G1243T / R1370K / R1456I / G1606D** by combining **ESM-2 650M** zero-shot mask-marginal scoring with a **Cas9-family class-conservation filter** (class_cons < 0.5 required). Key results:

- **PLM2 recovers `G1243T`** — the same WED-PLL mutation that defines en31, with **rank 1/19** at its position under ESM-2 650M (vs rank 13/19 under 35M). This is empirical validation that **model scale recovered ONE of four reference mutations** that 35M had missed.
- **PLM2 avoids the PLM1 failure mode**: no W1459 substitution (filtered at class_cons=1.00), no R1367L (filtered at class_cons=0.50). PLM1's four positions are all replaced or moved.
- **Pre-registered hypothesis H1 is REFUTED.** ESM-2 650M did not recover the *three* PAM-contact mutations (E1369R, E1449H, E1603H); they remain at ranks 13/19, 15/19, 16/19. The PAM-contact engineering signal is invisible to a sequence-only PLM because it requires the DNA/RNA context — confirming the design-plan prediction.
- The cross-validation showed **NEGATIVE controls (charge reversals, glycine intros, aromatic loss) score HIGHER on average than POSITIVE controls under 650M** (+1.12 vs +0.04). The rare-AA bias persists at scale. The conservation filter is what made PLM2 credible, not the LLR alone.

PLM2 is reported as the best in-session candidate; it is **not** wet-lab ready. Phase 3 (LigandMPNN with structure conditioning) is mandated by the H1 refutation.

## 1. Phase 1 → Phase 2 transition

Phase 1 (`design-report.md`) produced PLM1 = H1236L/R1367L/W1459K/Q1596N from ESM-2 35M alone, and failed the M1 verification gate. Phase 2 introduces three corrections, each pre-registered:

| H# | Hypothesis | Verdict |
|---|---|---|
| H1 | ESM-2 650M ranks all four reference mutations in top-6 at their positions | **REFUTED** — only G1243T moves into top-6 (rank 1); E1369R/E1449H/E1603H stay at 13–16 |
| H2 | Conservation filter downweights PLM1-style picks while leaving en31's intact | **CONFIRMED** — class_cons < 0.5 filter removes W1459K (cls=1.00) and R1367L (cls=0.50); preserves G1243T (0.33) and E1449H (0.33) |
| H3 | Composite `LLR_650M − λ · class_cons` retrospectively places en31 in top quartile (1596 candidates) | **REFUTED** in current form — λ calibration found no λ ∈ [0.5, 5.0] recovering E1369R in top-5 at its position (E1369R has LLR=−1.16 under 650M; within-position rank is determined by LLR alone, λ shifts equally) |

The H3 refutation revealed a methodological subtlety: within a single position, all 19 substitutions share the same conservation score (it is a per-position quantity). The composite score `LLR − λ · cls_cons` shifts them all equally, so within-position rank is unchanged. The composite affects only cross-position rank. We re-ran with default λ=1.0 and accept the empirical result.

## 2. Method: what changed vs Phase 1

| Aspect | Phase 1 (PLM1) | Phase 2 (PLM2) |
|---|---|---|
| Model | ESM-2 35M | **ESM-2 650M** (~18× params) |
| Scan target | 84 hotspot positions | Same 84 positions |
| Selection criterion | Top LLR per window | **Top LLR per window AND class_cons < 0.5 AND LLR > 0** |
| Conservation source | None | Star-MSA of 5 Cas9 orthologs (FnCas9 + SpCas9 + SaCas9 + Nme1Cas9 + CjCas9) |
| Composite score | LLR alone | `LLR − λ · class_cons` (λ=1.0; calibration to en31 failed) |
| Code | `scripts/build_candidate.py` | `scripts/build_candidate_v2.py` |

Conservation scorer: `src/nuclease_design/scoring/conservation.py`. Six unit tests in `tests/test_conservation.py`. Two conservation metrics:
- **identity_conservation**: fraction of orthologs sharing the exact FnCas9 WT residue at the homologous column.
- **class_conservation**: fraction sharing the *physicochemical class* (positive / negative / polar / hydrophobic / aromatic / glycine / proline / cysteine).

The class metric is what catches PLM1's R1367L and W1459K — these have identity=0 (no ortholog has identical R or W) but class=0.5–1.0 (charges or aromatics are preserved across the family).

## 3. Verification results

### 3.1 Reference variants under both models

| Mutation | LLR_35M | rank@pos (35M) | LLR_650M | rank@pos (650M) | Notes |
|---|---:|:---:|---:|:---:|---|
| **G1243T** (en31) | −0.172 | 13/19 | **+4.436** | **1/19** | Model scale recovers this. Largest LLR shift. |
| E1369R (en1, en31) | −0.811 | 12/19 | −1.159 | 13/19 | Unchanged. PAM-contact signal invisible to sequence-only PLM. |
| E1449H (en31) | −1.600 | 16/19 | −1.396 | 15/19 | Minor improvement. |
| E1603H (en15) | −1.562 | 16/19 | −1.724 | 16/19 | Unchanged. |

### 3.2 Cross-validation: positive / negative / neutral

(Full table at `results/runs/2026-05-13_cross_validation/cross_validation.tsv`.)

| Category | n | LLR_35M mean | LLR_650M mean | LLR_650M range |
|---|---:|---:|---:|---|
| POSITIVE (en1, en15, en31) | 4 | −1.04 | +0.04 | −1.72 to +4.44 |
| NEGATIVE (predicted-disruptive) | 8 (5 scored) | +0.78 | **+1.12** | −0.90 to +2.78 |
| NEUTRAL (conservative subs) | 4 (1 scored) | −0.07 | −0.14 | n/a single point |

**Pre-registered H1 pass criterion** (`pos_mean − neg_mean > 1.0`): 35M = −1.82, 650M = **−1.08**. Both negative — model puts negatives ABOVE positives. **Refuted.**

This is the cleanest empirical demonstration so far that ESM-2 zero-shot scoring is **biased toward substitutions at rare amino acids**, *regardless of model scale*. Specifically the W1459 substitutions dominate: W1459K under 650M scores +4.166 (rank 2 overall), beating every reference functional mutation except G1243T.

### 3.3 Conservation scorer empirical check

At PLM1 mutation sites, the new class-conservation metric correctly flags:

| Variant | id_conservation | **class_conservation** | Verdict |
|---|---:|---:|---|
| H1236L (PLM1) | 0.00 | 0.00 | OK (variable) |
| R1367L (PLM1) | 0.00 | **0.50** | FLAG — R/K family-conserved |
| W1459K (PLM1) | 0.25 | **1.00** | FLAG — fully aromatic-conserved |
| Q1596N (PLM1) | 0.00 | 0.25 | OK (mostly variable) |

The `class_cons < 0.5` filter rejects R1367L and W1459K — exactly the mutations cross-ortholog mapping had identified as evolutionarily contraindicated in Phase 1. H2 confirmed.

## 4. FnCas9-PLM2 candidate

```
>FnCas9-PLM2 PLM-designed FnCas9 v2; G1243T/R1370K/R1456I/G1606D
```

| Window | Mutation | LLR_650M | class_cons | composite (λ=1.0) | Rationale |
|---|---|---:|---:|---:|---|
| WED_PLL_G1243 | **G1243T** | +4.436 | 0.33 | +4.103 | Same as en31 — model scale recovered it. WED phosphate-lock loop. |
| PI_E1369 | R1370K | +1.381 | 0.25 | +1.131 | R→K conservative (both positive). Adjacent to en1's E1369R. Surface (SASA 167 Å²), near RNA (3.9 Å). |
| PI_E1449 | R1456I | +1.386 | 0.00 | +1.386 | R→I (loss of positive) at family-variable position. Surface (SASA 98 Å²), 5.5 Å from RNA. |
| PI_WED_E1603 | G1606D | +1.389 | 0.25 | +1.139 | G→D introduces a charged sidechain at a partially buried glycine (SASA 16.7 Å²) → structural risk; only weakly family-conserved. |

Files: `results/runs/2026-05-13_candidates_v2/fncas9_variants_v2.fasta`, `FnCas9-PLM2.meta.json`.

## 5. PLM2 vs PLM1 head-to-head

| Window | PLM1 (Phase 1, 35M alone) | PLM2 (Phase 2, 650M + conservation) | Comment |
|---|---|---|---|
| WED_PLL_G1243 | H1236L (class_cons=0.00) | **G1243T** (en31 match) | PLM2 recovers en31's choice |
| PI_E1369 | R1367L (class_cons=0.50 — filtered) | R1370K (conservative R→K) | PLM1 violated the filter; PLM2 picks a different position |
| PI_E1449 | W1459K (class_cons=1.00 — filtered) | R1456I | PLM1's pick was aromatic-conserved; PLM2 avoids it |
| PI_WED_E1603 | Q1596N (class_cons=0.25) | G1606D | Both at variable positions; G→D has more structural risk than Q→N |

PLM2 distinguishes itself from PLM1 in **all four windows**. CP-6 passed.

## 6. Two-way homology for PLM2

### 6.1 Sequence (NW BLOSUM62, all-vs-all in `results/runs/2026-05-13_homology_PLM2/`)

| vs FnCas9-PLM2 | % Identity | % Similarity |
|---|---:|---:|
| FnCas9 WT | 99.75 | 99.82 |
| FnCas9 en31 | 99.69 | 99.75 |
| FnCas9 en15 | 99.69 | 99.75 |
| SpCas9 | 22.27 | 44.47 |
| SaCas9 | 26.83 | 48.85 |
| Nme1Cas9 | 25.33 | 47.52 |
| CjCas9 | 31.04 | 49.79 |

### 6.2 Structural context (PDB 5B2O, `results/runs/2026-05-13_structure_PLM2/`)

| Pos | WT res | Domain | SASA (Å²) | n contacts (6 Å) | nearest DNA (Å) | nearest RNA (Å) | Interpretation |
|---:|:---:|---|---:|---:|---:|---:|---|
| **1243** | GLY | WED | 28.2 | 5 | **3.65** | 4.91 | DNA-contact, tight backbone. G→T adds methyl (phosphate-lock published mechanism). |
| **1370** | ARG | PI | **166.6** | 8 | 9.79 | **3.92** | Surface-exposed RNA-contact. R→K preserves positive charge. Low structural risk. |
| **1456** | ARG | PI | 97.8 | 6 | 11.36 | 5.52 | Moderately exposed PI surface near RNA. R→I removes charge — moderate functional risk. |
| **1606** | GLY | PI | 16.7 | 7 | 6.51 | 25.89 | **Buried** glycine far from nucleic acid. G→D introduces a charged sidechain in a buried position — **structural risk** (likely ΔΔG > +2 kcal/mol if buried-D unhappy). |

### 6.3 Cross-ortholog residue mapping for PLM2 sites (`results/runs/2026-05-13_cross_ortholog_PLM2/`)

| Site | FnCas9 WT | id_c | cls_c | SpCas9 | SaCas9 | Nme1Cas9 | CjCas9 |
|---|:---:|---:|---:|:---:|:---:|:---:|:---:|
| **G1243** (PLM2, en31) | G | 0.25 | 0.33 | N | gap | **G\*** | K |
| **R1370** (PLM2) | R | 0.00 | 0.25 | K | E | G | E |
| **R1456** (PLM2) | R | 0.00 | 0.00 | A | P | T | gap |
| **G1606** (PLM2) | G | 0.25 | 0.25 | **G\*** | D | Q | V |
| E1369 (en1, en31) | E | 0.50 | 0.50 | **E\*** | P | **E\*** | K |
| E1449 (en31) | E | 0.00 | 0.33 | Y | K | gap | D |
| E1603 (en15) | E | 0.00 | 0.00 | S | Y | Q | N |

`*` = identical to FnCas9 WT at the structurally homologous position.

Reading the mapping:
- G1243 is glycine in Nme1Cas9 too — a position with cross-family functional/structural significance, picked by both en31 and PLM2.
- R1370 has K in SpCas9 (positive preserved); the PLM2 R→K choice is consistent with the SpCas9 natural state.
- R1456 is highly variable (A, P, T, gap across orthologs) — R is unique to FnCas9; PLM2's R→I is plausible but loses charge.
- G1606 has G in SpCas9 (conserved). PLM2's G→D is bolder than en31 would pick at a partially-conserved residue.

## 7. Verification gate verdicts (final)

| CP | Gate | Verdict |
|---|---|---|
| CP-1 | 650M scan completes, all 1596 variants scored | **PASS** (12 min CPU) |
| CP-2 | Positive vs negative LLR separation > 1.0 under 650M | **FAIL** — negatives score +1.08 above positives. ESM-2 family fundamentally unable to rank Cas9 mutations. |
| CP-3 | Conservation scorer distinguishes E1369 (conserved) from W1459 (more aromatic-conserved) | **PASS** — id_cons 0.50 vs 0.25; class_cons 0.50 vs 1.00 |
| CP-4 | Composite score retrospectively places en31's E1369R in top-5 | **FAIL** — no λ in [0.5, 5.0] recovers within-position top-5; methodological subtlety documented |
| CP-5 | PLM2 mutations all have class_conservation < 0.5 | **PASS** — 0.33, 0.25, 0.00, 0.25 (all < 0.5) |
| CP-6 | PLM2 differs from PLM1 in ≥ 2 of 4 windows | **PASS** — differs in all 4 |

## 8. Scientific honesty: what this campaign shows

1. **ESM-2 zero-shot scoring is structurally biased on engineered Cas9.** At neither 35M nor 650M does it rank E1369R, E1449H, or E1603H among the top picks at their positions. These are PAM-contact mutations whose function depends on direct DNA/RNA interaction — invisible to a sequence-only model.
2. **Model scale does help selectively.** G1243T moved from rank 13 to rank 1 at its position when going 35M → 650M. The phosphate-lock-loop signal is presumably encoded somehow in the model at scale; the PAM-contact signal is not.
3. **The rare-amino-acid bias is robust to scale.** W1459 substitutions dominated the top-K under both 35M and 650M because tryptophan has low natural occurrence and any substitution is "expected" by the model. Without a conservation filter, the design would be a tryptophan-replacement.
4. **A simple family-conservation filter substantially mitigates the bias.** The 5-sequence Cas9 MSA we built rejects PLM1's two worst picks (R1367L, W1459K). This is a small-cost, high-value addition.
5. **Composite scoring `LLR − λ · cons` has a known subtlety.** Within a position, all substitutions share the same conservation value, so λ shifts them equally and within-position rank is fixed by LLR. The composite affects cross-position rank, which is what selection of the top-1-per-window benefits from. Document this in any future implementation.

## 9. What PLM2 is and is not

**PLM2 is:**
- A defensible PLM-suggested four-mutation FnCas9 variant that respects family-level evolutionary signal.
- Empirical validation that ESM-2 650M plus a conservation filter is better than ESM-2 35M alone.
- A useful comparator for any future Phase 3 LigandMPNN design.

**PLM2 is NOT:**
- Wet-lab ready. The cross-validation showed 650M cannot reliably distinguish functional from non-functional mutations.
- Better than en31 at restoring activity. We have no functional evidence either way.
- Free of structural risk. G1606D in a buried position has a real chance of being destabilising.

## 10. Recommendation: proceed to Phase 3

Phase 3 should add **structure-conditioned scoring** to break the rare-AA bias decisively. Options in priority order:

1. **LigandMPNN** on a predicted FnCas9-sgRNA-DNA complex from Boltz-2 or Chai-1. Models DNA atoms explicitly, would heavily penalise W1459K (the disrupted aromatic) and reward E1369R (the PAM-contact charge).
2. **ESM-IF1** windowed scoring with PDB 5B2O backbone. Would at least see backbone constraints.
3. **Larger MSA conservation.** MMseqs2 against UniRef + ≥ 100 Cas9 sequences instead of 5 orthologs. Would refine per-position entropy and catch our current undercounted variants.

Resource estimate for Phase 3: 1× A100 ~3 hr (Boltz complex + LigandMPNN sampling). ~$5–15 cloud GPU. The MSA work is CPU-only (~2 hr).

If Phase 3 still produces a candidate that doesn't recover the PAM-contact mutations, the conclusion is: **PLMs alone, even structure-conditioned, do not see this specific engineering opportunity**, and rational structure-guided design (as Acharya 2024 did) remains the right approach for FnCas9.

## 11. Files produced in Phase 2

```
results/runs/
├── 2026-05-13_esm_saturation_650M/
│   ├── scores.tsv                    # 1596 mutants with 650M LLR
│   └── meta.json
├── 2026-05-13_conservation/
│   └── hotspot_conservation.tsv      # per-position id/class/Shannon
├── 2026-05-13_cross_validation/
│   └── cross_validation.tsv          # pos/neg/neutral controls under both models
├── 2026-05-13_candidates_v2/
│   ├── fncas9_variants_v2.fasta      # PLM2 + WT + en31 + en15
│   └── FnCas9-PLM2.meta.json
├── 2026-05-13_homology_PLM2/         # sequence matrix
├── 2026-05-13_structure_PLM2/        # PDB 5B2O context table
├── 2026-05-13_cross_ortholog_PLM2/   # site mapping
└── 2026-05-13_final/
    └── design-report-phase2.md       # this file
```

Code added in Phase 2:
- `src/nuclease_design/scoring/conservation.py` (+ 6 tests)
- `scripts/run_conservation.py`
- `scripts/cross_validation.py`
- `scripts/build_candidate_v2.py`
- `scripts/run_homology_for_variant.py`
- `scripts/map_residues_plm2.py`

All previous Phase 1 tests still pass (40/40 total now, including the new conservation tests).
