# Next-session priming prompt

Paste the block below as the first message in tomorrow's session. It gives Claude enough context to resume the robustness phase without re-deriving state.

---

Resuming the FnCas9 PLM-redesign project after a one-day pause. Today is the next robustness-phase work session.

**State at end of last session (2026-05-15 / 2026-05-16 early):**
- In-silico campaign is complete; recommended candidate is **FnCas9-PLM5** (Y1249F / Y1341L / A1325K / K1479F).
- Robustness phase is mid-flight. **3 of 5 "ready for the PI" criteria are ✅ DONE:**
  - ✅ §2.2 apo-ΔΔG filter bracketed (PLM4 reinstated, proteinmpnn_ddg known-miscalibrated for hydrophobic↔K).
  - ✅ §2.3 pairwise epistasis characterized (ThermoMPNN-D: PLM5's |Σ epistasis|/|Σ additive| = 0.019; en31's = 7.1×).
  - ✅ §2.1 partial (MSA-enabled Boltz across 5 variants — **PLM5 leads even en31**; still need a second predictor).
- 2 criteria still open: structural second-predictor agreement (§2.1), functional gap (§2.4), and the falsifiable E1449L/H prediction (§2.5).

**Before doing anything else, read these for full context (in this order):**
1. The auto-memory `session_handoff_2026-05-16.md` (it has the full state + gotchas).
2. `notes/plans/2026-05-15_ROBUSTNESS_PLAN.md` (live roadmap; §6 is the "ready for the PI" gate).
3. `notes/worklog/2026-05-15_WORKLOG.md` (chronological per-session log; latest entry is the §2.3 epistasis section).
4. `notes/plm/verification-log.md` last 3 sections (PLM4 direct Boltz / MSA Boltz / ThermoMPNN-D epistasis).

**Today's work, in priority order:**

1. **§2.5 — single-point E1449L vs E1449H Boltz** (~0.5 hr V100; closes criterion 5).
   - Add `fncas9_e1449l` and `fncas9_e1449h` to the variants dict in `scripts/prepare_boltz_yamls.py` (single mutants on WT backbone, WED+PI truncation 1230–1620).
   - Run `.venv/bin/python scripts/prepare_boltz_yamls.py` to regenerate YAMLs.
   - `bash hpc/sync.sh push`, then on HPC: `sbatch hpc/slurm/04_boltz_complex.sbatch` (will pick up the new YAMLs).
   - When done: `bash hpc/sync.sh pull`, then `.venv/bin/python scripts/boltz_analyze.py` on the new run dir.
   - Record the result in `notes/plm/verification-log.md` as the falsifiable E1449L/H claim with CI.

2. **§2.1 — Chai-1 attempt on HPC** (closes criterion 1's second-predictor leg).
   - Chai-1 has similar-to-larger memory needs than Boltz; may OOM on V100 32GB. Have a truncation fallback ready (the existing WED+PI 1230–1620 truncation is the first fallback; an even tighter PI-only window is the second).
   - Inputs: PLM5 / en31 / WT FASTAs (already in the project).
   - This may need a new sbatch (`hpc/slurm/06_chai1.sbatch`) — write it following the pattern of `05_thermompnn_d.sbatch`.

3. **§2.4 — Protein2PAM scan** (~10 min, web service; closes criterion 2).
   - Free at protein2pam.profluent.bio (Polyform-NC cleared for academic use; Nayfach et al. *Nat Biotechnol* 2026).
   - Submit PLM5 / en31 / WT FASTAs; record predicted PAM PWMs in `notes/plm/verification-log.md`.

4. **User browser task** (parallel to compute work — please do this in a browser tab independent of the Claude session):
   - Submit PLM5 / en31 / WT to **AlphaFold3 Server** (alphafoldserver.com). Confirms criterion 1's second-predictor leg from a fully independent source. Free academic access; ~few-min queue.

**Operational gotchas (don't re-discover):**
- HPC SSH to tejas (CSIR-IGIB) is **password-only** (no key registered). The user runs `bash hpc/sync.sh push|pull` interactively each time.
- **`prepare_boltz_yamls.py` needs Python 3.10+** — use `.venv/bin/python` explicitly, not system `python3`.
- HPC `dgx` partition has a **~1.5h practical wall-time limit** despite SBATCH `--time=04:00:00`. Boltz at 5 samples on the truncated WED+PI takes ~10 min, so this is not a constraint for §2.5, but flag for any saturation-style job.
- The 9.1 GB `results/runs/2026-05-15_thermompnn_d_hpc/additive.csv` exists locally — don't try to load with pandas if you need to look anything up. Use grep (see `scripts/thermompnn_d_epistasis_analyze.py` for the pattern).
- Memory ecosystem: `project_context.md` is the high-level state; `session_handoff_2026-05-16.md` is the most recent detailed snapshot. Read both at session start.

**Wet-lab handoff is the terminal step**, gated on all 5 criteria ✅. Don't pitch it as the next move — the user has stated this explicitly. After all 5 criteria pass, the PI conversation happens.

Start by reading the session_handoff_2026-05-16 memory + the robustness plan, then propose the §2.5 implementation as the first concrete step.
