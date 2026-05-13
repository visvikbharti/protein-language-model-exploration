# Design plan — Phase 2 (post-PLM1)

**Date:** 2026-05-13
**Predecessor:** `docs/design-plan.md` (the M0–M6 master plan), `results/runs/2026-05-13_final/design-report.md` (the Phase 1 / PLM1 result + its M1-gate failure).

## Why Phase 2 exists

The Phase 1 PLM1 candidate (`H1236L/R1367L/W1459K/Q1596N` from ESM-2 35M) **failed the M1 verification gate** explicitly defined in `design-plan.md` §M1. Specifically:

- All four published enFnCas9 mutations (G1243T, E1369R, E1449H, E1603H) ranked **12–16 of 19** at their respective positions under ESM-2 35M, with negative LLR.
- Cross-ortholog mapping (`results/runs/2026-05-13_cross_ortholog/site_mapping.tsv`) shows the PLM1 picks include residues conserved across Cas9 orthologs (R1367 = R/K in SpCas9 + SaCas9; W1459 = W in Nme1Cas9), which the model could not see from sequence alone.

The Phase 1 finding is itself scientifically valuable — it documents that small zero-shot PLMs are biased by per-residue rare-AA frequency. But it is not a credible nuclease-design output. Phase 2 must address the failure modes before any downstream commitment.

## The three pre-registered hypotheses Phase 2 will test

| H# | Statement | Falsification criterion |
|----|---|---|
| **H1** | Model scale fixes the rare-AA bias: ESM-2 **650M** mask-marginal LLR ranks all four en31/en15 reference mutations in the top 6 of 19 at their positions. | If 650M still ranks any reference mutation outside the top 10, scale alone is insufficient — escalate to ESM-3 or structure-conditioned scoring. |
| **H2** | A Cas9-family conservation filter (Shannon entropy across an MSA of FnCas9 + SpCas9 + SaCas9 + Nme1Cas9 + CjCas9) downweights or rejects the PLM1-style picks at conserved positions while leaving en31's choices intact. | If en31's mutations are also filtered out (i.e., they too sit at fully conserved columns), our conservation criterion is wrong — we need a more nuanced filter. |
| **H3** | A composite score `LLR_650M − λ · conservation` (λ to be calibrated) ranks en31 in the **top quartile** of all single-mutant candidates in the four hotspot windows. | If en31 still does not crack top 25 %, the ESM-2 family is fundamentally unsuitable for FnCas9 zero-shot scoring and we must commit to LigandMPNN as Phase 3. |

## Cross-validation protocol

Three classes of controls scored alongside the design candidates. Conducted under **both** the 35M and 650M models so we can directly compare bias.

### Positive controls (validated functional mutations)
- en1 (E1369R), en15 (E1603H), en31 (G1243T, E1369R, E1449H)
- **Expectation:** mean LLR > 0; at least one of the three en31 mutations in the top decile at its position.

### Negative controls (predicted-disruptive mutations)
- **Charge reversal at buried PI-domain hydrophobic core:** L1407R, V1400D (chosen because they are conserved hydrophobic and structurally buried — verifiable later from 5B2O SASA < 20 %).
- **Loss-of-aromatic at conserved nucleic-acid contact:** Y1431A (Y1431 sits near the protein-DNA face in PI in 5B2O — to be verified per the structure analysis).
- **Expectation:** mean LLR strongly negative; all controls in bottom decile.

If we can confirm catalytic-residue identities for FnCas9 (RuvC and HNH active sites; needs cross-reference to Hirano 2016), additional negative controls:
- HNH catalytic residue → A (e.g., H979A if confirmed)
- RuvC catalytic residue → A (e.g., D11A or D831A — Hirano 2016 lists D11/E479/D830 as the RuvC-active triad in FnCas9; **verify before using**)

### Neutral controls (conservative mutations at non-conserved surface positions)
- Identified from the conservation analysis: any position where conservation ≤ 0.4 across the 5 orthologs and where FnCas9 SASA > 70 Å² in 5B2O.
- Conservative substitution (S→T, V→I, K→R) at three such positions.
- **Expectation:** mean LLR near zero (±0.5).

## Checkpoints (with explicit gates)

| CP | Gate | Pass condition | If failed |
|---|---|---|---|
| **CP-1** | ESM-2 650M scan completes | All 1596 variants scored, scores written, en31 mutations recorded | Investigate model-loading or scoring bug; do not proceed |
| **CP-2** | Cross-validation separates pos vs neg controls under 650M | Positive controls mean LLR > negative controls mean LLR by ≥ 1 standard deviation | Phase 3 (LigandMPNN). Phase 2 cannot continue with this model. |
| **CP-3** | Conservation scorer produces sensible per-position entropy | Hotspot residues E1369 and W1459 have **different** conservation scores (E1369 more conserved than W1459 is the prediction from cross-ortholog data) | Inspect MSA construction; conservation scorer is wrong |
| **CP-4** | Composite score retrospectively recovers en31 | At least one en31 mutation in top-5 at its position under composite score | Tune λ; if no λ in [0.5, 5] works, the conservation+LLR combination is insufficient |
| **CP-5** | FnCas9-PLM2 mutations avoid family-conserved positions | All PLM2 mutation sites have conservation < 0.7 | Re-pick from below-conservation-threshold candidates |
| **CP-6** | Phase 2 homology analysis confirms PLM2 differs from PLM1 in expected ways | PLM2 selects ≥ 2 mutations at positions distinct from PLM1's four; at least one of the four en31 positions is hit | Reconsider the design space; the windows might be too narrow |

## Methods refinements over Phase 1

1. **Model:** ESM-2 650M (esm2_t33_650M_UR50D). Memory ~3 GB on CPU. Forward pass ~10–20 s per 1629-aa sequence. 84 positions ≈ 20–30 min CPU. **Cross-checked against ESM-2 35M to quantify the model-scale effect.**
2. **Conservation scorer:** column-wise Shannon entropy on the 5-sequence Cas9 family MSA built from pairwise alignments to FnCas9 reference. Normalised to [0, 1].
3. **Composite score:** `s_composite(V) = LLR_650M(V) − λ · conservation(pos(V))` with **λ calibrated retrospectively** so that en31's E1369R appears in the top-5 at position 1369 under the composite. If multiple λ produce the same retrospective rank, prefer the smaller (more conservative) λ. λ is recorded in the run meta.
4. **Selection rule:** for each hotspot window, choose the top-1 substitution under the composite score subject to:
   - WT residue is not catalytic (excluding HNH/RuvC active sites)
   - Conservation at the position is < 0.7
   - LLR_650M ≥ 0 (strictly preferred over WT)
5. **Multi-mutant combination:** sum of composite scores under the independence approximation (documented as in Phase 1).
6. **Cross-validation report:** every Phase 2 result is reported with the matched 35M score, the 650M score, the conservation score, and the composite score so the reader can audit any decision.

## Falsification plan

If Phase 2 produces a PLM2 candidate that **does not** retrospectively rank en31 in the top quartile, we will:
1. Document the failure publicly in the report (Phase 1 + Phase 2 negative result).
2. Escalate to Phase 3 = LigandMPNN with structure conditioning (requires GPU, deferred to the next session that has compute).
3. Pause any wet-lab consideration.

If Phase 2 produces a candidate that *does* recover en31 retrospectively, we declare Phase 2 a success and:
1. Run the candidate through the full homology pipeline (Phase 1 analyses re-executed).
2. Recommend a 96-variant wet-lab plate with FnCas9-PLM2 as one candidate alongside en31 (positive control) and HNH-dead variant (negative).

## Out of scope (still)

- GPU-required tools (LigandMPNN, RFdiffusion, Boltz, Chai-1, ESM-3, AlphaFold)
- Wet-lab
- Off-target prediction
- Larger MSA (would require MMseqs2 or HHblits against UniRef, which is doable but multi-GB and slow)
- 3D structural superposition across Cas9 PDBs (would require TM-align or similar)

These remain on the Phase 3 list.
