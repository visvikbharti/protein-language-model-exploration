#!/usr/bin/env bash
# One-time HPC environment setup.
#
# Creates .venv-hpc/ in the project root with all dependencies needed for the
# Phase 3 SLURM jobs. Uses the cluster's python-3.12.2 module (NOT the broken
# anaconda base).
#
# Run from project root:
#     module load python-3.12.2
#     bash hpc/env/setup_env.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

VENV=".venv-hpc"

if [[ -d "$VENV" ]]; then
    echo "[setup] $VENV already exists. Delete it first to recreate."
    exit 1
fi

echo "[setup] Python: $(python3 --version), $(which python3)"

echo "[setup] Creating venv: $VENV"
python3 -m venv "$VENV"

# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --upgrade pip wheel

echo "[setup] Installing numpy first (avoid building from source later)..."
# Install numpy from PyPI explicitly with a version pin compatible with everything.
# numpy 2.x has wheels for cp311; pinning <2.3 keeps compatibility with fair-esm
# and older transformers if they happen to need it.
pip install "numpy>=1.26,<2.3"

echo "[setup] Installing PyTorch with CUDA 11.8 (V100-compatible)..."
# CUDA 11.8 wheels are the safest for V100 — V100 has compute capability 7.0 which
# is supported by all PyTorch 2.x builds. We use --extra-index-url (not --index-url)
# so PyPI remains available for dependencies like numpy, sympy, etc. that PyTorch's
# wheel index doesn't host.
pip install --extra-index-url https://download.pytorch.org/whl/cu118 \
    "torch>=2.1,<2.5" \
    "torchvision>=0.16" \
    "torchaudio>=2.1"

echo "[setup] Installing protein ML stack..."
pip install \
    "numpy>=1.26" \
    "scipy>=1.11" \
    "pandas>=2.1" \
    "pyarrow>=14" \
    "pydantic>=2.5" \
    "pyyaml>=6" \
    "biotite>=0.40" \
    "biopython>=1.83" \
    "transformers>=4.40" \
    "accelerate>=0.30" \
    "fair-esm>=2.0.1" \
    "matplotlib>=3.8" \
    "seaborn>=0.13" \
    "tqdm>=4.66" \
    "click>=8.1" \
    "rich>=13.7" \
    "pytest>=8.0" \
    "ipykernel>=6.29"

echo "[setup] Installing the project itself in editable mode..."
pip install -e .

echo "[setup] Verifying GPU access:"
python -c "
import torch
print(f'torch:    {torch.__version__}')
print(f'cuda built: {torch.version.cuda}')
print(f'cuda available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f'  GPU {i}: {p.name}  compute_capability={p.major}.{p.minor}  VRAM={p.total_memory/1e9:.1f}GB')
"

echo "[setup] Running unit tests:"
PYTHONPATH=src python -m pytest tests/ -q --no-header

echo
echo "[setup] Done. To activate later:"
echo "  cd $PROJECT_ROOT && source $VENV/bin/activate"
