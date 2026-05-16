#!/bin/bash
#SBATCH --job-name=boltz_e1449
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/04c_boltz_e1449_%j.out
#SBATCH --error=logs/04c_boltz_e1449_%j.err

# Single-point Boltz-2 prediction: FnCas9 WT + E1449L vs. FnCas9 WT + E1449H.
# §2.5 of notes/plans/2026-05-15_ROBUSTNESS_PLAN.md — falsifiable in-silico
# prediction. ESM-2 and LigandMPNN both prefer L at 1449; Acharya 2024 uses H
# (one of three mutations in en31). Single-point isolates the 1449 effect from
# G1243T and E1369R epistasis seen in en31's clustered geometry.
#
# Success criterion: clear directional prediction at iPTM, prot↔DNA-PAM iPTM,
# and per-residue pLDDT at position 1449, with confidence intervals across
# 5 diffusion samples. Closes "ready for the PI" gate criterion 5.
#
# Walltime estimate: ~10 min per variant on V100 (cf. job 219552 PLM4 single
# variant at ~10 min) → ~20-30 min total. Well within the ~1.5 h dgx
# practical limit (see session_handoff_2026-05-16 gotchas).

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
OUTPUT_DIR="results/runs/${DATE}_boltz_e1449"
mkdir -p "$OUTPUT_DIR"

# Regenerate YAMLs (variants dict already includes fncas9_e1449l and
# fncas9_e1449h as of the 04c sbatch landing date).
echo "[setup] Generating Boltz input YAMLs (PI-domain truncation for V100 fit)..."
PYTHONPATH=src python scripts/prepare_boltz_yamls.py --truncate 1230-1620

VARIANTS=(
    "fncas9_e1449l"
    "fncas9_e1449h"
)

for SLUG in "${VARIANTS[@]}"; do
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
        --diffusion_samples 5 \
        || {
            echo "[warn] $SLUG prediction failed. Continuing with next variant."
        }
done

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
