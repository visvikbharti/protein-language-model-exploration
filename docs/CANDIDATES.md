# Candidate variants — per-mutation analysis

**Purpose:** detailed dossier on every mutation in PLM3, PLM4, PLM5, and the en31/en15 reference variants. Each mutation gets its biophysical context, position annotation, model scores from every method we've run, and a candid commentary on the most informative or concerning aspects.

**Companion to:** `docs/PROJECT_OVERVIEW.md` (executive summary), `docs/PLM_PRIMER.md` (method theory), `notes/plm/verification-log.md` (raw data + provenance).

---

## 1. Quick reference — all candidates side by side

| Candidate | Mutations | Source method | ESM-2 cumul. composite | LigandMPNN top_freq min | Cumul. apo ΔΔG (kcal/mol) | Boltz iPTM (DNA-PAM) | In en31 envelope? |
|-----------|-----------|---------------|------------------------|--------------------------|---------------------------|---------------------|-------------------|
| **FnCas9-WT** | (none) | — | 0 | — | 0 | 0.939±0.008 | yes (anchor) |
| **FnCas9-en31** | G1243T / E1369R / E1449H | Acharya 2024 directed evolution | (G1243T rank 1, others Q3) | n/a (not sampled) | **+0.40** | **0.942±0.008** | yes (anchor) |
| **FnCas9-en15** | E1603H | Acharya 2024 | (rank 5,109/7,429, Q3) | n/a | **−1.37** | not run | yes (anchor) |
| **FnCas9-PLM3** | G1243T / W1507K / C1292K / M1617K | ESM-2 zero-shot | +13.7 | n/a | **−8.42** | **0.901±0.056** ↓ | "too stable" — outside |
| **FnCas9-PLM4** | T1535V / Y1249F / Y1341L / A1325K | LigandMPNN | n/a | 0.989 | **+6.74** | not run (skipped after gate) | ❌ outside (+6 above en31) |
| **FnCas9-PLM5** | Y1249F / Y1341L / A1325K / K1479F | LigandMPNN + ΔΔG gate | n/a | 0.985 | **+0.59** | **0.933±0.025** ≈ en31 | ✓ essentially at en31 |

The "en31 envelope" is the calibrated-safe band [−1.4, +0.4] kcal/mol cumulative apo ΔΔG that the two known-functional Acharya 2024 variants occupy.

---

## 2. en31 reference dossier (Acharya 2024 directed evolution, *Nat Commun* 2024)

en31 = **G1243T / E1369R / E1449H**. Triple mutant. Wet-lab phenotype: >2-fold cleavage rate vs WT, expanded PAM (NGG → NGG/NGA/NAG), ~1,300× specificity vs SpCas9 (Digenome-seq), ~3.5× expansion of targetable human genome.

### G1243T (WED domain)

| Property | Value |
|----------|-------|
| Position context | WED (Wedge) domain, ~1,230–1,340. Bridges REC lobe to PI lobe. G1243 is on a loop between two helices, surface-exposed |
| WT residue | G (Gly — flexible, often a hinge or tight-turn residue) |
| Mutation | T (Thr — polar, β-branched, can H-bond) |
| ESM-2 LLR (mask-marginal, 650M) | **+4.436** (rank 1 / 7,429 in the broader PI scan) |
| Class conservation (4-ortholog panel) | 0.33 (some flexibility allowed across SpCas9/SaCas9/Nme1Cas9/CjCas9 at this position) |
| LigandMPNN top freq pooled | T = 0.455, S = 0.456 (T is essentially tied with Ser as the modal pick) |
| LigandMPNN target match? | **Yes** — T matches en31 exactly |
| proteinmpnn_ddg apo ΔΔG | **−2.65 kcal/mol** (stabilizing) |
| Biophysical commentary | A flexible Gly → polar β-branched Thr is a moderate substitution. Stabilizing per the apo ΔΔG. Both sequence-only and structure-conditioned models agree this position should change, and both prefer something polar (T or S). Confirms this is a robust prediction across methods. |

### E1369R (PI domain — the PAM-contact mutation)

| Property | Value |
|----------|-------|
| Position context | PI domain, ~1,340–1,620. The PI domain reads the PAM. E1369 is on a helix that sits across the major groove of the PAM-distal duplex |
| WT residue | E (Glu — acidic, negatively charged sidechain) |
| Mutation | R (Arg — basic, positively charged, long sidechain) |
| ESM-2 LLR | rank **4,956 / 7,429** in broader pool (Q3) — model thinks this is **worse** than WT |
| LigandMPNN top freq pooled | K = 0.522, R = 0.365 (Acharya's R is the runner-up; the top is K, also +charge) |
| LigandMPNN WT freq | **0.000** — never sampled. LigandMPNN strongly insists this position must change |
| LigandMPNN target match? | **Partial** — same biophysical class (+charge), different specific amino acid (K vs R). The same biophysical fix |
| proteinmpnn_ddg apo ΔΔG | **+3.20 kcal/mol** ("STRONG destabilizer") |
| Biophysical commentary | This is the canonical PAM-relaxation engineering site. The WT E sidechain is too negative to be close to the negatively-charged DNA backbone phosphates; en1/en31 swap it to R (or our K), creating a favorable contact with PAM-distal phosphates. The apo ΔΔG of +3.20 looks like destabilization, but in the DNA-bound complex it's stabilizing. **en31's functional phenotype with this exact mutation is what calibrates the +3.2 kcal/mol apo ΔΔG ceiling.** |

### E1449H (PI domain)

| Property | Value |
|----------|-------|
| Position context | PI domain, near the loop that reads the PAM-proximal nucleotides |
| WT residue | E (acidic) |
| Mutation | H (histidine — polar, weakly basic at neutral pH, aromatic ring) |
| ESM-2 LLR | rank **5,117 / 7,429** in broader pool (Q3) |
| LigandMPNN top freq pooled | L = 0.985 (strong consensus to change to hydrophobic L) |
| LigandMPNN target match? | **No** — LigandMPNN never samples H here (target freq = 0.000) |
| proteinmpnn_ddg apo ΔΔG | **−0.15 kcal/mol** (neutral) |
| Biophysical commentary | Both in-silico methods disagree with Acharya's choice. LigandMPNN strongly prefers L; ESM-2 prefers WT E. en31's H may be a directed-evolution compromise — possibly tuned for non-structural function (kinetics, off-target rate) that neither model captures. **Falsifiable prediction:** single-point E1449L vs E1449H comparison should be done if wet-lab work proceeds. |

---

## 3. en15 reference dossier

en15 = **E1603H**. Single mutation. Wet-lab phenotype: >2-fold cleavage rate, lower K_d for DNA (49 nM vs WT 170 nM, MST on VEGFA3 target).

### E1603H (PI domain C-terminal)

| Property | Value |
|----------|-------|
| Position context | C-terminal end of PI domain, near the protein's C-terminus |
| WT residue | E (acidic) |
| Mutation | H (histidine) |
| ESM-2 LLR | rank **5,109 / 7,429** (Q3) — model dispreferred |
| LigandMPNN top freq pooled | L = 0.517 (LigandMPNN also prefers L here, not H) |
| LigandMPNN target match? | **No** — H is never sampled (0.000) |
| proteinmpnn_ddg apo ΔΔG | **−1.37 kcal/mol** (stabilizing) |
| Biophysical commentary | Same pattern as E1449H: the experimentally-evolved H is not the model-preferred choice. ESM-2 prefers WT, LigandMPNN prefers L. The wet-lab phenotype (better DNA binding) suggests E1603H may be tuned for binding-affinity rather than fold-stability or contact geometry — a property neither in-silico method directly captures. **Falsifiable prediction:** E1603L could give similar or better K_d than E1603H. |

---

## 4. FnCas9-PLM3 dossier (ESM-2 sequence-only)

PLM3 = **G1243T / W1507K / C1292K / M1617K**. Built by `scripts/build_candidate_v3.py` from the 7,429-variant PI scan.

Cumulative apo ΔΔG: −8.42 kcal/mol — very stable. Three of four picks are X → K, indicating residual rare-amino-acid bias not fully filtered by class-conservation.

### G1243T (shared with en31)

See en31 dossier (Section 2). The fact that ESM-2 ranks this at position 1 / 7,429 in the broader pool is the strongest positive-control hit in this project: a known-functional mutation recovered de novo from a sequence-only zero-shot scan.

### W1507K

| Property | Value |
|----------|-------|
| Position context | PI domain, mid-helix |
| WT residue | W (tryptophan — large aromatic, very hydrophobic, often part of stacking interactions) |
| Mutation | K (lysine — basic, long flexible sidechain) |
| ESM-2 LLR | +3.308 |
| Class conservation | 0.00 (low — orthologs vary at this position) |
| proteinmpnn_ddg apo ΔΔG | **−5.07 kcal/mol** ("STABILIZING") |
| Biophysical commentary | **Suspicious.** Replacing a large aromatic with a charged residue should typically cost stability (loss of hydrophobic surface area and aromatic stacking). The proteinmpnn_ddg call of −5.07 kcal/mol "stabilizing" is either (a) a real but counter-intuitive observation that W1507 is on a solvent-exposed surface where the K is well-solvated and energetically favorable, or (b) a calibration artifact in proteinmpnn_ddg for hydrophobic → K substitutions. Boltz-2 should arbitrate by showing whether the local geometry around 1507 looks intact in the PLM3 prediction. If W1507's aromatic ring is in a contact in the WT model, then the K is a real concern regardless of the apo ΔΔG. |

### C1292K

| Property | Value |
|----------|-------|
| Position context | WED domain |
| WT residue | C (cysteine — small, polar, can form disulfide bonds) |
| Mutation | K (basic) |
| ESM-2 LLR | +3.100 |
| Class conservation | 0.00 |
| proteinmpnn_ddg apo ΔΔG | **−3.63 kcal/mol** (stabilizing) |
| Biophysical commentary | C → K is reasonable if C1292 is a free (non-disulfide-bonded) cysteine — Fn nucleases typically have a few free Cys, often poorly tolerated functionally because they can form spurious oxidation products in vitro. Swapping to K removes that liability and adds a + charge. Cumulatively this looks like a "cleanup" mutation rather than a function-targeted one. |

### M1617K

| Property | Value |
|----------|-------|
| Position context | C-terminal end of PI domain |
| WT residue | M (methionine — hydrophobic, sulfur-containing) |
| Mutation | K (basic) |
| ESM-2 LLR | +3.057 |
| Class conservation | 0.00 |
| proteinmpnn_ddg apo ΔΔG | **+2.93 kcal/mol** (moderate destabilizer — the one mutation in PLM3 that costs apo stability) |
| Biophysical commentary | Met-to-Lys near the C-terminus is a borderline call. If M1617 is solvent-exposed it's fine; if it's part of a hydrophobic cluster anchoring the PI domain C-terminus, this destabilizes that anchor. Boltz-2 + visual inspection of the WT model's M1617 environment would clarify. |

**Overall assessment of PLM3:** the G1243T overlap with en31 is a real win; the three X→K mutations need structural validation (Boltz). The cumulative −8.42 apo ΔΔG is anomalously large — flagged for inspection but not auto-rejected because "too stable" rarely breaks function in nucleases.

---

## 5. FnCas9-PLM4 dossier (LigandMPNN structure+ligand)

PLM4 = **T1535V / Y1249F / Y1341L / A1325K**. Built by `scripts/build_candidate_v4.py` from the LigandMPNN aggregate without a ΔΔG filter.

Cumulative apo ΔΔG: +6.74 kcal/mol — 6.3 kcal/mol outside the en31 envelope. T1535V is the dominant outlier and is what motivated building PLM5.

### T1535V

| Property | Value |
|----------|-------|
| Position context | PI domain |
| WT residue | T (threonine — polar, β-branched, hydroxyl-bearing) |
| Mutation | V (valine — hydrophobic, β-branched, isosteric with T at the Cβ but loses the −OH) |
| LigandMPNN top freq pooled | **1.000** (perfectly confident in the DNA-bound complex) |
| LigandMPNN WT freq | 0.000 |
| Class conservation | 0.00 |
| proteinmpnn_ddg apo ΔΔG | **+4.15 kcal/mol** ("STRONG destabilizer") |
| Biophysical commentary | The most informative single mutation in this whole campaign. LigandMPNN's structure+ligand-conditioned posterior says "in the DNA-bound complex, this should be V"; proteinmpnn_ddg's apo-state ΔΔG says "this destabilizes the apo fold by 4 kcal/mol." The two structure-aware models *agree the position should change* but *disagree on what to change to*, and only because they're conditioning on different reference states. Most likely interpretation: T1535's hydroxyl makes an intramolecular H-bond in the apo fold (proteinmpnn_ddg sees this and flags loss). In the DNA-bound complex, T1535 may make a different contact (perhaps to the DNA backbone or to the sgRNA) that prefers V's smaller hydrophobic sidechain. This is the kind of tension Boltz-2 can resolve — and a high-priority position to inspect once the Boltz predictions land. |

### Y1249F

| Property | Value |
|----------|-------|
| Position context | WED domain |
| WT residue | Y (tyrosine — aromatic, with a hydroxyl) |
| Mutation | F (phenylalanine — aromatic, no hydroxyl) |
| LigandMPNN top freq pooled | 1.000 |
| proteinmpnn_ddg apo ΔΔG | **−0.98 kcal/mol** (stabilizing) |
| Biophysical commentary | Y → F is *the* canonical conservative aromatic substitution: same shape, same π-stacking capacity, only loses the −OH. If Y1249's hydroxyl is making an H-bond, F1249 breaks that bond (and may cost a fraction of a kcal/mol). If the hydroxyl isn't H-bonded, F is essentially silent. proteinmpnn_ddg suggests the −OH wasn't load-bearing here. Low-risk pick. |

### Y1341L

| Property | Value |
|----------|-------|
| Position context | PI domain |
| WT residue | Y (aromatic + hydroxyl) |
| Mutation | L (leucine — hydrophobic, branched, no aromatic ring) |
| LigandMPNN top freq pooled | 0.996 |
| proteinmpnn_ddg apo ΔΔG | +1.78 kcal/mol (moderate destabilizer; within en31 envelope) |
| Biophysical commentary | More aggressive than Y1249F — removes both the aromatic ring and the hydroxyl. If Y1341 was in an aromatic stack, the L replacement is a real perturbation. Worth visual inspection. |

### A1325K

| Property | Value |
|----------|-------|
| Position context | WED-PI hinge region |
| WT residue | A (alanine — small, hydrophobic, no functional group) |
| Mutation | K (basic, long flexible sidechain) |
| LigandMPNN top freq pooled | 0.989 |
| proteinmpnn_ddg apo ΔΔG | +1.79 kcal/mol (moderate destabilizer) |
| Biophysical commentary | A → K is a *large* sidechain swap (gain of ~7 heavy atoms). If A1325 is buried, K1325 can't fit and the apo destabilization is real. If A1325 is on a surface loop, K is fine and may even contact DNA. LigandMPNN's high frequency suggests the latter (it sees the DNA context and likes a basic residue here). |

**Overall assessment of PLM4:** the per-mutation LigandMPNN frequencies are extreme (3/4 at top_freq = 1.000) — likely autoregressive overconfidence (Section 4.4 of `PROJECT_OVERVIEW.md`), not necessarily four genuinely well-determined positions. The +6.74 cumulative apo ΔΔG is real evidence against PLM4 as-is; T1535V (+4.15) is the dominant problem.

---

## 6. FnCas9-PLM5 dossier (LigandMPNN + apo-ΔΔG gate)

PLM5 = **Y1249F / Y1341L / A1325K / K1479F**. Built by `scripts/build_candidate_v4.py --ddg-csv … --max-single-ddg 3.2 --candidate-name FnCas9-PLM5`.

Same three picks as PLM4 (Y1249F, Y1341L, A1325K) plus **K1479F** replacing T1535V. Cumulative apo ΔΔG: +0.59 kcal/mol — essentially at en31's +0.40 anchor.

### K1479F (the new pick that replaces T1535V)

| Property | Value |
|----------|-------|
| Position context | PI domain |
| WT residue | K (basic, long flexible sidechain) |
| Mutation | F (aromatic, large hydrophobic) |
| LigandMPNN top freq pooled | 0.985 |
| LigandMPNN WT freq | 0.000 |
| proteinmpnn_ddg apo ΔΔG | **−2.00 kcal/mol** (stabilizing) |
| Biophysical commentary | K → F removes a positive charge and adds an aromatic. Reverse of the more common "add charge to PI" pattern we've seen — here LigandMPNN actually wants to *remove* a positive charge. Could indicate K1479 is in a position where the + charge is unfavorable (perhaps in a hydrophobic pocket, or pointing into a negative neighbor) and an aromatic packs better. proteinmpnn_ddg agrees this stabilizes the apo fold. Reasonable pick. |

**Overall assessment of PLM5:** the cleanest of our three computed candidates. Cumulative apo ΔΔG at the en31 anchor; each individual mutation is within the en31 envelope. Three of four picks are aromatic-or-hydrophobic substitutions (Y→F, Y→L, K→F) rather than X→K — consistent with LigandMPNN being less biased toward K than ESM-2 was for PLM3. K1479F is the most interesting new pick because it's contrary to the "add + charge in PI" pattern, suggesting LigandMPNN's posterior includes more local context than just "PI domain → wants + charge."

---

## 7. Cross-method consistency table

For every mutation we have computed in this campaign, here is the score from every method:

| Mutation | ESM-2 LLR | LigandMPNN target_freq | LigandMPNN top non-WT | ΔΔG (apo) | In PLM3? | In PLM4? | In PLM5? | In en31/15? |
|----------|-----------|------------------------|------------------------|-----------|----------|----------|----------|-------------|
| G1243T | +4.436 (rank 1/7,429) | 0.455 | T=0.455 (tied with S=0.456) | −2.65 | ✓ | ✗ | ✗ | ✓ (en31) |
| W1507K | +3.308 | n/a (LigandMPNN top is L=0.5) | — | −5.07 | ✓ | ✗ | ✗ | ✗ |
| C1292K | +3.100 | n/a | — | −3.63 | ✓ | ✗ | ✗ | ✗ |
| M1617K | +3.057 | n/a | — | +2.93 | ✓ | ✗ | ✗ | ✗ |
| T1535V | n/a (LigandMPNN-picked) | 1.000 | (V is top) | +4.15 | ✗ | ✓ | ✗ | ✗ |
| Y1249F | n/a | 1.000 | (F is top) | −0.98 | ✗ | ✓ | ✓ | ✗ |
| Y1341L | n/a | 0.996 | (L is top) | +1.78 | ✗ | ✓ | ✓ | ✗ |
| A1325K | n/a | 0.989 | (K is top) | +1.79 | ✗ | ✓ | ✓ | ✗ |
| K1479F | n/a | 0.985 | (F is top) | −2.00 | ✗ | ✗ | ✓ | ✗ |
| E1369R | rank 4,956/7,429 (LLR < 0) | 0.365 | K=0.522 | +3.20 | ✗ | ✗ | ✗ | ✓ (en31) |
| E1449H | rank 5,117/7,429 (LLR < 0) | 0.000 | L=0.985 | −0.15 | ✗ | ✗ | ✗ | ✓ (en31) |
| E1603H | rank 5,109/7,429 (LLR < 0) | 0.000 | L=0.517 | −1.37 | ✗ | ✗ | ✗ | ✓ (en15) |

**Reading the table:**

- **G1243T** is the only mutation that all methods agree on AND is also in en31. This is the single most robust prediction in the campaign.
- **E1369R** is recovered by LigandMPNN (as the runner-up at 36.5% — K wins at 52.2%) but NOT by ESM-2 (Q3 rank). The structure-conditioned model fixes the sequence-only blind spot.
- **E1449H and E1603H** are recovered by neither model. Both prefer L. Either the published H mutations are tuned for non-structural function or both models miss the same structural feature. Falsifiable wet-lab prediction.
- **W1507K's "stabilizing" call** is the largest unexplained model output and a high-priority Boltz target.

---

## 8. Decisions and rationale, audit-trail style

| Decision | Rationale | Alternative considered |
|----------|-----------|------------------------|
| Use en31 as primary calibration anchor | Only published functional FnCas9 variant with full mutation set and direct measurements; from the same wet-lab group whose results we trust most for this protein | en1, en15 also functional but smaller mutation sets; less informative as multi-mutant calibrations |
| Set `--max-single-ddg 3.2` for PLM5 | Equal to en31's worst single-position apo ΔΔG (E1369R = +3.20). Above this we are extrapolating beyond known-functional precedent | More aggressive +5 kcal/mol — would keep T1535V but lose calibration anchoring |
| Filter on class_conservation not identity_conservation | A position can be "diversified" in orthologs at the identity level but conserved at the class level (e.g. always K/R, never D/E). Identity-conservation alone misses this | Identity-only — used in earlier hotspot-window runs, found to admit physicochemically broken picks (W1459K) |
| Choose top-K = 4 candidates | Matches en31's 3-mutation count plus room for one more without diluting the per-mutation confidence | K = 3 (matches en31 exactly) or K = 5/6 (would dilute) |
| Min-spacing = 5 residues | Prevents picks from clustering at one local hotspot; matches the typical α-helix turn period | 0 (allow clustering) or 10 (over-disperse) |
| Use only LigandMPNN's `v_32_010` checkpoint | Default for the ligand-aware pipeline; cited in the original paper | `v_32_005` or `v_32_020/030` — would change the noise level of training |
| Score LigandMPNN samples by *pooled* frequency | Averaging T=0.1, T=0.2, T=0.3 gives a richer per-position posterior than any single temperature | Per-temperature ranking — would inflate disagreement between adjacent temperatures |
| Apo-ΔΔG as soft filter, not hard reject | The model evaluates the wrong reference state (apo, not complex); known-functional variants get +3.2 readings. Hard-rejecting at "destabilizer" would discard en31 itself | Hard reject at ΔΔG > 1.5 — would also reject E1369R, the most important wet-lab-validated mutation |
| Use 5B2O over 5B2P (different PAM) | TGG PAM is canonical; matches en31's wet-lab measurement context | 5B2P (TGA PAM) — would give a different ligand context but is also a valid Cas9-DNA complex |

---

## 9. What we would *not* claim from this data

Important not to overclaim. These are things our in-silico results **do not** support:

1. ❌ "PLM5 has higher cleavage activity than WT." — We have not measured cleavage. Any claim requires wet-lab work.
2. ❌ "T1535V destabilizes the complex." — proteinmpnn_ddg evaluates the apo fold, not the complex. The +4.15 reading is evidence about the apo state only. The complex may be unaffected.
3. ❌ "LigandMPNN is better than ESM-2 for engineering." — The two models have different strengths. LigandMPNN sees the ligand and recovers PAM-contact biophysics; ESM-2 has no structural blind spots and works on sequences with no PDB. Best practice is to use both, as we do.
4. ❌ "en31's E1449H is suboptimal." — Both models prefer L at this position, but our models are missing something (epistasis, kinetics, or off-target tradeoffs). Acharya's evolution found H; this should be respected unless directly contradicted by wet-lab data.
5. ❌ "PLM3's W1507K is biophysically reasonable." — Flagged as suspicious. The −5.07 stabilization is an anomaly that needs structural validation.
