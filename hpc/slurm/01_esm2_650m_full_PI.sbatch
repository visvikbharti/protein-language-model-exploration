#!/usr/bin/env bash
#SBATCH --job-name=esm2_650m_PI
#SBATCH --partition=dgx
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/01_esm2_650m_PI_%j.out
#SBATCH --error=logs/01_esm2_650m_PI_%j.err

# ESM-2 650M zero-shot saturation over the entire PI domain of FnCas9
# (residues ~1340-1620, ~280 positions × 19 substitutions = ~5,320 mutants).
#
# On a V100 with fp16, this should take 5-15 minutes (vs ~12 min on CPU for
# the 84-position subset). The bigger position set covers all of the PAM-
# interacting region rather than just the four enFnCas9 hotspots.

set -eo pipefail
mkdir -p logs results

# Initialise the modules system (SLURM jobs don't source ~/.bashrc).
if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh
elif [ -f /usr/share/Modules/init/bash ]; then
    source /usr/share/Modules/init/bash
fi
command -v module >/dev/null && module purge || true

cd /lustre/vishal.bharti/protein-language-model-exploration
source .venv-hpc/bin/activate

DATE=$(date -u +%Y-%m-%d)
OUTPUT_DIR="results/runs/${DATE}_esm2_650M_full_PI_hpc"

echo "===== ESM-2 650M full PI-domain scan ====="
echo "Date: $(date)"
echo "Output dir: $OUTPUT_DIR"
echo

# Extend the saturation script to scan a larger window.
# Currently scripts/run_saturation.py uses HOTSPOT_WINDOWS hardcoded.
# Here we override by setting an env var the script can read OR by patching:
PYTHONPATH=src python <<'PY'
import os, sys, json
sys.path.insert(0, 'src')
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from nuclease_design.io import load_fasta
from nuclease_design.scoring.esm import ESMScorer, score_saturation
from nuclease_design.variants import Variant

OUTPUT_DIR = Path(os.environ.get(
    "OUTPUT_DIR",
    f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_esm2_650M_full_PI_hpc",
))

# Full PI domain (Hirano 2016 boundaries ~1340-1620; we go 1230-1620 to also
# cover the WED phosphate-lock-loop region)
positions = list(range(1230, 1621))

fncas9 = load_fasta(Path("data/raw/A0Q5Y3_fncas9.fasta"))[0].sequence
print(f"FnCas9 length: {len(fncas9)}")
print(f"Scanning {len(positions)} positions")

scorer = ESMScorer(name="esm2_650M", device="cuda")
sat = score_saturation(scorer, fncas9, positions)
print(f"Scored {len(sat)} variants")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
tsv_path = OUTPUT_DIR / "scores.tsv"
with tsv_path.open("w") as f:
    f.write("pos\twt\tmut\tvariant\tllr\n")
    for v, s in sat:
        f.write(f"{v.pos}\t{v.wt}\t{v.mut}\t{v}\t{s:.6f}\n")
print(f"Wrote {tsv_path}")

# Meta
meta = {
    "model": "esm2_t33_650M_UR50D",
    "device": "cuda",
    "n_positions": len(positions),
    "positions_range": [min(positions), max(positions)],
    "n_variants_scored": len(sat),
    "fasta": "data/raw/A0Q5Y3_fncas9.fasta",
    "started_at_utc": datetime.now(timezone.utc).isoformat(),
}
(OUTPUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

# Quick check: where do reference mutations land
ranks = {}
all_vars = [(v, s) for v, s in sat]
all_vars.sort(key=lambda x: -x[1])
var_to_rank = {str(v): i + 1 for i, (v, _) in enumerate(all_vars)}
for v_str in ["G1243T", "E1369R", "E1449H", "E1603H"]:
    if v_str in var_to_rank:
        print(f"  {v_str}: global rank {var_to_rank[v_str]}/{len(all_vars)}")
PY

echo
echo "===== Done ====="
