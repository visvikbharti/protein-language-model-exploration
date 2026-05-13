#!/bin/bash
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

# Bootstrap PATH — dgx compute node has empty PATH for SLURM jobs.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}

set -eo pipefail
mkdir -p logs results external

# Initialise the modules system (SLURM jobs don't source ~/.bashrc).
if [ -f /etc/profile.d/modules.sh ]; then
    . /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    . /usr/share/Modules/init/bash
fi
command -v module >/dev/null 2>&1 && module purge || true

cd /lustre/vishal.bharti/protein-language-model-exploration
. .venv-hpc/bin/activate

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

# Install LigandMPNN's Python deps that aren't already in our venv.
# DO NOT use their requirements.txt directly — it pins torch==2.2.1 (cu12),
# numpy==1.23.5, scipy==1.12.0, which would clobber our cu118 stack.
# Only the LigandMPNN-specific packages are needed; torch/numpy/scipy/biopython
# are already provided by setup_env.sh and are compatible.
if [[ ! -f "$LIGANDMPNN_DIR/.deps_installed" ]]; then
    echo "[setup] Installing LigandMPNN-specific deps (ProDy, ml-collections, dm-tree)..."
    pip install --prefer-binary 'ProDy>=2.4,<3' 'ml-collections>=0.1.1' 'dm-tree>=0.1.8'
    touch "$LIGANDMPNN_DIR/.deps_installed"
fi

# Patch vendored openfold for NumPy 2.x: it uses np.int / np.float / np.bool
# which were removed in NumPy 1.24. Downgrading numpy would break the rest of
# the venv (ESM-2 et al. already validated at numpy 2.x), so we rewrite the
# aliases in place. \b word-boundary protects np.int_ / np.float64 etc.
if [[ ! -f "$LIGANDMPNN_DIR/.numpy2_patched" ]]; then
    echo "[setup] Patching vendored openfold for NumPy 2.x compatibility..."
    find "$LIGANDMPNN_DIR/openfold" -name '*.py' -exec sed -i -E \
        -e 's/\bnp\.int\b/int/g' \
        -e 's/\bnp\.float\b/float/g' \
        -e 's/\bnp\.bool\b/bool/g' \
        -e 's/\bnp\.object\b/object/g' \
        -e 's/\bnp\.str\b/str/g' \
        -e 's/\bnp\.long\b/int/g' \
        -e 's/\bnp\.unicode\b/str/g' \
        {} +
    touch "$LIGANDMPNN_DIR/.numpy2_patched"
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

# PI-domain residues to design — full WED+PI region 1230-1620.
# LigandMPNN's CLI expects SPACE-SEPARATED tokens "A1230 A1231 ..." — passing a
# range like "A1230-A1620" is silently rejected (0 positions designed, all
# 1,600 samples come back identical to the PDB sequence; see job 214059).
# 5B2O chain A uses UniProt numbering directly; all 391 positions in
# 1230-1620 are resolved (verified against 5B2O ATOM records, 2026-05-13).
DESIGN_RESIDUES=$(python3 -c "print(' '.join(f'A{i}' for i in range(1230, 1621)))")
N_DESIGN_TOKENS=$(echo "$DESIGN_RESIDUES" | wc -w)
echo "Design residues: $N_DESIGN_TOKENS tokens (first=$(echo $DESIGN_RESIDUES | awk '{print $1}'), last=$(echo $DESIGN_RESIDUES | awk '{print $NF}'))"
echo

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
