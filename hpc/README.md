# Deploying Phase 3 on CSIR-IGIB Tejas HPC

**Cluster:** `tejas.igib.res.in`
**User:** `vishal.bharti`
**Working tree on HPC:** `/lustre/vishal.bharti/protein-language-model-exploration/` (rsync target)
**GPU partition:** `dgx` (1 node `igib-dgx`, 8× V100 32 GB, 80 CPU cores, 500 GB RAM)
**Scheduler:** SLURM 20.11.5

## What this directory contains

```
hpc/
├── README.md                          # this file
├── env/
│   ├── setup_env.sh                   # bootstrap a Python 3.12 venv on /lustre with all PLM deps
│   └── requirements_hpc.txt           # exact pinned deps for the HPC env
├── slurm/
│   ├── 00_smoke_test_gpu.sbatch       # `nvidia-smi` + torch.cuda.is_available() sanity check
│   ├── 01_esm2_650m_full_PI.sbatch    # full PI-domain saturation with ESM-2 650M (CPU job, ~30 min)
│   ├── 02_ligandmpnn_sampling.sbatch  # LigandMPNN on FnCas9 + sgRNA + DNA (1× V100, ~1-2 hr)
│   ├── 03_proteinmpnn_ddg.sbatch      # stability filter on top candidates (1× V100, ~30 min)
│   └── 04_boltz_complex.sbatch        # Boltz-2 complex prediction (1× V100, ~30 min, domain-only)
├── inputs/
│   └── README.md                      # what to place here before each job
└── sync.sh                            # rsync helper: Mac → HPC and back
```

## Deployment flow

```
[Mac local dev]              [HPC tejas]
       │                          │
       ├── rsync code/data ────►  │  /lustre/vishal.bharti/protein-language-model-exploration/
       │                          │
       │                          ├── module load python-3.12.2
       │                          ├── source hpc/env/setup_env.sh   (once)
       │                          │
       │                          ├── sbatch hpc/slurm/00_smoke_test_gpu.sbatch
       │                          ├── sbatch hpc/slurm/02_ligandmpnn_sampling.sbatch
       │                          │   ...
       │                          │
       │  ◄── rsync results ──────┤
       │                          │
```

## Step-by-step (first time)

### 1. Initial rsync from Mac
```bash
# On Mac, from the project root:
bash hpc/sync.sh push
# Pushes the working tree (code, scripts, notes, results, hpc/) to:
# vishal.bharti@tejas.igib.res.in:/lustre/vishal.bharti/protein-language-model-exploration/
```

### 2. Set up the HPC Python environment (one-time, ~10 minutes)
```bash
# On HPC:
ssh vishal.bharti@tejas.igib.res.in
cd /lustre/vishal.bharti/protein-language-model-exploration
module load python-3.12.2
bash hpc/env/setup_env.sh
# Creates .venv-hpc/ with torch+CUDA, fair-esm, biopython, biotite, etc.
```

### 3. Sanity check the GPU
```bash
sbatch hpc/slurm/00_smoke_test_gpu.sbatch
# Wait ~1 minute, then check the .out file:
squeue -u $USER
cat slurm-<jobid>.out
```

Expected: `nvidia-smi` listing 1× V100, PyTorch reporting `cuda available: True`, CUDA version reported.

### 4. Run the Phase 3 jobs (in dependency order)
```bash
# Each `sbatch` returns a job ID. Use --dependency=afterok:<jobid> to chain.
JID1=$(sbatch --parsable hpc/slurm/01_esm2_650m_full_PI.sbatch)
JID2=$(sbatch --parsable --dependency=afterok:$JID1 hpc/slurm/02_ligandmpnn_sampling.sbatch)
JID3=$(sbatch --parsable --dependency=afterok:$JID2 hpc/slurm/03_proteinmpnn_ddg.sbatch)
JID4=$(sbatch --parsable --dependency=afterok:$JID3 hpc/slurm/04_boltz_complex.sbatch)
```

### 5. Pull results back to the Mac
```bash
# Once the chain finishes:
bash hpc/sync.sh pull
# Brings new files in results/runs/ back to local for further analysis.
```

## Why the conda base is broken (FYI)

The `(base)` env on login shows `libarchive.so.20: cannot open shared object file`. That's the `conda-libmamba-solver` plugin missing a system library. We side-step this entirely by using **a fresh Python venv from `module load python-3.12.2`** instead of conda. No reliance on the cluster's anaconda.

## Why V100 changes the plan vs an A100/H100

| Concern | V100 behaviour | Mitigation |
|---|---|---|
| No bfloat16 hardware | Boltz/Chai default to bfloat16 — fall back to fp16 | Test fp16; if OOM, predict only the PI domain (~400 aa) instead of full FnCas9 (1629 aa) |
| 32 GB VRAM | Tight for Boltz-2 on a 1700-residue complex | Reduce input length; use smaller Boltz model variant if available |
| No FlashAttention-2 | Some Evo / xFormers paths slower | Acceptable — we're not running Evo 2 in Phase 3 |
| Older PCIe | Slower CPU-GPU transfer | Negligible for our batch-style inference |

ESM-2 650M, LigandMPNN, ProteinMPNN, RFdiffusion all run comfortably on V100 32 GB.

## SLURM quirks specific to this cluster

1. **`srun --pty bash` fails** with `execve(): bash: No such file or directory`. Use `sbatch` instead, or pass `--export=ALL` + explicit shell. See `00_smoke_test_gpu.sbatch` for the working pattern.
2. **No `cuda` module** — PyTorch wheels carry their own CUDA runtime, which is what we use. The system NVIDIA driver provides CUDA capability.
3. **`pycuda` module exists** — but we don't need it; PyTorch handles all GPU access.
4. **Lustre filesystem** — write batch outputs there, not to /tmp. Large weight files (ESM-2 650M is 2.4 GB; Boltz weights ~5 GB) go in `/lustre/vishal.bharti/.cache/torch/hub/`.
