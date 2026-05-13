#!/usr/bin/env bash
#SBATCH --job-name=ligandmpnn
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=logs/02_ligandmpnn_%j.out
#SBATCH --error=logs/02_ligandmpnn_%j.err

# LigandMPNN sampling on FnCas9 + sgRNA + DNA from PDB 5B2O.
#
# This is the Phase 3 core experiment: structure-conditioned design with the
# sgRNA + target DNA atoms as ligand context. Sample 5,000 sequences across
# 3 temperatures, with the PI-domain residues masked (designed) and the rest
# of FnCas9 fixed.
#
# Expected time on V100 32GB: ~1-2 hours for 5,000 samples × 3 temps.

set -euo pipefail
mkdir -p logs results external

module purge
module load python-3.12.2

cd /lustre/vishal.bharti/protein-language-model-exploration
source .venv-hpc/bin/activate

# Clone the LigandMPNN repo if not already present (~/external/LigandMPNN)
LIGANDMPNN_DIR="$PWD/external/LigandMPNN"
if [[ ! -d "$LIGANDMPNN_DIR" ]]; then
    echo "[setup] Cloning LigandMPNN..."
    git clone https://github.com/dauparas/LigandMPNN.git "$LIGANDMPNN_DIR"
fi

# Download weights if missing
if [[ ! -d "$LIGANDMPNN_DIR/model_params" ]]; then
    echo "[setup] Downloading LigandMPNN weights..."
    cd "$LIGANDMPNN_DIR"
    bash get_model_params.sh "model_params"
    cd -
fi

# Validate input PDB
INPUT_PDB="data/raw/5B2O.pdb"
if [[ ! -f "$INPUT_PDB" ]]; then
    echo "[error] Missing input PDB: $INPUT_PDB"
    exit 1
fi

DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_ligandmpnn_PI"
mkdir -p "$OUTPUT_DIR"

echo "===== LigandMPNN sampling on FnCas9 + sgRNA + DNA ====="
echo "Date: $(date)"
echo "Input PDB: $INPUT_PDB"
echo "Output dir: $OUTPUT_DIR"
echo "LigandMPNN dir: $LIGANDMPNN_DIR"
echo

# PI-domain residues to design (mask) — same as our Phase 2 hotspots, but extended
# to the full PI region. LigandMPNN expects 1-indexed residue ranges with chain ID.
# 5B2O chain A is the protein; B/C are sgRNA/DNA in some PDB conventions — verify.
DESIGN_RESIDUES="A1230-A1620"

for TEMP in 0.1 0.2 0.3; do
    echo ">> Sampling at temperature $TEMP"
    python "$LIGANDMPNN_DIR/run.py" \
        --pdb_path "$INPUT_PDB" \
        --out_folder "$OUTPUT_DIR/T${TEMP}" \
        --model_type "ligand_mpnn" \
        --checkpoint_ligand_mpnn "$LIGANDMPNN_DIR/model_params/ligandmpnn_v_32_010_25.pt" \
        --number_of_batches 50 \
        --batch_size 32 \
        --temperature "$TEMP" \
        --redesigned_residues "$DESIGN_RESIDUES" \
        --pack_side_chains 0 \
        --save_stats 1 \
        --verbose 1
done

echo
echo "===== Sampling done ====="
ls -la "$OUTPUT_DIR"
echo
echo "Next: run scripts/ligandmpnn_aggregate.py (not yet written) to compile"
echo "per-position frequencies into a single TSV for downstream filtering."
