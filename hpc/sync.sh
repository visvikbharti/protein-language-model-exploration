#!/usr/bin/env bash
# Sync the project tree between local Mac and the CSIR-IGIB HPC.
#
# Usage:
#   bash hpc/sync.sh push      # local Mac -> HPC
#   bash hpc/sync.sh pull      # HPC -> local Mac
#   bash hpc/sync.sh push -n   # dry-run

# NOTE: do NOT use `set -u` here — macOS ships bash 3.2 which throws on
# empty array expansion (e.g. "${EXTRA_FLAGS[@]}" when no extra args given).
set -eo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REMOTE_HOST="${HPC_HOST:-tejas.igib.res.in}"
REMOTE_USER="${HPC_USER:-vishal.bharti}"
REMOTE_PATH="${HPC_PATH:-/lustre/vishal.bharti/protein-language-model-exploration}"

# Collect extra rsync flags (anything after the verb). Use shift + "$@" so
# the array is empty (not undefined) when no flags are given.
CMD="${1:-}"
shift 2>/dev/null || true
EXTRA_FLAGS=("$@")

EXCLUDES=(
    --exclude '.git/'
    --exclude '.venv/'
    --exclude '.venv-hpc/'
    --exclude '__pycache__/'
    --exclude '*.pyc'
    --exclude '.pytest_cache/'
    --exclude '.mypy_cache/'
    --exclude '.ruff_cache/'
    --exclude '.DS_Store'
    --exclude '.ipynb_checkpoints/'
    --exclude 'data/raw/structures/*.pdb'   # large PDBs — re-download on HPC if needed
    --exclude 'external/'                   # vendored repos; HPC clones its own copies
    --exclude 'logs/'                       # SLURM logs only live on HPC
    --exclude '*.sif'                       # Singularity images stay on HPC
    --exclude '.cache/'
)

case "$CMD" in
    push)
        echo "[sync] $PROJECT_ROOT/  ->  $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        rsync -avhP "${EXCLUDES[@]}" ${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"} \
            "$PROJECT_ROOT/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        ;;
    pull)
        echo "[sync] $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/results/  ->  $PROJECT_ROOT/results/"
        rsync -avhP ${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"} \
            "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/results/" \
            "$PROJECT_ROOT/results/"
        echo
        echo "[sync] $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/logs/  ->  $PROJECT_ROOT/logs/"
        rsync -avhP ${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"} \
            "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/logs/" \
            "$PROJECT_ROOT/logs/" || true
        ;;
    *)
        echo "Usage: $0 {push|pull} [rsync flags]"
        echo
        echo "Examples:"
        echo "  $0 push           # full push"
        echo "  $0 push -n        # dry-run"
        echo "  $0 pull           # pull results/ and logs/ from HPC"
        echo
        echo "Environment overrides:"
        echo "  HPC_HOST=$REMOTE_HOST"
        echo "  HPC_USER=$REMOTE_USER"
        echo "  HPC_PATH=$REMOTE_PATH"
        exit 1
        ;;
esac

echo "[sync] Done."
