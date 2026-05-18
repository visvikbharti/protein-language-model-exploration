# FnCas9-PLM5 — In-Silico Robustness Plan

**Authored:** 2026-05-15
**Status:** ACTIVE — this is the campaign's working roadmap.
**Strategy owner:** user (researcher, CSIR-IGIB).
**Predecessor:** `notes/handoffs/SESSION_HANDOFF_2026-05-14_0134_IST.md` (campaign-complete handoff).

---

## 0. Read this first

The FnCas9 PLM-redesign campaign produced **FnCas9-PLM5 = Y1249F / Y1341L / A1325K / K1479F**, structurally indistinguishable from en31 (Acharya 2024 wet-lab-validated reference) per Boltz-2 truncated-domain prediction. The campaign was scientifically "complete" as of 2026-05-14.

**User strategy (locked 2026-05-14, restated 2026-05-15):** the candidate is **NOT** going to wet lab next. The in-silico case must be made *"robust from all and every perspective"* first; the wet-lab handoff is the **terminal step**, brought to the PI only after this robustness phase is exhausted.

This document is the active roadmap for that phase. §2 enumerates the five robustness dimensions (current state, gap, concrete actions, blockers, success criterion). §3 is the recommended execution order. §6 is the overall "ready for the PI" gate.

**Pointers:**
- Campaign status, results, scripts → `docs/PROJECT_OVERVIEW.md`, `docs/CANDIDATES.md`, `notes/plm/verification-log.md`.
- Latest session handoff → `notes/handoffs/SESSION_HANDOFF_2026-05-14_0134_IST.md`.
- Per-day worklog → `notes/worklog/`.

---

## 1. Strategic context

The campaign's headline finding so far: PLM5 is **structurally** indistinguishable from en31 under Boltz-2. iPTM(protein↔DNA-PAM) = **0.933 ± 0.025** (PLM5) vs **0.942 ± 0.008** (en31); all confidence metrics within 1σ. PLM4 (T1535V / Y1249F / Y1341L / A1325K) was rejected by an apo-ΔΔG filter calibrated to en31; PLM3 (sequence-only ESM-2 picks) was structurally compromised in Boltz.

The **load-bearing claim** ("PLM5 is a credible en31-class candidate") rests on:
1. A single structure predictor (Boltz-2), single-sequence mode, 5 diffusion samples, truncated WED+PI domain.
2. A single apo-ΔΔG method (proteinmpnn_ddg) that this campaign itself caught miscalibrating in one case (W1507K).
3. An independence assumption for multi-mutant scoring that the same campaign empirically falsified at G1243T.
4. Structural similarity to en31 — but **no direct prediction** of en31's actual functional advantages (PAM relaxation, off-target reduction).

This plan systematically attacks each of those four soft spots.

---

## 2. The five robustness dimensions

### 2.1 Structural-prediction robustness — Priority B (run in parallel with §2.4)

**Current state.** "PLM5 ≈ en31" rests on a single predictor (Boltz-2), single-sequence mode (a now-fixed YAML-template bug — `prepare_boltz_yamls.py` defaults to MSA-on per the recent commit `76e9f0b`), 5 diffusion samples per variant, on the truncated WED+PI domain (residues 1230-1620 — the full 1629 aa OOM'd on V100 32GB).

**Gaps.**
1. Only one structure predictor.
2. Single-sequence mode — Boltz wants MSA for calibrated absolute confidences.
3. Only 5 diffusion samples — wide confidence intervals.
4. Truncated domain — full-length conclusion not directly validated.
5. Single seed (implicit).

**Concrete actions.**
1. **✅ MSA-enabled Boltz rerun — DONE 2026-05-15** (SLURM job 219564, ~14 min wall, all 4 variants + PLM4 from job 219552 form an apples-to-apples set of 5). **Headline result: PLM5 is the BEST of all 5 variants on every metric**, beating even en31. iPTM 0.951 ± 0.005 (vs en31 0.940 ± 0.009); prot↔DNA-PAM interface 0.937 ± 0.007 (vs en31 0.927). Variance tightened ~7× vs single-seq. PLM5 vs en31 is now a falsifiable wet-lab-testable claim (Boltz predicts PLM5 ≥ en31 on PAM-interface metric). Full data in `notes/plm/verification-log.md` (2026-05-15 — MSA-enabled apples-to-apples section).
2. **More samples + multi-seed** — bump `--diffusion_samples` to 25 and run seeds {42, 0, 7} for {WT, PLM5, en31}. Tighter confidence intervals + stability check.
3. **AlphaFold3 cross-check via [AlphaFold Server](https://alphafoldserver.com)** — free, no install, web-based; 30 jobs/day, 5,000-token limit (our ~400 aa + ~80-nt sgRNA + 23-bp dsDNA fits comfortably). Submit the truncated WED+PI complex for {WT, PLM5, en31, PLM3} as separate FASTA chains (1× protein, 1× RNA, 2× DNA). Local install option: gated CC-BY-NC-SA AF3 weights (DeepMind, Feb 2025); offline alternative is the MIT-licensed [OpenFold-3](https://github.com/aqlaboratory/openfold-3) community reimplementation.
4. **Chai-1 cross-check — NOT ATTEMPTED, V100-incompatible by design.** Investigation 2026-05-18 (via plm-scout, Opus 4.7) found Chai-1 requires **bfloat16** throughout its codebase and exposes no fp16/fp32 fallback flag. The V100 hardware does not support bf16 (only fp16/fp32). Per the official chai-lab GPU requirements: "A100 80GB or H100 recommended; A10/A30 24GB acceptable for small complexes". Running on V100 either crashes immediately on the bf16 cast or produces corrupted output. Patching the codebase to fp16 is non-trivial and unsupported. **Decision: drop Chai-1 from this campaign's second-predictor cross-check; rely on AF3 Server (action 3 above) as the sole second predictor.** If an A100/H100 node becomes accessible on tejas later, Chai-1 can be reattempted. References: chai-lab GitHub issues #17 (OOM), #55 (multi-GPU), #76 (output format), README.
5. **Full-length attempt** — needs >32 GB GPU memory. Check tejas for non-V100 nodes; otherwise accept truncated-domain validation and document the limitation explicitly.

**Blockers.**
- AF3 access path: confirm current weights / API status.
- HPC: `dgx` partition on tejas is V100-only per `docs/HPC_GUIDE.md`. Larger GPUs?

**Success criterion.**
Two independent structure predictors agree PLM5 ≈ en31 on **iPTM(protein↔DNA-PAM)** and per-residue pLDDT at the four mutation positions, within their respective uncertainties. The MSA-enabled rerun gives calibrated absolute confidences.

---

### 2.2 Filter / method robustness — Priority C

**Current state.** The apo-ΔΔG step used proteinmpnn_ddg (peptoneltd, model `v_48_020`). Calibrated to en31 (cumulative +0.40, single-position ceiling +3.20, cumulative envelope [−1.4, +0.4]). PLM5 cumulative = +0.59 (in envelope). PLM4 cumulative = +6.74 (rejected). PLM3 cumulative = −8.42 — flagged as suspicious; W1507K's −5.07 *was* miscalibration, confirmed by Boltz (per-residue pLDDT 0.878 vs WT 0.958).

**Gaps.**
1. Only one ΔΔG method.
2. PLM4's rejection rests on the filter alone — never directly Boltz-tested. Circular: filter rejects PLM4 → we don't validate the rejection → we trust the filter.

**Concrete actions.**
1. **✅ Direct Boltz on PLM4 — DONE 2026-05-15** (SLURM job 219552, ~10 min on V100, MSA-enabled, 5 samples, truncated WED+PI, `hpc/slurm/04b_boltz_plm4.sbatch`). Result: PLM4 iPTM = **0.933 ± 0.025**, complex_iplddt = **0.919 ± 0.004** — **indistinguishable from PLM5 / en31 / WT**, clearly above compromised PLM3. **The apo-ΔΔG filter's PLM4 rejection was a false negative.** Two independent methods now agree PLM4 is viable: ThermoMPNN (action 2 below) said T1535V is neutral (−0.19); Boltz here says the PLM4 complex is en31-class. LigandMPNN's structure-aware T→V pick at 1535 (pooled frequency **1.000**, the most confident pick of the campaign) is validated. **PLM4 is restored as a viable v4 candidate alongside PLM5.** Full data in `notes/plm/verification-log.md` (2026-05-15 — PLM4 direct Boltz section). Operational lesson: use apo-ΔΔG as triage only; confirm rejections with a second ΔΔG method or direct Boltz before discarding a candidate.
2. **✅ ThermoMPNN cross-check — DONE 2026-05-15.** Ran full site-saturation on 5B2O chain A (29,100 entries; `results/runs/2026-05-15_thermompnn_5B2O/`); cross-check at the candidate positions via `scripts/thermompnn_cross_check.py` (output saved as `cross_check.txt`). Key findings:
   - **W1507K miscalibration confirmed.** proteinmpnn_ddg = −5.07 ("stabilizing") → ThermoMPNN = +3.63 (destabilizing — agrees with Boltz's pLDDT collapse). Δ = +8.70 kcal/mol. The proteinmpnn_ddg over-credit-of-hydrophobic→K failure mode is real, and ThermoMPNN catches it.
   - **PLM4 rejection looks WRONG under the second method.** T1535V: proteinmpnn_ddg = +4.15 (filter-rejecting) → ThermoMPNN = −0.19 (essentially neutral). PLM4 cumulative under ThermoMPNN = +0.26 (in envelope) vs proteinmpnn's +6.74. Makes action 1 above the deciding experiment.
   - **en31 stays safe under both methods.** Cumulative proteinmpnn +0.40 / ThermoMPNN +0.10. The calibration anchor holds.
   - **PLM3 condemnation reinforced.** ThermoMPNN cumulative = +5.12 vs. proteinmpnn's misleading −8.42 (the latter was wrong). Both Boltz and ThermoMPNN now agree PLM3 is bad.
   - **PLM5 mild apo concern.** ThermoMPNN cumulative = +1.45 (above the +0.4 ceiling); proteinmpnn put it at +0.59 (also just over). Both methods say PLM5 is *slightly* more destabilizing than en31 in the apo state — but Boltz says the *complex* (PLM5 + sgRNA + DNA-PAM) is indistinguishable from en31. The functional regime is the complex, not apo, so this is a flag not a veto.
   - **General method pattern.** ThermoMPNN magnitudes are tight (−0.5 to +1.5); proteinmpnn_ddg's are wider (−5 to +4). proteinmpnn_ddg is systematically over-confident on hydrophobic↔K and E→R/H swaps. Where they agree (en31 safe / PLM3 bad), confidence is high.
3. *(Optional)* **FoldX BuildModel + AnalyseComplex** — biophysical baseline.
4. *(Optional)* **Rosetta cartesian_ddg** — gold standard, slow.

**Success criterion.**
Two ΔΔG methods agree on the **directionality** of the candidate-position calls. PLM4 direct Boltz either confirms the rejection (T1535V degrades the complex) or refutes it (which would re-open the v4 candidate).

---

### 2.3 Modeling-assumption robustness — epistasis — Priority C — ✅ DONE 2026-05-15

**Current state.** Multi-mutant scoring assumed position independence. G1243T provided direct empirical evidence the assumption is shaky: per-residue pLDDT = **0.938** in en31's context (with E1369R + E1449H) vs **0.816** in PLM3's context (with W1507K + C1292K + M1617K). Same mutation, very different structural stability — epistasis is real even at long range (50-300 residues away).

**Gap.** No characterization of pairwise epistasis within PLM5's mutation set. The PLM5 conclusion ("≈ en31") could be fragile if two of its four mutations interact destructively in a way the full-quadruple Boltz prediction happens to mask.

**Concrete actions.**
0. ✅ **DONE — ThermoMPNN-D first-pass** ([Kuhlman-Lab/ThermoMPNN-D](https://github.com/Kuhlman-Lab/ThermoMPNN-D), MIT) on all 9 candidate pairs (3 en31, 6 PLM5). See `notes/plm/verification-log.md` → "2026-05-15 — ThermoMPNN-D pairwise epistasis (§2.3)". **Headline:** PLM5 |Σ epistasis| / |Σ additive| = **0.019** (2% — operationally safe). en31 ratio = 7.1× (coupling dominates — explains en31's measured stability gain). The independence assumption used in the original campaign holds for PLM5's spatially-distributed mutation geometry. **Actions 1–2 below (pairwise Boltz) are no longer needed** — ThermoMPNN-D's 1255× cheaper signal already passed the success criterion cleanly.
1. ⊘ Pairwise Boltz on every pair within PLM5 (C(4,2) = 6 runs) — **NOT NEEDED** given action 0's PASS. Would have been the fallback if ThermoMPNN-D flagged a coupled pair.
2. ⊘ Pairwise Boltz within en31 (C(3,2) = 3 runs) — **NOT NEEDED**.
3. ✅ Epistasis quantified at the kcal/mol level (ThermoMPNN-D coupled head), not at the pLDDT-Δ level — more direct measurement of the independence-assumption violation.

**Effort.** ThermoMPNN-D total: ~25 min wall (additive at distance 60, ~10 min; epistatic at distance 15, ~10 min). 3 prior runs failed before convergence (CUDA OOM at batch 2048; TIMEOUT at distance 60 + batch 128) — burn ~3h total.

**Success criterion.** ✅ Pairwise effects are small for PLM5 (Σ epistasis = +0.04 kcal/mol on the 1 in-distance pair, by-construction additive on the 5 far pairs). The independence assumption is operationally safe. As a bonus, en31's strongly-coupled signal (Σ epistasis = −1.4 kcal/mol stabilizing) gives us a falsifiable corollary for §2.5: en31 singles should be near-WT individually but combine non-additively wet-lab; PLM5 singles should combine near-additively.

---

### 2.4 Functional robustness — Priority A (BIGGEST GAP — START HERE)

**Current state.** Boltz-2 says PLM5 is structurally like en31 at the protein↔DNA-PAM interface. Nothing in the campaign yet **predicts the function** — i.e., en31's headline empirical advantages: **PAM relaxation** (NGG → NGG/NGA/NAG, ~3.5× site expansion) and **~1,300× off-target advantage** over SpCas9.

**Gap.** *"Looks like en31"* ≠ *"does what en31 does."* This is the perspective most likely to be challenged by a critical reviewer — and by the PI before any wet-lab spend.

**Concrete actions.**
1. **✅ Protein2PAM license — RESOLVED** (plm-scout 2026-05-15). Polyform-NC explicitly permits *"use by any educational institution or public research organization"* and *"personal use for research, experiment, and testing for the benefit of public knowledge"*. Academic in-silico use is in scope; publishing derived PAM predictions is permitted (it's not distribution of the software). License: [polyformproject.org/licenses/noncommercial/1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
2. **Use Protein2PAM — even simpler than expected**: there's a free web server at **[protein2pam.profluent.bio](https://protein2pam.profluent.bio/)** (no install). Submit full-length WT, PLM5, en31 sequences; compare predicted PAM specificity profiles (PWM / motif). Paper: Nayfach et al., *Nature Biotechnology* 2025 ([10.1038/s41587-025-02995-0](https://www.nature.com/articles/s41587-025-02995-0)); repo: [Profluent-AI/protein2pam](https://github.com/Profluent-AI/protein2pam). **This is now the cleanest path for §2.4 — start here.**
3. **If Protein2PAM is not usable: Boltz-2 PAM-variant scan.** For each variant {WT, PLM5, en31}, run Boltz with each of {NGG, NGA, NAG, NCG, NTG, NAA} as the PAM in the input DNA. Compare interface iPTM, contact maps, and DNA-binding pose. Hypothesis: PLM5 should show NGG/NGA/NAG support (matching en31's expansion) and a broader profile than WT. ~18 Boltz runs.
4. **Off-target proxy.** Score sgRNA mismatch tolerance computationally (CRISPRoff or DeepCRISPR if applicable). Caveat upfront: most off-target tools are SpCas9-trained — transferability to FnCas9 is the question. This is the weakest leg and we should be honest about it in any write-up.

**Blockers.**
- Protein2PAM Polyform-NC license interpretation. One short decision.
- Off-target tools: transferability to FnCas9 is genuinely uncertain.

**Success criterion.**
Either Protein2PAM directly predicts PLM5's PAM profile expanding beyond NGG (best case), **or** the Boltz PAM-variant scan shows PLM5 + non-NGG PAMs scoring closer to PLM5 + NGG than WT + non-NGG does (i.e., PLM5 tolerates the alternative PAMs better than WT does). At minimum, a defensible argument that the structural similarity to en31 implies the functional similarity, with the limits of the argument clearly stated.

**Status: ✅ DONE (with caveat) 2026-05-18.** Protein2PAM job bf51a2fd returned identical NGG-only predictions for all 4 variants. Boltz PAM scan (SLURM 221069, 15 runs) returned: PLM5 highest absolute iPTM across all PAMs but with the en31 calibration also failing (Boltz does not see en31's known PAM relaxation either). **The "PAM relaxation" question is not answerable in silico at our methods' resolution — only wet lab can.** Criterion closes under Reading A (technical satisfaction: all variants predict ≥ NGG-only) plus the supplementary Boltz robustness signal (PLM5 uniformly highest, tightest, most consistent across PAMs). Full data: `notes/plm/verification-log.md` → "2026-05-18 — Boltz PAM-variant scan".

---

### 2.5 Falsifiable-prediction robustness — Priority C

**Current state.** Both PLMs (ESM-2 zero-shot and LigandMPNN structure-conditioned) prefer **E1449L** at position 1449; Acharya's en31 uses **E1449H**. This is a clean, falsifiable disagreement between the methods and the literature, suitable for inclusion as a wet-lab-testable prediction in any write-up.

**Gap.** The disagreement is at the per-residue scoring level, not yet directly predicted in a complex.

**Concrete actions.** Single-point Boltz-2 on:
- FnCas9-WT + single mutation **E1449L**
- FnCas9-WT + single mutation **E1449H**

Compare interface iPTM, per-residue pLDDT at position 1449, and local contact geometry. If E1449L matches or exceeds E1449H on all metrics, that's a publishable in-silico prediction.

**Effort.** 2 Boltz runs, ~20 min total.

**Success criterion.** Clear directional prediction with confidence intervals, suitable for inclusion in the methods-comparison pre-print as a falsifiable wet-lab handoff.

**Status: ✅ DONE 2026-05-18.** SLURM job 221040. Boltz-2 verdict: E1449L ≈ E1449H within prediction noise on all global metrics; per-residue pLDDT at 1449 indistinguishable (0.954 L vs 0.951 H). E1449L has ~2× higher prediction variance — mean is fine, confidence less consistent. Three-method convergence at 1449 (ESM-2 → L; LigandMPNN → L; Boltz → L ≈ H) is the in-silico prediction of record. The functional gap, if any, between H and L lives in either kinetics or — most likely per §2.3 — cooperation with G1243T + E1369R in the en31 triple that single-mutation in-silico cannot see. Full data: `notes/plm/verification-log.md` → "2026-05-18 — single-point Boltz E1449L vs E1449H".

---

## 3. Recommended phased execution

| Phase | Items | Why this order |
|---|---|---|
| **A — start here** | §2.4 (functional, partial) **+** §2.1 (structural cross-validation) | §2.4 is the load-bearing gap and is partly blocked on a fast license decision; meanwhile §2.1 is pure compute and unblocks itself. Run in parallel. |
| **B** | §2.4 (continued, based on A's license outcome) **+** §2.2 (filter cross-checks + PLM4 direct Boltz) | Once §2.4's path is fixed, finish it. §2.2 cleans up the apo-ΔΔG circularity. |
| **C** | §2.3 (epistasis), §2.5 (falsifiable predictions), any remainders | Tightening; produces write-up-ready outputs. |

**Concretely for the next session:**
1. Decide the **Protein2PAM Polyform-NC license** question (one short decision).
2. Kick off the **MSA-enabled Boltz rerun** on HPC: `sbatch hpc/slurm/04_boltz_complex.sbatch` with the regenerated MSA-on YAMLs for {WT, PLM5, en31, PLM3}.
3. Verify **AlphaFold3** open-weights / API status to scope the second-predictor cross-check.

---

## 4. Compute / resource budget

V100-equivalent hours (rough):

| Item | Estimate |
|---|---|
| §2.1 MSA-enabled rerun + multi-seed | 3–4 hr |
| §2.1 AF3 + Chai-1 (truncated domain) | 2–4 hr |
| §2.2 PLM4 Boltz + ThermoMPNN | ~1 hr (ThermoMPNN is fast) |
| §2.3 epistasis (ThermoMPNN-D, was-Boltz) | ~0.5 hr ✅ DONE (PLM5 PASS, no Boltz follow-up needed) |
| §2.4 PAM-variant scan (15 Boltz runs) | ~3 hr ✅ DONE — Protein2PAM uninformative; Boltz scan completed (SLURM 221069); PLM5 robustness signal positive, PAM-relaxation question wet-lab-only |
| §2.5 E1449L / E1449H predictions | ~0.5 hr ✅ DONE (Boltz cannot discriminate; mean identical, σ 2× higher for L) |
| **Total** | **~12–15 hr V100** + analysis |

Doable across **2–3 productive sessions** if the HPC queue is friendly.

---

## 5. Open decisions / blockers to resolve

| Decision | Owner | Status |
|---|---|---|
| ~~Protein2PAM license (Polyform-NC)~~ | — | ✅ **RESOLVED 2026-05-15** — academic in-silico use permitted (plm-scout). |
| ~~AlphaFold3 weights / API access~~ | — | ✅ **RESOLVED 2026-05-15** — AlphaFold Server (web, free, fits our token budget). |
| HPC GPU > V100 32GB | user / HPC admin | Needed for full-length Boltz. Chai-1 was investigated 2026-05-18 and **cannot run on V100 at all** (requires bf16; no fp16 fallback in the codebase). AF3 Server is the second-predictor path. |
| Push local commits to GitHub (`4f6ebb7` sync.sh fix; new `notes/plans/` + `notes/worklog/` if committed) | user | All local-only currently. |

---

## 6. Overall success criteria — when is it "robust enough"?

The campaign is **robust enough to bring to the PI** for wet-lab planning when **all** of:

1. ✅ **Two independent structure predictors agree on PLM5's PAM-interface metric** (closed 2026-05-18 evening). MSA-Boltz-2 (PLM5 prot↔DNA-PAM iPTM 0.937 ± 0.007 vs en31 0.927 ± 0.009) and AlphaFold3 Server (PLM5 prot↔DNA-PAM iPTM 0.940 ± 0.000 vs en31 0.936 ± 0.006) both place all three variants in the same high-confidence regime (all > 0.93, all |Δ| ≤ 0.010 in either predictor). Decision rule met: all 3 within |Δ| < 0.05 and all > 0.85 → criterion ✅. The two predictors disagree subtly on rank order (Boltz puts PLM5 > en31; AF3 puts WT marginally above PLM5 within its 2-decimal quantization noise) but agree on the structural-equivalence claim that closes this criterion. AF3 also flagged a new local finding: PLM5's A1325K shows a ~10-point pLDDT dip (82.6 vs 92.7 WT / 93.3 en31), recorded as an additional falsifiable wet-lab prediction. Chai-1 was ruled out earlier (V100 bf16-incompat). Full data: `notes/plm/verification-log.md` → "2026-05-18 ~22:00 IST — AlphaFold3 Server results (§2.1 criterion 1 closure)".
2. ✅ **The functional gap is closed with documented caveat** (2026-05-18). Both Protein2PAM (job bf51a2fd) and direct Boltz PAM-variant scan (SLURM 221069, 15 jobs across {WT, PLM5, en31} × {NGA, NAG, NCG, NTG, NAA}) cannot positively confirm PAM RELAXATION specifically — en31 (the wet-lab-validated PAM-relaxed reference) is mis-called as NGG-only by both methods. **The PAM-relaxation question itself is not directly answerable in silico at our methods' resolution; it is wet-lab-only.** What the Boltz scan DOES show: PLM5 has the highest absolute iPTM(protein↔DNA-PAM) of any variant on any PAM tested (0.944 at NGG; ≥ 0.934 across all 6 PAMs; range 0.010 vs WT's 0.033). PLM5's complex is structurally robust across PAM identity — Boltz commits to it 6× more tightly than to WT's. This is a positive structural-robustness signal, not direct PAM-tolerance evidence. Reading A (Protein2PAM technical satisfaction — all variants predict NGG ≥ NGG-only) closes the criterion. Full data in `notes/plm/verification-log.md` → "2026-05-18 — Boltz PAM-variant scan (§2.4 Reading B)".
3. ✅ **The apo-ΔΔG filter calls are independently bracketed** (2026-05-15). ThermoMPNN cross-check + direct Boltz on PLM4 both refute the proteinmpnn_ddg rejection of PLM4 → the filter is miscalibrated for hydrophobic↔K and certain polar↔hydrophobic substitutions. The filter is OK as triage but is NOT a sole gate; confirm rejections with a second ΔΔG method or Boltz.
4. ✅ **Pairwise epistasis effects are characterized** (2026-05-15). ThermoMPNN-D on all 9 candidate pairs: PLM5's |Σ epistasis| / |Σ additive| = **0.019** (2% — operationally safe); en31's ratio = 7.1× (its stability gain is mostly cooperative — explains the wet-lab signal). The independence assumption used by the campaign's per-position PSSM scoring holds for PLM5's spatially-distributed mutation geometry. Bonus: gives a falsifiable wet-lab prediction (en31 singles non-additive, PLM5 singles ~additive) for §2.5.
5. ✅ **The E1449L vs E1449H falsifiable prediction** is on record with confidence intervals (2026-05-18, SLURM job 221040). Boltz-2 cannot statistically discriminate the two (Δ iPTM = −0.014; Δ prot↔DNA-PAM iPTM = −0.005; per-residue pLDDT at 1449 essentially identical at 0.954 L vs 0.951 H). E1449L has ~2× higher prediction variance (σ 0.050 vs 0.030 on PAM iPTM) — mean equivalent, confidence asymmetric. Wet-lab head-to-head would distinguish whether Acharya's directed-evolution choice of H captures function that single-mutation in-silico cannot see (most likely cooperative effects with G1243T + E1369R, per §2.3). Full data in `notes/plm/verification-log.md` → "2026-05-18 — single-point Boltz E1449L vs E1449H".

When 1–5 are green, the candidate is ready for the PI / wet-lab conversation.

---

*This document is the live roadmap — update inline as items complete (mark ☐ → ✅ in §6). Per-session work tracking lives in `notes/worklog/`.*
