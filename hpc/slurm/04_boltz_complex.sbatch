#!/bin/bash
#SBATCH --job-name=boltz_complex
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=logs/04_boltz_%j.out
#SBATCH --error=logs/04_boltz_%j.err

# Boltz-2 prediction of FnCas9 + sgRNA + DNA complex.
#
# WARNING: V100 doesn't have native bfloat16, so Boltz will fall back to fp16.
# For full FnCas9 (1629 aa) + ~80-nt sgRNA + ~40-nt DNA, this may OOM on V100 32GB.
#
# Mitigation: try full-length first, and if OOM, fall back to the WED-PI domain
# only (residues 1230-1620 = 391 aa + ligands).
#
# Time on V100 32GB: ~30-60 min for the full complex.

# Bootstrap PATH — dgx compute node has empty PATH for SLURM jobs.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}

set -eo pipefail
mkdir -p logs results

# Initialise the modules system (SLURM jobs don't source ~/.bashrc).
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
OUTPUT_DIR="results/runs/${DATE}_boltz_complex"
mkdir -p "$OUTPUT_DIR"

# Boltz input YAML — placeholder.
# Real workflow: prepare configs/ with one YAML per variant to predict:
#   - WT FnCas9 + sgRNA + dsDNA target with NGG PAM
#   - FnCas9-PLM2 + same sgRNA + same DNA
#   - FnCas9-en31 + same sgRNA + same DNA
# YAML format docs: https://github.com/jwohlwend/boltz

CONFIG_YAML="hpc/inputs/boltz_fncas9_plm2.yaml"
if [[ ! -f "$CONFIG_YAML" ]]; then
    echo "[error] Missing $CONFIG_YAML — see hpc/inputs/README.md for the template."
    exit 1
fi

echo "===== Boltz-2 complex prediction ====="
echo "Config: $CONFIG_YAML"
echo "Output dir: $OUTPUT_DIR"
echo

# Use fp16 (V100 doesn't have bfloat16); see Boltz CLI flags
boltz predict "$CONFIG_YAML" \
    --out_dir "$OUTPUT_DIR" \
    --use_msa_server 1 \
    --diffusion_samples 5 \
    || {
        echo
        echo "[fallback] Full-length prediction failed (probably OOM)."
        echo "Trying domain-only fallback..."
        DOMAIN_YAML="hpc/inputs/boltz_fncas9_plm2_PI_domain.yaml"
        if [[ -f "$DOMAIN_YAML" ]]; then
            boltz predict "$DOMAIN_YAML" \
                --out_dir "$OUTPUT_DIR/PI_only" \
                --diffusion_samples 5
        else
            echo "[error] No domain-only fallback YAML at $DOMAIN_YAML"
            exit 1
        fi
    }

echo
echo "===== Done ====="
ls -la "$OUTPUT_DIR"
