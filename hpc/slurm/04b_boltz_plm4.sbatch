#!/bin/bash
#SBATCH --job-name=boltz_plm4
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/04b_boltz_plm4_%j.out
#SBATCH --error=logs/04b_boltz_plm4_%j.err

# Direct Boltz-2 prediction on FnCas9-PLM4 (T1535V/Y1249F/Y1341L/A1325K) + sgRNA + DNA.
# Rationale: PLM4 was rejected by the apo-DDG filter (proteinmpnn_ddg = +6.74 cumulative,
# T1535V alone = +4.15). The ThermoMPNN cross-check (2026-05-15) disagrees — it puts PLM4
# cumulative at +0.26 (within envelope) and T1535V at -0.19 (essentially neutral). Direct
# Boltz on the full complex is the deciding experiment: §2.2 action 1 of the robustness
# plan. ~10 min on V100 with truncation, 5 samples.

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

if ! python -c "import boltz" 2>/dev/null; then
    echo "[setup] Installing boltz..."
    pip install boltz
fi

DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_boltz_plm4"
mkdir -p "$OUTPUT_DIR"

# Regenerate the PLM4 YAML (the variants dict already includes fncas9_plm4 as of
# 2026-05-15; scripts/prepare_boltz_yamls.py writes all four MSA-on YAMLs).
echo "[setup] Generating Boltz input YAMLs (PI-domain truncation for V100 fit)..."
PYTHONPATH=src python scripts/prepare_boltz_yamls.py --truncate 1230-1620

SLUG="fncas9_plm4"
CONFIG_YAML="hpc/inputs/boltz_${SLUG}.yaml"
if [[ ! -f "$CONFIG_YAML" ]]; then
    echo "[error] Missing $CONFIG_YAML"
    exit 1
fi
VAR_OUT="$OUTPUT_DIR/$SLUG"
mkdir -p "$VAR_OUT"

echo
echo "===== Boltz-2 prediction: $SLUG ====="
echo "Config: $CONFIG_YAML"
echo "Output: $VAR_OUT"
echo

boltz predict "$CONFIG_YAML" \
    --out_dir "$VAR_OUT" \
    --use_msa_server \
    --diffusion_samples 5

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
