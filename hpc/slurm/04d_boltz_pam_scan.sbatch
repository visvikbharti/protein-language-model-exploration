#!/bin/bash
#SBATCH --job-name=boltz_pam_scan
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/04d_boltz_pam_scan_%j.out
#SBATCH --error=logs/04d_boltz_pam_scan_%j.err

# Boltz-2 PAM-variant scan: §2.4 (Reading B) of the robustness phase.
#
# Background: Protein2PAM (2026-05-18) returned a null result — all 4 FnCas9
# variants predicted NGG-only with no inter-variant resolution. The web service
# does not distinguish PLM5 from en31 from WT. en31 is wet-lab-validated to
# relax NGG → NGG/NGA/NAG (Acharya 2024), so Protein2PAM is below the
# resolution threshold for our question. Fallback per the original robustness
# plan §2.4 action 3: predict the full complex under each of {NGG, NGA, NAG,
# NCG, NTG, NAA} for each of {WT, PLM5, en31} and compare interface confidence.
# A candidate that tolerates non-NGG PAMs better than WT tolerates non-NGG PAMs
# is structurally consistent with the PAM-relaxation phenotype.
#
# NGG control runs (3 variants) are already in results/runs/2026-05-15_boltz_complex/
# — we reuse those rather than re-running. This sbatch runs the 15 non-NGG combos:
#   {WT, PLM5, en31} × {NGA, NAG, NCG, NTG, NAA} = 15 Boltz predictions.
#
# Wall time: ~10 min per prediction on V100 with truncated WED+PI (1230-1620),
# MSA-on, 5 diffusion samples. 15 × 10 = ~2.5 hr cumulative; --time=04:00:00
# gives generous buffer.

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
OUTPUT_DIR="results/runs/${DATE}_boltz_pam_scan"
mkdir -p "$OUTPUT_DIR"

# YAMLs were generated locally via scripts/prepare_boltz_pam_scan_yamls.py
# and pushed to hpc/inputs/. Regenerate here as well so the sbatch is
# self-contained if YAML file metadata drifts.
echo "[setup] Regenerating PAM-scan YAMLs..."
PYTHONPATH=src python scripts/prepare_boltz_pam_scan_yamls.py

# 15 variants: {wt, plm5, en31} × {NGA, NAG, NCG, NTG, NAA}
VARIANTS=(
    "fncas9_wt_pam_NGA"
    "fncas9_wt_pam_NAG"
    "fncas9_wt_pam_NCG"
    "fncas9_wt_pam_NTG"
    "fncas9_wt_pam_NAA"
    "fncas9_plm5_pam_NGA"
    "fncas9_plm5_pam_NAG"
    "fncas9_plm5_pam_NCG"
    "fncas9_plm5_pam_NTG"
    "fncas9_plm5_pam_NAA"
    "fncas9_en31_pam_NGA"
    "fncas9_en31_pam_NAG"
    "fncas9_en31_pam_NCG"
    "fncas9_en31_pam_NTG"
    "fncas9_en31_pam_NAA"
)

for SLUG in "${VARIANTS[@]}"; do
    CONFIG_YAML="hpc/inputs/boltz_${SLUG}.yaml"
    if [[ ! -f "$CONFIG_YAML" ]]; then
        echo "[error] Missing $CONFIG_YAML"
        exit 1
    fi
    VAR_OUT="$OUTPUT_DIR/$SLUG"
    if [[ -d "$VAR_OUT" && -n "$(ls -A "$VAR_OUT" 2>/dev/null)" ]]; then
        echo "[skip] $SLUG output exists, skipping (resume mode)"
        continue
    fi
    mkdir -p "$VAR_OUT"
    echo
    echo "===== Boltz-2 PAM-scan: $SLUG ====="
    boltz predict "$CONFIG_YAML" \
        --out_dir "$VAR_OUT" \
        --use_msa_server \
        --diffusion_samples 5 \
        || {
            echo "[warn] $SLUG failed. Continuing."
        }
done

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
