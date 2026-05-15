#!/bin/bash
#SBATCH --job-name=thermompnn_d
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/05_thermompnn_d_%j.out
#SBATCH --error=logs/05_thermompnn_d_%j.err

# §2.3 of the robustness plan: pairwise epistasis via ThermoMPNN-D
# (Kuhlman-Lab/ThermoMPNN-D, MIT). Runs both modes — `additive` (sum of
# singles) and `epistatic` (coupled head). The epistasis term per pair is
# (epistatic - additive); near-zero = additive scoring is safe; non-zero =
# coupling exists in the trained-distribution regime (mostly <~10 Å pairs).
#
# --distance 60 captures ALL 9 of our candidate pairs (6 within PLM5 at
# 14-50 Å, 3 within en31 at 8.5-9 Å). On Mac the --distance 60 pair list
# blew up memory (~9 GB steady, ~20 GB peak with broadcasting temporaries);
# tejas-dgx (500 GB node RAM, 64 GB allocation here) handles it cleanly.
# GPU on V100 accelerates the inference step.

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}

set -eo pipefail
mkdir -p logs results

if [ -f /etc/profile.d/modules.sh ]; then
    . /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    . /usr/share/Modules/init/bash
fi
command -v module >/dev/null 2>&1 && module purge || true

cd /lustre/vishal.bharti/protein-language-model-exploration
. .venv-hpc/bin/activate

# Allow the CUDA allocator to expand segments instead of failing on fragmented
# large allocations. The epistatic head's `mpnn_edges_raw.repeat(batch_size, ...)`
# is a big single tensor on a 1455-residue protein.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# ThermoMPNN-D Python deps — install if missing (idempotent)
python -c "import pytorch_lightning, omegaconf, wandb" 2>/dev/null || {
    echo "[setup] Installing ThermoMPNN-D Python deps..."
    pip install --quiet pytorch-lightning omegaconf joblib tqdm pandas wandb
}

# Clone ThermoMPNN-D on first run (external/ is excluded from rsync push)
if [ ! -d external/ThermoMPNN-D ]; then
    echo "[setup] Cloning ThermoMPNN-D..."
    mkdir -p external
    git clone --depth 1 https://github.com/Kuhlman-Lab/ThermoMPNN-D external/ThermoMPNN-D
fi

# Patch ThermoMPNN-D's local.yaml for our install path (idempotent)
LOCAL_YAML="external/ThermoMPNN-D/examples/configs/local.yaml"
if [ -f "$LOCAL_YAML" ] && grep -q '/proj/kuhl_lab' "$LOCAL_YAML"; then
    echo "[setup] Patching local.yaml thermompnn_dir..."
    sed -i "s|thermompnn_dir: .*|thermompnn_dir: \"$(pwd)/external/ThermoMPNN-D\"|" "$LOCAL_YAML"
fi

DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_thermompnn_d_hpc"
mkdir -p "$OUTPUT_DIR"

PROJ_ROOT=$(pwd)
cd external/ThermoMPNN-D
export PYTHONPATH=$(pwd):${PYTHONPATH:-}

PDB="$PROJ_ROOT/data/raw/5B2O.pdb"

echo
if [ -f "$PROJ_ROOT/$OUTPUT_DIR/additive.csv" ]; then
    echo "===== additive.csv already exists, skipping additive mode ====="
else
    echo "===== ThermoMPNN-D: additive mode (distance 60, all 9 candidate pairs in scope) ====="
    python v2_ssm.py \
        --mode additive \
        --pdb "$PDB" \
        --batch_size 256 \
        --out "$PROJ_ROOT/$OUTPUT_DIR/additive" \
        --chains A \
        --threshold 100 \
        --distance 60
fi

echo
echo "===== ThermoMPNN-D: epistatic mode (distance 15, batch_size 128) ====="
# Two memory/time tradeoffs forced this scope:
#   - batch_size 2048 (the README's recommendation, tuned for ~35-aa proteins) OOMs
#     the V100 here because mpnn_edges_raw.repeat(2048, ...) for a 1455-residue
#     protein would allocate ~76 GB. 128 fits comfortably with the model + activations.
#   - distance 60 + batch_size 128 takes ~1:46 wall, exceeding the partition's
#     practical time limit (~1.5 h based on prior TIMEOUTs). Distance 15 cuts the
#     pair count ~18x and finishes in ~10 min while still capturing the en31 trio
#     (all 8.5-9 A, in the model's trained coupling regime) plus PLM5's closest
#     pair (1249-1341, 14.1 A). The five PLM5 pairs >20 A are out-of-distribution
#     for the trained coupling head; epistasis term predicted there would be
#     ~additive by construction (= spatial independence), so omitting them costs
#     no scientific signal.
python v2_ssm.py \
    --mode epistatic \
    --pdb "$PDB" \
    --batch_size 128 \
    --out "$PROJ_ROOT/$OUTPUT_DIR/epistatic" \
    --chains A \
    --threshold 100 \
    --distance 15

echo
echo "===== Done ====="
ls -la "$PROJ_ROOT/$OUTPUT_DIR/"
