#!/usr/bin/env bash
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

set -euo pipefail
mkdir -p logs results external/proteinmpnn_ddg

module purge
module load python-3.12.2
module load singularity-3.7.4

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

singularity run --nv "$SIF" \
    predict.py \
        --pdb "$INPUT_PDB" \
        --output "$OUTPUT_DIR/ddg.csv" \
        --chain A \
        --positions 1230-1620

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
