# Next-session priming prompt

Paste the block below as the first message in the next session. Works for either the **2026-05-16 evening session** (when the user returns to campus and the HPC VPN is no longer needed) **or any later session**.

---

Resuming the FnCas9 PLM-redesign project. Robustness phase is mid-flight; we are NOT yet at the wet-lab handoff. **Today's session date varies — read the worklogs in order to confirm the latest state before acting.**

**State at end of 2026-05-16 afternoon session:**

- In-silico campaign is complete; recommended candidate is **FnCas9-PLM5** (Y1249F / Y1341L / A1325K / K1479F). PLM4 is a viable backup (T1535V replaces K1479F).
- Robustness phase is **3 of 5 "ready for the PI" criteria ✅ DONE**:
  - ✅ §2.1 partial — MSA-Boltz across 5 variants (PLM5 leads even en31). Second predictor still needed for full ✅.
  - ✅ §2.2 apo-ΔΔG filter bracketed (PLM4 reinstated; proteinmpnn_ddg known-miscalibrated for hydrophobic↔K).
  - ✅ §2.3 pairwise epistasis characterized (ThermoMPNN-D: PLM5 |Σ ep|/|Σ add| = 0.019; en31's = 7.1×).
- **§2.5 IMPLEMENTED LOCALLY ON 2026-05-16, NOT YET SUBMITTED.** Files already exist:
  - `scripts/prepare_boltz_yamls.py` — `fncas9_e1449l` and `fncas9_e1449h` already in the variants dict.
  - `hpc/slurm/04c_boltz_e1449.sbatch` — sbatch ready to submit (mirrors the 04b PLM4 pattern).
  - `hpc/inputs/boltz_fncas9_e1449l.yaml` and `boltz_fncas9_e1449h.yaml` — already generated locally.
  - **Do NOT re-create these files.** Just push, submit, pull, analyze.
- 2 criteria still ☐ open after §2.5 lands: §2.1 second predictor (AlphaFold3 Server / Chai-1) and §2.4 (Protein2PAM functional gap).
- HPC work was **blocked on 2026-05-16 by VPN setup** (user was off-campus and first-time-using-VPN). Expected to clear once user is back on campus network.

**Significant deck/docs work landed 2026-05-16 afternoon:**

- `docs/presentation/FnCas9_PLM_Redesign.pptx` is now **27 slides, 12 figures, 2.0 MB**. 5 new robustness-phase figures + 3 new slides (per-residue pLDDT trace, pairwise distance heatmap, 3D structural rendering on PDB 5B2O).
- New plan doc `notes/plans/2026-05-16_TIER1_MD_PROXY_PLAN.md` (Tier 1 = ~10 ns OpenMM relaxation of 6 systems including SpCas9 as baseline; ~3–6 GPU-days). **Optional and explicitly gated to AFTER §2.4 + §2.5 close.** Do not start unless user asks.

**Before doing anything else, read these for full context (in this order):**

1. The auto-memory `session_handoff_2026-05-16.md` (full state + gotchas; reflects end-of-2026-05-16-afternoon state).
2. `notes/worklog/2026-05-16_WORKLOG.md` (today's chronology — what was done locally, what was deferred).
3. `notes/worklog/2026-05-15_WORKLOG.md` (predecessor — has the MSA-Boltz, PLM4-reinstated, and ThermoMPNN-D results).
4. `notes/plans/2026-05-15_ROBUSTNESS_PLAN.md` (live roadmap; §6 is the "ready for the PI" gate).
5. `notes/plm/verification-log.md` last 3 sections (PLM4 direct Boltz / MSA-Boltz / ThermoMPNN-D epistasis).

**Today's work, in priority order:**

1. **§2.5 — push, submit, pull, analyze** (~30 min wall + ~10 min human; closes criterion 5):
   ```
   bash hpc/sync.sh push                          # mirrors the new sbatch + YAMLs
   ssh tejas                                       # password auth (no key registered)
     sbatch hpc/slurm/04c_boltz_e1449.sbatch
     squeue -u $USER                               # watch (job ID echo'd by sbatch)
     exit
   bash hpc/sync.sh pull                          # pull results when done
   PYTHONPATH=src .venv/bin/python scripts/boltz_analyze.py \
     --run-dir results/runs/YYYY-MM-DD_boltz_e1449
   ```
   Then record the falsifiable E1449L vs E1449H result (iPTM, prot↔DNA-PAM iPTM, per-residue pLDDT at position 1449, with σ across 5 samples) in `notes/plm/verification-log.md`. Flip §6 criterion 5 to ✅ in the robustness plan.

2. **§2.1 Chai-1 attempt on HPC** (closes criterion 1's second-predictor leg). Chai-1 has similar-to-larger memory needs than Boltz; may OOM on V100 32GB. Have a truncation fallback ready (existing WED+PI 1230–1620 is the first fallback; even tighter PI-only window is the second). Inputs: PLM5 / en31 / WT FASTAs (already in the project). This needs a NEW sbatch `hpc/slurm/06_chai1.sbatch` — write it following the pattern of `05_thermompnn_d.sbatch`.

3. **§2.4 Protein2PAM scan** (~10 min, web service at protein2pam.profluent.bio; closes criterion 2). Polyform-NC license cleared for academic use. Submit PLM5 / en31 / WT FASTAs; compare predicted PAM PWMs; record in `notes/plm/verification-log.md`.

4. **User browser task (parallel to compute)** — submit PLM5 / en31 / WT to **AlphaFold3 Server** (alphafoldserver.com). Confirms criterion 1's second-predictor leg from a fully independent source. Free academic access; ~few-min queue.

**Operational gotchas (don't re-discover):**

- **HPC SSH to tejas (CSIR-IGIB) is password-only** (no key registered). User runs `bash hpc/sync.sh push|pull` interactively each time.
- **VPN required if off-campus.** User figured this out on 2026-05-16 the hard way. On-campus = no VPN needed; off-campus = VPN.
- **`prepare_boltz_yamls.py` needs Python 3.10+** (uses `dataclass(slots=True)`). Use `.venv/bin/python` explicitly, NOT system `python3`.
- HPC `dgx` partition has a **~1.5h practical wall-time limit** despite SBATCH `--time=04:00:00`. Boltz at 5 samples on the truncated WED+PI takes ~10 min, so this is NOT a constraint for §2.5, but flag for any saturation-style or MD job.
- ThermoMPNN-D `additive.csv` (9.1 GB) at `results/runs/2026-05-15_thermompnn_d_hpc/` — don't load with pandas; use grep (see `scripts/thermompnn_d_epistasis_analyze.py`).
- PPT rebuild: `PYTHONPATH=src .venv/bin/python scripts/build_presentation.py` regenerates all 12 figures + 27 slides from scratch.
- Memory ecosystem: `project_context.md` = high-level state; `session_handoff_2026-05-16.md` = latest detailed snapshot. Read both at session start.

**Wet-lab handoff is the terminal step**, gated on all 5 criteria ✅. Don't pitch it as the next move — the user has stated this explicitly and durably (`feedback_robustness_before_wetlab` memory). After all 5 criteria pass, the PI conversation happens.

**Tier 1 MD-proxy** (`notes/plans/2026-05-16_TIER1_MD_PROXY_PLAN.md`) exists as an optional confidence-reinforcement step. Do NOT start it unless §2.4 + §2.5 are closed AND the user explicitly asks.

Start by reading the session_handoff memory + 2026-05-16 worklog + robustness plan, then propose the §2.5 push/submit as the first concrete step.
