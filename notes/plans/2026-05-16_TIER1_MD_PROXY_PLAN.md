# Tier 1 MD-proxy plan — SpCas9 baseline + short dynamics check

**Authored:** 2026-05-16
**Status:** Phase A ✅ COMPLETE (2026-05-18 evening). SpCas9 PI Boltz baseline added to MSA-Boltz comparison table, doc updates propagated to verification log + PROJECT_OVERVIEW + PI brief + TECHNICAL_REPORT + PPT. Phase B (OpenMM env setup) not started; awaiting decision on whether to proceed to MD before PLM5 wet-lab data lands.
**Predecessor:** [`notes/plans/2026-05-15_ROBUSTNESS_PLAN.md`](2026-05-15_ROBUSTNESS_PLAN.md) (active robustness phase)
**Triggered by:** user request 2026-05-16 — "can we work on MD simulation and compare SpCas9 RNP binding with all variants of enFnCas9 and our novel nuclease".

---

## 0. TL;DR

Tier 1 is a *bounded* MD-proxy: ~10 ns OpenMM relaxation of the Boltz-predicted complexes for 6 systems (WT FnCas9, PLM3, PLM4, PLM5, en31, **plus SpCas9 as a cross-species baseline**), with RMSF and interface-contact-persistence as the comparison metrics. Cost: **~3–6 GPU-days + 2–4 setup days**. Output: one new section in `notes/plm/verification-log.md`, 2–3 PPT slides, a "dynamics-stability" badge for each candidate.

Tier 1 does **not** produce binding free energies. That is Tier 2 (~2 weeks) or Tier 3 (~1–2 months). See §9.

This plan does **not** alter the wet-lab gate. The five "ready for the PI" criteria in `2026-05-15_ROBUSTNESS_PLAN.md` §6 remain authoritative. Tier 1 is an *additional* confidence signal, not a replacement criterion.

---

## 1. Motivation

Three independent reasons:

1. **SpCas9 baseline.** All campaign claims so far compare to en31 (a wet-lab FnCas9 variant). The field-standard comparator is SpCas9. Adding SpCas9 to the same Boltz apples-to-apples table converts "PLM5 ≈ en31" into "PLM5 ≥ en31 ≥ SpCas9 on the predicted PAM interface". That is a stronger claim and the one the PI / reviewers will probe.
2. **Static-vs-dynamic.** Boltz-2 gives a static predicted complex with confidence scores. Confidence high at iPTM does not guarantee the contact survives thermal motion. Short MD (~10 ns) cheaply triages: any candidate whose predicted interface collapses under physiological temperature is filtered out before wet-lab.
3. **Interface contact persistence.** RMSF tells us *which* residues are floppy. PLM5's K1479F (the one PLM5 mutation that ThermoMPNN flagged at +1.45 apo cumulative) is the obvious target to watch: if its local RMSF is en31-class in MD, the apo-ΔΔG flag is resolved.

---

## 2. Scope

### In scope (Tier 1)
- 2a. **Boltz on SpCas9 + sgRNA + DNA** with the same truncation strategy used for the FnCas9 set (WED+PI-equivalent domain, or full if SpCas9 fits).
- 2b. **OpenMM relaxation** of the Boltz-predicted complex for each of 6 systems: WT FnCas9, PLM3, PLM4, PLM5, en31, SpCas9. **1 trajectory per system**, **~10 ns each**, NPT, 310 K.
- 2c. **RMSF** per residue per trajectory.
- 2d. **Interface contact persistence**: fraction of trajectory frames where each prot↔DNA-PAM contact (Cα–C1′ < 8 Å at t=0) is maintained.
- 2e. **Comparison table + figures** added to verification-log and deck.

### Out of scope (Tier 2 / Tier 3, not this plan)
- Replicate trajectories (>1 per system).
- Microsecond-scale sampling.
- MM/PBSA or MM/GBSA binding free energies.
- Alchemical (FEP, TI) binding free energies.
- APO simulations (RNP without DNA) for comparison.
- Cross-pH or cross-temperature scans.
- Mutagenesis along the trajectory (e.g. E1449L vs E1449H via FEP).

If any of these become necessary, write a fresh Tier 2 plan.

---

## 3. Implementation phases

### Phase A — SpCas9 Boltz baseline ✅ COMPLETE (2026-05-18)

1. **Sequence.** ✅ SpCas9 = UniProt Q99ZW2 (1,368 aa, *Streptococcus pyogenes*). Cached at `data/raw/Q99ZW2_spcas9.fasta`.
2. **sgRNA + DNA target.** ✅ Option (a) — same 5B2O-derived sgRNA + DNA C/D as the FnCas9 set. Apples-to-apples interface metric. Caveat documented in YAML header.
3. **Truncation.** ✅ PI domain only, residues 1100–1368 (269 aa, per Hirano 2016). Full-length 1368 aa would OOM V100 32GB. 269 aa < FnCas9's 391-aa WED+PI window so fits comfortably.
4. **Script changes.** ✅ For the single one-off, wrote YAML directly at `hpc/inputs/boltz_spcas9_pi.yaml` (no script refactor — defer until 2nd cross-species variant added). Extended `scripts/boltz_analyze.py` auto-detection to recognise `spcas9_*`, `nme1cas9_*`, `sacas9_*`, `cjcas9_*` subdirs alongside `fncas9_*`. Special label map updated: `spcas9_pi` → `SpCas9`.
5. **sbatch.** ✅ `hpc/slurm/04e_boltz_spcas9.sbatch` written, mirrors 04c structure. MSA-Boltz, 5 diffusion samples, dgx V100, 64G mem, 1h walltime.
6. **Run.** ✅ SLURM 221082 on tejas igib-dgx, COMPLETED 0:0 (2026-05-18). Output at `results/runs/2026-05-18_boltz_spcas9/spcas9_pi/`.
7. **Add to MSA-Boltz table.** ✅ Six docs updated: verification log (Tier 1 Phase A section), PI brief (TL;DR + Why-it-works §1), TECHNICAL_REPORT (Abstract + §3.5.1) + regenerated HTML, build_presentation.py (new fig_spcas9_baseline + slide 17b) → PPT regenerated, PROJECT_OVERVIEW §9.

**Results (mean ± σ over 5 diffusion samples):**
- SpCas9 PI iPTM 0.952 ± 0.001; prot↔DNA-PAM iPTM 0.967 ± 0.001.
- Naive +0.030 over PLM5 on PAM interface, but confounded by (a) truncation-size (SpCas9 PI 269 aa < FnCas9 WED+PI 391 aa; smaller systems score systematically higher) and (b) MSA-depth asymmetry (SpCas9 ortholog space dramatically richer).
- **Honest framing**: PLM5 in same high-confidence regime as SpCas9 PI (all variants iPTM > 0.92). NOT "PLM5 beats SpCas9". Within-FnCas9 "PLM5 ≥ en31" ranking preserved as clean apples-to-apples.

### Phase B — OpenMM environment setup (~1–2 days, Mac local)

1. **Install OpenMM** into `.venv` (Mac) and `.venv-hpc` (tejas).
   ```
   pip install openmm openmmforcefields openff-toolkit pdbfixer mdtraj
   ```
   `mdtraj` for analysis, `pdbfixer` for adding missing atoms / hydrogens, `openmmforcefields` for combined ff14SB / OL3 / OL15 in one ForceField object.
2. **Test installation.** Run OpenMM's "lysozyme in water" example on Mac (10 min). Verify GPU codepath works on tejas via a 100-step test on V100.
3. **Force field decision.**
   - Protein: **AMBER ff14SB** (standard, well-validated). ff19SB is newer but requires OPC water; ff14SB pairs cleanly with TIP3P.
   - RNA: **AMBER OL3** (default for RNA).
   - DNA: **AMBER OL15** (default for B-DNA).
   - Water: **TIP3P** (matches ff14SB).
   - Ions: 0.15 M NaCl, Joung & Cheatham parameters.
4. **Convert Boltz outputs to MD-ready input.**
   - Boltz writes CIF. Convert to PDB via `mdtraj` or `biotite`.
   - Pick the **highest-confidence model** per variant (model_0 in the Boltz outputs is typically the best per `confidence_*.json`).
   - Run `pdbfixer` to add hydrogens, fix any missing atoms.
   - Solvate in a TIP3P octahedron, 10 Å padding from any solute atom.
   - Neutralise + 0.15 M NaCl.
5. **Test on WT FnCas9.** Minimise → 100 ps NVT (300 K) → 1 ns NPT equilibration → 1 ns NPT production at 310 K. Verify trajectory writes, no NaNs, no exploding atoms.

**Success:** WT FnCas9 trajectory completes 1 ns on the Mac (or V100 if Mac is too slow) with no crashes; RMSD trajectory plot looks reasonable (drifts in the 1–3 Å range, no jumps).

**Known risk:** Boltz-predicted structures may have rotamer clashes that crash MD even after minimisation. If so, increase minimisation tolerance, or rebuild sidechains via `pdbfixer.removeHydrogens()` + re-add.

### Phase C — Production relaxation (~3–6 GPU-days, HPC)

1. **Write `scripts/openmm_relax.py`** — one-shot runner taking a starting PDB and an output trajectory path:
   - Minimise (5,000 steps, default tolerance).
   - NVT 100 ps at 300 K, position-restrained protein (10 kcal/mol/Å²).
   - NPT 1 ns at 310 K, restraints off.
   - **Production: 10 ns NPT at 310 K, 2 fs timestep with HMR + constraints, 1 frame / 10 ps.**
   - Save trajectory as DCD, save final state as XML.
   - Log RMSD every 100 ps to verify stability live.
2. **HPC walltime.** ~50 ns/day on V100 → 10 ns ≈ 4.8 hours. Exceeds the **~1.5 h practical dgx limit**. **Restart logic required**:
   - Save checkpoint XML every 30 min.
   - On restart, load XML and continue from last saved step.
   - Wrap in a sbatch that submits N back-to-back jobs (N≈4 for 10 ns) using `--dependency=afterany:<prev>`.
3. **`hpc/slurm/06_openmm_relax.sbatch`** template + a small launcher script `scripts/queue_openmm_chain.sh <variant>` that submits the chain.
4. **Run order.** WT first (lowest risk), then PLM5 (most important), then en31, then PLM4 / PLM3 / SpCas9. Parallelise if multiple GPUs available.
5. **Storage.** ~150 MB per trajectory (~10 GB total). Fits My Passport easily; HPC scratch fine.

**Success:** 6 trajectories complete to 10 ns. No system shows RMSD > 5 Å vs starting structure at any point past 2 ns equilibration.

**Known risk:** SpCas9 may need its own pdbfixer pass (different residue conventions). May need a longer NPT equilibration (2 ns instead of 1 ns) if the system is more strained.

### Phase D — Analysis + figures (~1 day, Mac local)

1. **`scripts/openmm_analyze.py`** — takes a trajectory + topology, outputs:
   - RMSD vs time (CSV + PNG).
   - RMSF per residue (CSV + PNG).
   - Contact persistence: for each Cα(protein)–C1'(DNA-PAM) pair within 8 Å at t=0, fraction of frames where pair is still within 10 Å. Output CSV.
2. **Comparison figures** (extend `scripts/build_presentation.py`):
   - **`fig_md_rmsf_overlay.png`** — RMSF traces for {WT, PLM5, en31, SpCas9} overlaid, mutation positions marked. PLM5 should track WT/en31 at the engineered positions.
   - **`fig_md_contact_persistence.png`** — bar chart, per variant: mean prot↔DNA-PAM contact persistence (0–1). Higher = more stable interface.
   - **`fig_md_rmsd_traces.png`** — RMSD vs time for all 6 systems, single panel. Sanity check that no system blew up.
3. **Aggregation table** (`results/runs/<date>_md_proxy/summary.tsv`):
   - Columns: variant | iPTM (Boltz) | mean RMSD | mean RMSF (engineered positions only) | contact persistence (%) | verdict
   - Append to `notes/plm/verification-log.md` under a new "MD-proxy (Tier 1)" section.
4. **PPT update**: 2 new slides:
   - Slide N: "Tier 1 MD-proxy — RMSF profile" (with `fig_md_rmsf_overlay.png`).
   - Slide N+1: "Tier 1 MD-proxy — interface contact persistence" (with `fig_md_contact_persistence.png`).
5. **Decision matrix**:
   - PLM5 contact persistence ≥ en31's: confidence reinforced ✅
   - PLM5 contact persistence within 5% of en31: still ✅, framed as "MD agrees with Boltz".
   - PLM5 contact persistence >10% lower than en31 and K1479F shows elevated RMSF: flag for Tier 2 (longer MD + replicates). Do **not** invalidate the candidate on one Tier 1 trajectory.

---

## 4. Compute / storage budget

| Phase | Compute | Storage | Wall time |
|---|---|---|---|
| A — SpCas9 Boltz | ~10 min V100 | 100 MB | ~1 hour incl. analysis |
| B — OpenMM setup | Mac CPU + 1 hr V100 test | 1 GB | 1–2 days human |
| C — 6 × 10 ns NPT | ~3–6 V100-days (restart overhead included) | 10 GB | 2–7 days wall (depending on queue) |
| D — analysis + figures | Mac CPU | 50 MB | 1 day human |
| **Total** | **~3–6 GPU-days + 1 hr Boltz** | **~12 GB** | **~1–2 weeks elapsed** |

Tejas dgx is V100-only. If an A100/H100 node becomes available, ~10× speedup possible; would compress Phase C to <1 day.

---

## 5. Software / dependency setup

```
# .venv (Mac) and .venv-hpc (tejas):
pip install \
    openmm==8.2.0 \
    openmmforcefields==0.13.0 \
    openff-toolkit==0.16.0 \
    pdbfixer==1.10.0 \
    mdtraj==1.10.0
```

(Versions are anchors as of 2026-05; pin to whatever resolves cleanly with current `numpy<2`.)

Force field files: shipped with `openmmforcefields`. No external downloads.

AmberTools: NOT needed (we are using OpenMM-native parameterisation via `openmmforcefields`).

---

## 6. Known risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Boltz CIF → MD input pipeline broken | medium | Manual conversion via mdtraj + pdbfixer; have a tested WT pass before any other variant. |
| Force field can't parameterise some residue (e.g. non-standard tail) | low | Truncate or model. |
| Predicted structures crash MD under minimisation | medium | Multi-stage minimisation (10⁵ steps), then 100 ps NVT with strong restraints, then progressive restraint release. |
| Trajectory NaN / explodes mid-run | low | Validated workflow above; checkpoint every 30 min so loss is bounded. |
| HPC walltime limit forces restart chains | certain | Built into Phase C plan (chained sbatch). |
| Single trajectory not enough to call differences significant | high | Honest framing: Tier 1 is triage, not measurement. Differences >10% are signals to investigate, not conclusions. |
| SpCas9 sgRNA mismatch (chain B not designed for SpCas9 scaffold) | medium | Acknowledged in interpretation. Run also with SpCas9-canonical target if Phase A leaves time. |

---

## 7. Success criteria — when is Tier 1 "done"?

Tier 1 is complete when **all** of:

1. ☐ SpCas9 has a row in the MSA-Boltz comparison table with iPTM and prot↔DNA-PAM iPTM.
2. ☐ 6 trajectories (WT, PLM3, PLM4, PLM5, en31, SpCas9) each reach 10 ns with stable RMSD.
3. ☐ RMSF profile recorded for each variant; engineered positions in PLM5 are not measurably more flexible than en31's engineered positions (within 1 Å² of the local mean).
4. ☐ Interface contact persistence computed for each variant; PLM5's value is ≥ 90% of en31's.
5. ☐ Two PPT slides added; verification log updated.

If 1–4 are green: confidence reinforced. The wet-lab handoff conversation gains one more independent line of evidence.

If any of 3 or 4 fail: that is a *signal*, not a verdict. Trigger Tier 2 (longer MD + replicates) before invalidating the candidate.

---

## 8. Where Tier 1 sits in the project timeline

```
[robustness §2.4 Protein2PAM]   ⎫
        +                        ⎬───→ all green ──→ wet-lab handoff conversation (PI gate)
[robustness §2.5 E1449L/H]       ⎭                                    │
                                                                      │
                            (Tier 1 MD-proxy runs in parallel here, OR after, OR not at all
                             depending on what's still needed for the PI conversation)
```

Tier 1 is **optional**. If §2.4 + §2.5 close cleanly and the PI is satisfied without MD, skip Tier 1 and let wet-lab be the next signal. If the PI conversation surfaces a "but how do we know it's dynamically stable" question, run Tier 1 in response.

---

## 9. Why not Tier 2 or Tier 3 now?

| Tier | What it gives | What it costs | Why not now |
|---|---|---|---|
| Tier 1 (this plan) | Dynamic-stability triage + SpCas9 baseline | ~1 week + 5 GPU-days | Cheap insurance pre-PI |
| Tier 2 | Same systems, 100 ns × 3 replicates → significance | ~3 weeks + 50 GPU-days | Only justified after a wet-lab signal, not before |
| Tier 3 | MM/PBSA or alchemical binding ΔG, publication-quality | ~1–2 months + 200+ GPU-days | For the follow-up paper, not the first one |

The project's current question is "is this candidate worth wet-lab spend?" Tier 1 answers that. Tier 2/3 answer downstream questions.

---

## 10. Open decisions to resolve before starting Phase A

| Decision | Owner | Default if no input |
|---|---|---|
| SpCas9 sgRNA/DNA: 5B2O-derived (a) vs SpCas9-canonical (b)? | user | (a) — apples-to-apples |
| Include APO (no DNA) trajectories? | user | NO — out of scope |
| Force field: ff14SB vs ff19SB? | (technical) | ff14SB + TIP3P — better-tested combo |
| Truncate SpCas9 for V100 fit, or wait for an A100? | user | Truncate (faster turnaround) |

---

*Live roadmap. Update inline as items complete. Per-session work tracking continues in `notes/worklog/`.*
