#!/bin/bash
#SBATCH --job-name=boltz_spcas9
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/04e_boltz_spcas9_%j.out
#SBATCH --error=logs/04e_boltz_spcas9_%j.err

# Boltz-2 prediction for SpCas9 PI domain + sgRNA + DNA target/PAM.
# Tier 1 Phase A of notes/plans/2026-05-16_TIER1_MD_PROXY_PLAN.md.
# Adds SpCas9 as the cross-species baseline to the MSA-Boltz comparison table,
# converting "PLM5 ≈ en31" into "PLM5 ≥ en31 ≥ SpCas9" framing for the PI gate.
#
# Input YAML: hpc/inputs/boltz_spcas9_pi.yaml  (SpCas9 PI 1100-1368, 269 aa,
#             same 5B2O-derived sgRNA + DNA C/D as the FnCas9 set).
# Walltime estimate: ~10-15 min on V100 (smaller than FnCas9 391-aa runs).
# 5 diffusion samples, MSA-Boltz mode (--use_msa_server) for apples-to-apples
# with the 2026-05-15_boltz_complex MSA results.

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
OUTPUT_DIR="results/runs/${DATE}_boltz_spcas9"
mkdir -p "$OUTPUT_DIR"

CONFIG_YAML="hpc/inputs/boltz_spcas9_pi.yaml"
if [[ ! -f "$CONFIG_YAML" ]]; then
    echo "[error] Missing $CONFIG_YAML"
    exit 1
fi

SLUG="spcas9_pi"
VAR_OUT="$OUTPUT_DIR/$SLUG"
mkdir -p "$VAR_OUT"
echo
echo "===== Boltz-2 prediction: $SLUG (SpCas9 PI 1100-1368) ====="
echo "Config: $CONFIG_YAML"
echo "Output: $VAR_OUT"
echo

boltz predict "$CONFIG_YAML" \
    --out_dir "$VAR_OUT" \
    --use_msa_server \
    --diffusion_samples 5 \
    || {
        echo "[error] SpCas9 Boltz prediction failed."
        exit 1
    }

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
