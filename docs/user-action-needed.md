# User action needed

The autonomous session in 2026-05 set up the project structure, knowledge base, agent definitions, design plan, methods/reproducibility docs, and verified the tool inventory. **Several follow-on steps cannot be done autonomously** and need a human at the keyboard.

Each item below is independent — start with whichever matches your next priority.

## A. Python environment (≈ 15 min)

**Why this is here, not auto-done:** the session's machine has Python 3.9 by default. Python 3.10+ is needed (we use `dataclass(slots=True)` and other 3.10+ syntax). The session created a venv with the local Homebrew `python3.11` and verified the test suite passes, but did not install the heavy ML deps because they would write into the user's filesystem outside our intent for an unattended run.

```bash
# Already done by the session (verify):
ls .venv && .venv/bin/python --version    # should be 3.11.11

# Activate
source .venv/bin/activate

# Install the project + dev deps (about 2 min)
pip install -e ".[dev]"

# Confirm tests still pass
pytest tests/ -q
```

Expected output: `34 passed in 0.04s` (or similar).

## B. Hugging Face access for gated models (≈ 10 min)

**Why this is here:** Hugging Face requires a human to click-through accept the licenses for ESM-3 (EvolutionaryScale community license) and a few other gated weights.

1. Create an account at https://huggingface.co/ if you don't have one.
2. Generate an access token at https://huggingface.co/settings/tokens (read-only is fine).
3. Accept the license for:
   - https://huggingface.co/EvolutionaryScale/esm3-sm-open-v1 (ESM-3 small open)
   - https://huggingface.co/EvolutionaryScale/esmc-300m-2024-12 (ESM Cambrian 300M)
4. Set the token in `.env` (not committed):
   ```bash
   echo "HF_TOKEN=hf_xxxxxxxx" > .env
   ```
5. Verify access:
   ```bash
   source .venv/bin/activate
   python -c "import os; from huggingface_hub import HfApi; \
              print(HfApi(token=os.environ['HF_TOKEN']).whoami())"
   ```

## C. GPU access (variable cost)

**Why this is here:** the design pipeline needs ~50 GPU-hours of H100/A100 time (see `docs/design-plan.md` §6). Cloud options:

| Provider | GPU | Approx $/hr (2026) | Notes |
|---|---|---|---|
| Lambda Cloud | H100 80GB | ~$3.00 | Good for short bursts |
| RunPod | A100 80GB | ~$1.80 | Spot pricing cheaper |
| vast.ai | RTX 4090 / A6000 | ~$0.50–1.20 | Variable reliability |
| Modal | H100 | ~$5.00 | Best DX, charges by second |
| Institutional HPC | — | $0 (typically) | Slowest to schedule |

Recommended: Modal for first prototyping (rapid iteration), then RunPod for the production sweep.

## D. Download reference data (≈ 5 min, scriptable)

```bash
source .venv/bin/activate

mkdir -p data/raw

# WT FnCas9 sequence
curl -sLo data/raw/A0Q5Y3.fasta https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta

# WT FnCas9 + sgRNA + DNA structure
curl -sLo data/raw/5B2O.pdb https://files.rcsb.org/download/5B2O.pdb

# Optional: variant-PAM context structures
curl -sLo data/raw/5B2P.pdb https://files.rcsb.org/download/5B2P.pdb
curl -sLo data/raw/5B2Q.pdb https://files.rcsb.org/download/5B2Q.pdb

# Optional: AlphaFold predicted model of A0Q5Y3
curl -sLo data/raw/AF-A0Q5Y3-F1-model_v4.pdb \
    https://alphafold.ebi.ac.uk/files/AF-A0Q5Y3-F1-model_v4.pdb

# Compute hashes for reproducibility
( cd data/raw && sha256sum *.fasta *.pdb > manifest.tsv )
```

## E. Install heavy ML deps (lazy — only what you need)

These are kept out of `pyproject.toml` core deps because each is large and not all milestones need all of them.

```bash
source .venv/bin/activate

# For M1, M2.2, M3 (ESM-2 zero-shot scoring) — ~5 GB
pip install fair-esm

# For M2.1, M3, M4 (LigandMPNN sampling and scoring) — vendor the repo
mkdir -p external
git -C external clone https://github.com/dauparas/LigandMPNN.git
git -C external clone https://github.com/dauparas/ProteinMPNN.git
( cd external/LigandMPNN && bash get_model_params.sh "model_params" )

# For M1, M5 (Boltz-2 complex prediction) — auto-downloads weights on first use
pip install boltz

# For M5 cross-validation (Chai-1) — auto-downloads weights
pip install chai_lab==0.6.1

# For M2.3 (Protein2PAM evolution — non-commercial use only)
git -C external clone https://github.com/Profluent-AI/protein2pam.git
( cd external/protein2pam && pip install -e . )

# For M3 ΔΔG filter — Docker only
docker pull ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base
```

## F. First milestone (M1 — baseline)

Once A–E are done, run:

```bash
source .venv/bin/activate
python -m nuclease_design.cli baseline \
    --config configs/baseline.yaml \
    --output results/runs/$(date -u +%Y-%m-%d)_baseline
```

(The CLI is not yet implemented — that is the next coding task. The current code provides primitives for variant parsing, FASTA I/O, and the Scorer Protocol; the CLI and pipeline orchestration come after the design plan is reviewed.)

## G. Wet-lab handoff (after M6)

When M6 completes, hand `docs/wet-lab-handoff.md` (auto-generated) to the wet-lab collaborator. The handoff doc contains:

- Final ranked variant list with FASTA sequences
- Assay protocol (from M0 design objective)
- Predicted effect sizes with confidence intervals
- Expected false-positive rate from cross-validator agreement
- Suggested controls (WT FnCas9, en31, a known dead mutant)

## H. Outstanding verification items

Documented in `notes/plm/verification-log.md` §"Outstanding items":

1. Exact HDR knock-in percentages for en1 / en15 / en31 vs. SpCas9-HF1 / eSpCas9 at DCX → need Supplementary Tables from the Acharya 2024 Nat Commun paper (not extractable from snippets).
2. OpenCRISPR-1 specific numbers (~240k Cas9s, ~4M generated, ~200 tested) → need Nature paper full text.
3. Protein2PAM "42 N4G PAMs vs 7 for WT" → need Nat Biotechnol full text.
4. Whether ESM-IF1 has an explicit context-length limit, and if so, the primary source (likely Hsu et al. 2022 paper).

If you have institutional access to Nature / Nat Biotechnol / Nat Commun, please pull the supplementary materials for each of the above and update the verification log.

## I. Decisions outstanding for the project lead

From `docs/design-plan.md` §9:

1. **Which design axis** in M0 — activity, PAM, or specificity?
2. **Which canonical locus** for in-cell editing predictions? (Default: HBB g21)
3. **Wet-lab variant cap**? (Default: 96)
4. **Use Protein2PAM** despite non-commercial license? (Default: yes for academic only)
