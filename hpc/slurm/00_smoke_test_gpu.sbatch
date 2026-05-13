#!/bin/bash
#SBATCH --job-name=plm_smoke_test
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=logs/00_smoke_%j.out
#SBATCH --error=logs/00_smoke_%j.err

# Phase 0 smoke test — written defensively because the dgx compute node on
# this cluster ships with a minimal/empty PATH. Every command up to the
# `export PATH` line uses an absolute path; after the export, normal PATH
# resolution works.

# --- Bootstrap PATH ----------------------------------------------------------
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}

# --- Diagnostic prologue -----------------------------------------------------
# These tell us, at minimum, what's available on the dgx compute node.
/bin/echo "===== Environment dump ====="
/bin/echo "PATH=$PATH"
/bin/echo "HOSTNAME=$(/bin/hostname 2>/dev/null || echo unknown)"
/bin/echo "PWD=$PWD"
/bin/echo "USER=$USER"
/bin/echo "SLURM_JOB_ID=$SLURM_JOB_ID"
/bin/echo "SLURM_NODELIST=$SLURM_NODELIST"
/bin/echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
/bin/echo

/bin/echo "===== /bin contents (first 30) ====="
/bin/ls /bin 2>/dev/null | /usr/bin/head -30 || /bin/echo "(no /bin)"
/bin/echo
/bin/echo "===== Binary locations ====="
for cmd in bash mkdir cat python python3 nvidia-smi nvcc which; do
    found=$(/usr/bin/which "$cmd" 2>/dev/null || /bin/echo "(not found)")
    /bin/echo "  $cmd -> $found"
done
/bin/echo

# --- Strict mode after the diagnostic dump (so failures still leave a log) ---
set -eo pipefail

# --- Modules system (optional) ----------------------------------------------
if [ -f /etc/profile.d/modules.sh ]; then
    . /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    . /usr/share/Modules/init/bash
fi
command -v module >/dev/null 2>&1 && module purge || true

# --- Project directory + venv ------------------------------------------------
cd /lustre/vishal.bharti/protein-language-model-exploration
mkdir -p logs

if [ ! -f .venv-hpc/bin/activate ]; then
    /bin/echo "[ERROR] .venv-hpc/bin/activate not found. Run hpc/env/setup_env.sh first."
    exit 1
fi
. .venv-hpc/bin/activate
/bin/echo "Python:  $(which python)"
/bin/echo "version: $(python --version)"
/bin/echo

# --- GPU sanity check --------------------------------------------------------
/bin/echo "===== nvidia-smi ====="
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi
else
    /bin/echo "(nvidia-smi not on PATH — checking known absolute paths)"
    for p in /usr/bin/nvidia-smi /usr/local/cuda/bin/nvidia-smi /opt/nvidia/nvidia-smi; do
        [ -x "$p" ] && { /bin/echo "found: $p"; "$p"; break; }
    done
fi
/bin/echo

/bin/echo "===== Python + torch ====="
python -c "
import sys, torch
print(f'python:           {sys.version.split()[0]}')
print(f'torch version:    {torch.__version__}')
print(f'torch CUDA built: {torch.version.cuda}')
print(f'cuDNN:            {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else \"n/a\"}')
print(f'cuda available:   {torch.cuda.is_available()}')
print(f'device count:     {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    p = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {p.name}  cc={p.major}.{p.minor}  VRAM={p.total_memory/1e9:.1f}GB  SMs={p.multi_processor_count}')
"
/bin/echo

/bin/echo "===== Tiny CUDA matmul ====="
python -c "
import torch
if not torch.cuda.is_available():
    raise SystemExit('CUDA NOT AVAILABLE — GPU job on a non-GPU node?')
x = torch.randn(1024, 1024, device='cuda')
y = x @ x.T
print(f'matmul shape: {tuple(y.shape)}, mean={y.mean().item():.4f}')
print('GPU smoke test PASSED')
"
/bin/echo

/bin/echo "===== Unit tests ====="
PYTHONPATH=src python -m pytest tests/ -q --no-header

/bin/echo
/bin/echo "===== Done ====="
