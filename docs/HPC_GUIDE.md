# HPC operations and reproducibility guide

**Purpose:** end-to-end operational playbook for re-running every phase of this campaign on CSIR-IGIB *tejas* (or another SLURM cluster). Every command verified against the actual runs from 2026-05-13.

**Companion to:** `docs/PROJECT_OVERVIEW.md`, `docs/methods.md`, `docs/reproducibility.md`.

---

## 1. Cluster facts

- **Cluster name:** tejas (CSIR-IGIB)
- **Login node:** `vishal.bharti@tejas.igib.res.in` (head node `hn1`)
- **Compute partition:** `dgx` (1× DGX server with 8× V100-SXM2-32GB)
- **Scheduler:** SLURM
- **Working directory:** `/lustre/vishal.bharti/protein-language-model-exploration/` (Lustre shared filesystem; visible to both hn1 and the dgx compute nodes)
- **Environment:** `module load singularity-3.7.4` for container work; Python venv at `.venv-hpc/` for native Python work

---

## 2. Environment setup (first-time only)

### 2.1 Clone the repo onto Lustre

```bash
ssh vishal.bharti@tejas.igib.res.in
cd /lustre/vishal.bharti
git clone https://github.com/visvikbharti/protein-language-model-exploration.git
cd protein-language-model-exploration
```

### 2.2 Build the Python virtual environment

```bash
bash hpc/env/setup_env.sh
```

This script:
- Loads the `python-3.11` module if available, otherwise uses the system `python3.11`.
- Creates `.venv-hpc/` with `python3.11 -m venv`.
- Installs numpy first (avoids the PyTorch index clobbering numpy resolution).
- Installs PyTorch from `https://download.pytorch.org/whl/cu118` (V100 needs CUDA 11.x compatible wheels).
- Installs the rest of the project requirements with `--prefer-binary` (avoids source builds requiring GCC ≥ 9.3, since IGIB's GCC is 8.4).

Pinned versions of note:
- `scipy >= 1.11, < 1.17`
- `pandas >= 2.1, < 2.3`
- `pyarrow >= 14, < 20`
- `fair-esm >= 2.0.0`

### 2.3 Verify with the smoke test

```bash
sbatch hpc/slurm/00_smoke_test_gpu.sbatch
sleep 30
squeue -u $USER
tail -n 50 logs/00_smoke_test_*.out
```

Expected output: 42 tests passed, 1 skipped, V100-SXM2-32GB detected, CUDA 12.2 driver.

If you see PATH errors (`mkdir: command not found`), the dgx node has an empty PATH for SLURM jobs — this is bootstrapped at the top of every sbatch via:

```bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}
```

---

## 3. Sync workflow (Mac ↔ HPC)

The repo lives canonically in git, but during active development you'll often want to sync local edits to HPC without committing intermediate states.

```bash
# On Mac
bash hpc/sync.sh push   # rsync Mac → HPC
bash hpc/sync.sh pull   # rsync HPC → Mac (for results)
```

`hpc/sync.sh` is configured with appropriate excludes (`.git/`, `.venv*/`, `__pycache__/`, `results/runs/*_FAILED*` etc.). Read the script for details.

**Recommended workflow:**
1. Edit code on Mac.
2. Commit + push to GitHub (so the change is canonical).
3. `bash hpc/sync.sh push` on Mac to mirror to HPC.
4. Run on HPC.
5. `bash hpc/sync.sh pull` on Mac to bring results back for analysis.

If you ever modify code on HPC directly, immediately copy it back to Mac for commit. Do NOT let the HPC working copy diverge from git.

---

## 4. Phase-by-phase commands

### Phase 1: Smoke test (validate environment)

```bash
sbatch hpc/slurm/00_smoke_test_gpu.sbatch
# wait for completion (~2 min)
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed
```

### Phase 2: ESM-2 zero-shot scan

```bash
sbatch hpc/slurm/01_esm2_650m_full_PI.sbatch
JOBID=$(squeue -h -u $USER -n esm2_650m_PI -o "%i")
# Wall time: ~3 minutes on V100. The full 7,429-variant scan.

# After completion:
ls results/runs/2026-05-13_esm2_650M_full_PI_hpc/
# Expected: scores.tsv (~270 KB), meta.json
```

To build the PLM3 candidate from the scan output:

```bash
SCAN_DIR=$(ls -1d results/runs/*_esm2_650M_full_PI_hpc | tail -1)
PYTHONPATH=src python scripts/build_candidate_v3.py \
    --scores "$SCAN_DIR/scores.tsv" \
    --top-k 4 \
    --max-class-conservation 0.5 \
    --min-spacing 5
# Outputs to results/runs/<UTC-date>_candidates_v3/
```

### Phase 3: LigandMPNN sampling

```bash
sbatch hpc/slurm/02_ligandmpnn_sampling.sbatch
JOBID=$(squeue -h -u $USER -n ligandmpnn -o "%i")
# Wall time: ~28 min on V100 for 4,800 samples (3 temperatures × 1,600).
# First-time setup additionally clones LigandMPNN and downloads ~50 MB of weights.

# Sanity-check 30 sec into the run:
sleep 30 && grep "Design residues" logs/02_ligandmpnn_${JOBID}.out
# Expected: "Design residues: 391 tokens (first=A1230, last=A1620)"
# If you see "0 tokens" or no line, the residue list got mangled — see Section 7 below.

# After completion, verify the samples are diverse:
for t in T0.1 T0.2 T0.3; do
    n=$(grep -v '^>' results/runs/*_ligandmpnn_PI/$t/seqs/5B2O.fa | sort -u | wc -l)
    echo "$t: $n unique"
done
# Expected: each ≈ 1,601 (1 reference + 1,600 distinct samples)
# If all = 1, design didn't happen — see Section 7.
```

Aggregate the samples:

```bash
PYTHONPATH=src python scripts/ligandmpnn_aggregate.py \
    --run-dir results/runs/2026-05-13_ligandmpnn_PI
```

Build PLM4:

```bash
PYTHONPATH=src python scripts/build_candidate_v4.py \
    --aggregate results/runs/2026-05-13_ligandmpnn_PI/aggregate.tsv \
    --top-k 4 \
    --min-top-freq 0.30 \
    --max-wt-freq 0.40 \
    --max-class-conservation 0.5
```

### Phase 4: ProteinMPNN-DDG apo stability

```bash
sbatch hpc/slurm/03_proteinmpnn_ddg.sbatch
# First run: ~8 min for Singularity image pull + ~30 sec compute.
# Subsequent runs: ~30 sec total (image cached).

# Analyzer:
DDG_DIR=$(ls -1d results/runs/*_proteinmpnn_ddg | grep -v FAILED | tail -1)
PYTHONPATH=src python scripts/proteinmpnn_ddg_analyze.py --ddg "$DDG_DIR/ddg.csv"
```

Build PLM5 with the ΔΔG gate:

```bash
PYTHONPATH=src python scripts/build_candidate_v4.py \
    --aggregate results/runs/2026-05-13_ligandmpnn_PI/aggregate.tsv \
    --ddg-csv "$DDG_DIR/ddg.csv" \
    --max-single-ddg 3.2 \
    --candidate-name FnCas9-PLM5 \
    --output-dir results/runs/$(date -u +%Y-%m-%d)_candidates_v5
```

### Phase 5: Boltz-2 complex prediction

```bash
PYTHONPATH=src python scripts/prepare_boltz_yamls.py
# Writes hpc/inputs/boltz_fncas9_{wt,plm3,plm5,en31}.yaml

sbatch hpc/slurm/04_boltz_complex.sbatch
JOBID=$(squeue -h -u $USER -n boltz_complex -o "%i")
# Wall time: ~2-4 hours total (~30-60 min per variant on V100).
# First-time setup: ~5 min to pip-install boltz (which downgrades numpy/scipy
# in the venv — see Section 7).

# Monitor:
sleep 60 && tail -n 30 logs/04_boltz_${JOBID}.out
squeue -u $USER
sacct -j $JOBID --format=JobID,State,ExitCode,Elapsed
```

Outputs land in `results/runs/<UTC-date>_boltz_complex/fncas9_<variant>/predictions/*.cif`.

---

## 5. Standard SLURM idioms used in all sbatches

Every sbatch in `hpc/slurm/` follows a common pattern. If you're writing a new one, mimic these:

### PATH bootstrap (line 1 after `#SBATCH` block)

```bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}
```

Why: dgx compute nodes start with an empty PATH for SLURM jobs. Without this, `mkdir`, `echo`, and many other tools fail with "command not found" → exit 127.

### Module init

```bash
if [ -f /etc/profile.d/modules.sh ]; then
    . /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    . /usr/share/Modules/init/bash
fi
command -v module >/dev/null 2>&1 && module purge || true
```

SLURM jobs don't source `~/.bashrc`, so the modules system needs to be initialized manually.

### Lustre directory + venv

```bash
cd /lustre/vishal.bharti/protein-language-model-exploration
. .venv-hpc/bin/activate
```

POSIX `.` is portable; `source` is bash-only.

### Output directory pattern

```bash
DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_<description>"
mkdir -p "$OUTPUT_DIR"
```

UTC date so directory names don't shift across local-timezone boundaries.

---

## 6. Useful one-liners

```bash
# Latest run dir for a given pattern
ls -1d results/runs/*_esm2_650M_full_PI_hpc 2>/dev/null | tail -1

# Watch a running job's log
tail -f logs/0?_*_${JOBID}.out logs/0?_*_${JOBID}.err

# Find the JOBID of your most recent submission
squeue -h -u $USER -o "%i %j %T %M" | head -1

# Job history with timings
sacct -u $USER --starttime $(date -d 'yesterday' +%F) \
    --format=JobID%-15,JobName%-22,State%-12,Elapsed,ExitCode

# Disk usage of run results
du -sh results/runs/*/ 2>/dev/null | sort -h | tail -10

# Quickly see which variants got predictions in a Boltz run
ls results/runs/*_boltz_complex/*/predictions/*.cif 2>/dev/null | \
    awk -F/ '{print $4}' | sort -u
```

---

## 7. Known failure modes and recovery

### LigandMPNN's residue list silently rejected

**Symptom:** job 214059 completed in 28 min wall, exit 0:0, but every sample sequence was identical (`sort -u | wc -l = 1` per temperature). All FASTA headers showed `seq_rec=nan`.

**Root cause:** `--redesigned_residues "A1230-A1620"` (range syntax) is silently rejected by LigandMPNN's CLI; the tool runs in score-only mode with 0 designed positions.

**Fix:** generate the space-separated token list at runtime:

```bash
DESIGN_RESIDUES=$(python3 -c "print(' '.join(f'A{i}' for i in range(1230, 1621)))")
```

Already applied in the current sbatch. The first 30 sec of the log will print `Design residues: 391 tokens (first=A1230, last=A1620)` — if you see 0 or no line, this fix has regressed.

### LigandMPNN openfold breaks on NumPy 2.x

**Symptom:** `AttributeError: module 'numpy' has no attribute 'int'.` during import of `openfold.np.residue_constants`.

**Root cause:** LigandMPNN vendors an older copy of openfold that uses `np.int`, `np.float`, `np.bool` etc. — all removed in NumPy 1.24+. Our venv has NumPy 2.2.6.

**Fix:** in-place sed-rewrite of the vendored openfold (sentinel-guarded so it runs once per clone):

```bash
find external/LigandMPNN/openfold -name '*.py' -exec sed -i -E \
    -e 's/\bnp\.int\b/int/g' \
    -e 's/\bnp\.float\b/float/g' \
    -e 's/\bnp\.bool\b/bool/g' \
    -e 's/\bnp\.object\b/object/g' \
    -e 's/\bnp\.str\b/str/g' \
    -e 's/\bnp\.long\b/int/g' \
    -e 's/\bnp\.unicode\b/str/g' \
    {} +
```

Already applied in the current sbatch.

### LigandMPNN requirements.txt clobbers torch/numpy/scipy

**Symptom:** running `pip install -r external/LigandMPNN/requirements.txt` uninstalls the cu118 PyTorch and installs torch==2.2.1 (cu12), numpy 1.23.5, scipy 1.12.0. Everything subsequently breaks.

**Fix:** install only the LigandMPNN-specific Python packages (ProDy, ml-collections, dm-tree), not the full requirements.txt:

```bash
pip install --prefer-binary 'ProDy>=2.4,<3' 'ml-collections>=0.1.1' 'dm-tree>=0.1.8'
```

Already applied.

### proteinmpnn_ddg container CLI mismatch

**Symptom:** `/usr/local/bin/_entrypoint.sh: line 24: exec: predict.py: not found` → exit 127.

**Root cause:** the peptoneltd container is distroless (no shell, no `cat`, no `ls`); the entrypoint expects `python3 /app/proteinmpnn_ddg/predict.py` with `--pdb_path` / `--chains` / `--outpath` flag names. Our initial sbatch used the wrong invocation.

**Fix:**

```bash
singularity run --nv \
    --bind "$PWD:/workspace" --pwd /workspace \
    "$SIF" \
    python3 /app/proteinmpnn_ddg/predict.py \
        --pdb_path "$INPUT_PDB" \
        --chains A \
        --outpath "$OUTPUT_DIR/ddg.csv" \
        --seed 42 \
        --model_name v_48_020
```

Already applied.

### Boltz pip-install downgrades the venv

**Symptom:** running `04_boltz_complex.sbatch` for the first time uninstalls numpy 2.2.6, scipy 1.16.3, dm-tree, requests, pyyaml, click — replacing them with Boltz's pinned versions.

**Impact:** post-Boltz reruns of the ESM-2 or LigandMPNN scripts may fail if any of those tools need newer numpy/scipy than what Boltz installed.

**Recovery if it breaks ESM-2 reruns:**

```bash
# Restore the numpy/scipy versions our other scripts need
pip install --upgrade --force-reinstall "numpy<3,>=2.0" "scipy>=1.16"
```

A cleaner long-term fix is a separate `.venv-boltz` for Boltz only. Not yet done as of 2026-05-13.

### dgx node has no `bash` on PATH

**Symptom:** `/usr/bin/env: 'bash': No such file or directory` at job start.

**Fix:** use `#!/bin/bash` shebang (absolute path), not `#!/usr/bin/env bash`. All current sbatches do this.

---

## 8. Verifying a fresh clone reproduces our results

If you (or a collaborator) start from a fresh clone and need to verify everything works:

```bash
# 1. Smoke test — 2 min
sbatch hpc/slurm/00_smoke_test_gpu.sbatch
# Wait, check it passed

# 2. ESM-2 scan — 3 min
sbatch hpc/slurm/01_esm2_650m_full_PI.sbatch
# Wait, check the rank-1 mutation in the output is G1243T (LLR > +4)

# 3. ProteinMPNN-DDG — 30 sec (after container pull)
sbatch hpc/slurm/03_proteinmpnn_ddg.sbatch
# Wait, check the output CSV has columns pre,post,pos,...,logit_difference_ddg

# 4. LigandMPNN — 28 min
sbatch hpc/slurm/02_ligandmpnn_sampling.sbatch
# Wait, check unique-sequence counts per temperature are ~1,601

# 5. Aggregate + build candidates
PYTHONPATH=src python scripts/ligandmpnn_aggregate.py \
    --run-dir results/runs/$(date -u +%Y-%m-%d)_ligandmpnn_PI
# Expected output table for the en31/en15 reference positions should match
# the data in notes/plm/verification-log.md (modulo random seed differences
# in the LigandMPNN sampling: G1243T target_freq ≈ 0.45, E1369R top is K)

# 6. Boltz — 2-4 hours
sbatch hpc/slurm/04_boltz_complex.sbatch
```

The only step that may vary across runs is LigandMPNN sampling (autoregressive sampling at finite temperature → some variability in per-position frequencies). Expect the qualitative findings to hold: G1243T recoverable, E1369R top non-WT is K, E1449H and E1603H top is L.

---

## 9. Storage budget and cleanup

| Path | Size | Notes |
|------|------|-------|
| `external/LigandMPNN/` | ~120 MB | Mostly model weights |
| `external/proteinmpnn_ddg/` | ~3 GB | Singularity SIF |
| `.venv-hpc/` | ~3 GB | Python venv with PyTorch, ESM, Boltz |
| `data/raw/` | ~10 MB | FASTAs and 5B2O PDB |
| `results/runs/*_esm2_*_hpc/` | ~300 KB per run | TSV + meta.json |
| `results/runs/*_ligandmpnn_*/` | ~30 MB per run | 3 FASTAs + packed PDBs + stats |
| `results/runs/*_proteinmpnn_ddg/` | ~1 MB per run | CSV |
| `results/runs/*_boltz_complex/` | ~500 MB per run | mmCIF predictions for 4 variants × 5 samples |

Cleanup recommendations:

```bash
# Remove failed-run directories (preserved with _FAILED_ suffix)
rm -rf results/runs/*_FAILED_*/

# Remove the Boltz packed/ subdirs which we don't currently use
rm -rf results/runs/*_ligandmpnn_PI/T*/packed/

# Compress old run results before archiving
tar czf results/runs/2026-05-13_ligandmpnn_PI.tar.gz \
    --exclude='*/backbones/*' \
    results/runs/2026-05-13_ligandmpnn_PI/
```

---

## 10. Contacts and accounts

- **HPC support:** CSIR-IGIB IT support (via institutional channels)
- **Project lead / PI:** (TBD — fill in)
- **Author:** Vishal Bharti <vishalvikashbharti@gmail.com>
- **GitHub:** [`visvikbharti/protein-language-model-exploration`](https://github.com/visvikbharti/protein-language-model-exploration)
- **Cluster account:** `vishal.bharti`, common partition, dgx access

Daily compute is on the shared dgx partition. Long-running jobs (>4 hours) should be coordinated with other partition users.
