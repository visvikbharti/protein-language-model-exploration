#!/usr/bin/env bash
#SBATCH --job-name=plm_smoke_test
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=logs/00_smoke_%j.out
#SBATCH --error=logs/00_smoke_%j.err

# GPU sanity check: verify nvidia-smi, PyTorch CUDA, and torch.cuda.is_available()
# on the dgx partition. Run before any Phase 3 work.
#
# Submit:   sbatch hpc/slurm/00_smoke_test_gpu.sbatch
# Watch:    squeue -u $USER
# Read:     cat logs/00_smoke_<jobid>.out

set -eo pipefail

mkdir -p logs

# Initialise the environment-modules system. SLURM jobs don't source ~/.bashrc
# so `module` isn't on PATH by default; we have to source the init script first.
# We also don't actually need a Python module on this cluster — the venv we
# created with miniconda's python3.11 is fully self-contained.
if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    source /usr/share/Modules/init/bash
fi
# The venv already pins python3.11.10 from miniconda; module load is optional.
# If `module` is available, purge anything we might inherit:
command -v module >/dev/null && module purge || true

cd /lustre/vishal.bharti/protein-language-model-exploration
source .venv-hpc/bin/activate

echo "===== Host & SLURM info ====="
echo "hostname:        $(hostname)"
echo "date:            $(date)"
echo "SLURM_JOB_ID:    $SLURM_JOB_ID"
echo "SLURM_NODELIST:  $SLURM_NODELIST"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-<unset>}"
echo

echo "===== nvidia-smi ====="
nvidia-smi || echo "(nvidia-smi not available on this node)"
echo

echo "===== Python & torch ====="
python --version
python -c "
import torch, sys
print(f'torch version:      {torch.__version__}')
print(f'torch CUDA built:   {torch.version.cuda}')
print(f'cuDNN:              {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else \"n/a\"}')
print(f'cuda available:     {torch.cuda.is_available()}')
print(f'device count:       {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    p = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {p.name}  cc={p.major}.{p.minor}  VRAM={p.total_memory/1e9:.1f}GB  multiproc={p.multi_processor_count}')
sys.exit(0)
"
echo

echo "===== Tiny CUDA tensor op ====="
python -c "
import torch
if not torch.cuda.is_available():
    raise SystemExit('CUDA not available')
x = torch.randn(1024, 1024, device='cuda')
y = x @ x.T
print(f'matmul output mean: {y.mean().item():.4f}, shape: {tuple(y.shape)}')
print('GPU smoke test PASSED')
"
echo

echo "===== Unit tests on the venv ====="
PYTHONPATH=src python -m pytest tests/ -q --no-header

echo
echo "===== Done ====="
