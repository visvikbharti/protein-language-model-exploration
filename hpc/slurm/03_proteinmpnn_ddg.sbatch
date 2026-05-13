#!/bin/bash
#SBATCH --job-name=proteinmpnn_ddg
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=logs/03_proteinmpnn_ddg_%j.out
#SBATCH --error=logs/03_proteinmpnn_ddg_%j.err

# proteinmpnn_ddg: saturation ΔΔG prediction from PDB 5B2O.
# Used as a stability filter on top candidates from LigandMPNN + ESM-2 scoring.
#
# Distributed as a Docker image (ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base).
# We pull as Singularity SIF for this cluster (singularity-3.7.4 available).
#
# Time on V100: ~10-30 min depending on PDB size.

# Bootstrap PATH — dgx compute node has empty PATH for SLURM jobs.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}

set -eo pipefail
mkdir -p logs results external/proteinmpnn_ddg

# Initialise the modules system (SLURM jobs don't source ~/.bashrc).
if [ -f /etc/profile.d/modules.sh ]; then
    . /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    . /usr/share/Modules/init/bash
fi
if command -v module >/dev/null 2>&1; then
    module purge || true
    module load singularity-3.7.4 || /bin/echo "[warn] could not load singularity module"
fi

cd /lustre/vishal.bharti/protein-language-model-exploration

DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_proteinmpnn_ddg"
mkdir -p "$OUTPUT_DIR"

SIF="external/proteinmpnn_ddg/proteinmpnn_ddg.sif"
if [[ ! -f "$SIF" ]]; then
    echo "[setup] Pulling proteinmpnn_ddg Singularity image..."
    cd external/proteinmpnn_ddg
    singularity pull --name proteinmpnn_ddg.sif \
        docker://ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base
    cd -
fi

INPUT_PDB="data/raw/5B2O.pdb"

echo "===== proteinmpnn_ddg saturation ΔΔG ====="
echo "Input PDB: $INPUT_PDB"
echo "Output dir: $OUTPUT_DIR"
echo

# The peptoneltd container is distroless (no cat/ls/sh) and the entrypoint
# exec's whatever argv we pass it. The predict.py script lives at
# /app/proteinmpnn_ddg/predict.py and must be invoked via python3
# (verified from the upstream README, 2026-05-13).
#
# Flag names from the README:
#   --pdb_path    input PDB
#   --chains      chain id (comma-separated for multiple)
#   --outpath     output CSV
#   --seed        random seed
#   --model_name  model checkpoint version
#
# No documented --positions flag; the tool runs full-chain saturation by
# default. We extract the 1230-1620 subset in scripts/proteinmpnn_ddg_analyze.py.
# Bind the working dir so the container can read $INPUT_PDB and write $OUTPUT_DIR.
singularity run --nv \
    --bind "$PWD:/workspace" --pwd /workspace \
    "$SIF" \
    python3 /app/proteinmpnn_ddg/predict.py \
        --pdb_path "$INPUT_PDB" \
        --chains A \
        --outpath "$OUTPUT_DIR/ddg.csv" \
        --seed 42 \
        --model_name v_48_020

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
