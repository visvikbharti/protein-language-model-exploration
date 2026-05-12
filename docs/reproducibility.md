# Reproducibility

Every claim produced by this project must be reproducible from artefacts on disk. This doc says exactly how.

## Principle

A result is reproducible if, given **(a)** the run directory under `results/runs/<name>/`, **(b)** this repository at the git SHA in that run's `meta.json`, and **(c)** the same model weights, anyone can re-execute the run and obtain the same outputs to within numerical tolerance.

## What lives in each run directory

```
results/runs/<name>/
├── meta.json              # full provenance (see methods.md §5)
├── pip-freeze.txt         # exact Python env at run time
├── config.yaml            # exact config used (copy, not link)
├── inputs/
│   ├── A0Q5Y3.fasta       # input FASTA used (snapshot, hashed in meta)
│   └── 5B2O.pdb           # input PDB used (snapshot, hashed in meta)
├── *.parquet              # tabular outputs
├── *.cif                  # any structure predictions
├── plots/*.png            # figures
└── report.md              # human-readable summary, written by the pipeline
```

Every artefact in `inputs/` is a **copy**, not a symlink. Inputs may be edited or deleted from `data/raw/` later; the run directory stays self-contained.

## To re-run an existing result

```bash
# 1. Check out the project at the run's git SHA
git checkout $(jq -r .git_sha results/runs/<name>/meta.json)

# 2. Recreate the Python env from the frozen list
python3.11 -m venv .venv-replay
source .venv-replay/bin/activate
pip install -r results/runs/<name>/pip-freeze.txt

# 3. Verify input hashes match
sha256sum -c results/runs/<name>/inputs.sha256

# 4. Re-execute
python -m nuclease_design.cli run --config results/runs/<name>/config.yaml \
    --output results/runs/<name>_replay
```

The new directory `<name>_replay/` should match the original to within (a) bit-identical for ESM-2 (deterministic algorithms enabled) and (b) sampled-output set equality for stochastic samplers (LigandMPNN temperatures, Protein2PAM evolution).

## Verifying agreement between original and replay

```bash
python -m nuclease_design.cli compare \
    results/runs/<name> \
    results/runs/<name>_replay
```

This compares each Parquet/CSV table row-by-row, structure files via per-residue C-alpha RMSD, and reports any divergence with a tolerance per artefact type.

## Hash management

- Every file in `data/raw/` is recorded in `data/raw/manifest.tsv` with SHA-256 + original URL + retrieval date.
- Model weights live under `data/external/`; hashes in `data/external/manifest.tsv`.
- The pipeline refuses to start if any required input has a hash mismatch.

## Non-determinism we accept and document

- **GPU non-determinism for some operations**: even with `torch.use_deterministic_algorithms(True)`, some CUDA ops are non-deterministic across GPU models. We document the GPU model in `meta.json`; results between H100 and A100 may differ at the ~1e-5 level.
- **Sampling stochasticity** in LigandMPNN and Protein2PAM is seeded; replay produces the same samples, but **changing the random seed will not** produce the same outputs (by design — sampler diversity).
- **External-service outputs** (AlphaFold3 server) cannot be reproduced byte-for-byte; we record the input + output and the date of the server query.

## What we never store

- Model weights inside the repo (they live in `data/external/`, gitignored).
- Raw FASTA / PDB files inside the repo (they live in `data/raw/`, gitignored).
- Cloud credentials or HuggingFace tokens.

## CI / continuous verification (future)

Future CI should re-run unit tests on every commit and re-execute a small "smoke" config (one variant, ESM-2 only, ~1 min) per release. Not yet implemented.
