# protein-language-model-exploration

PLM-guided redesign of FnCas9 toward enFnCas9-class performance.

## What this project is

A small-lab in-silico campaign to use protein language models (ESM-2/3, LigandMPNN, ProteinMPNN, Boltz-2, Protein2PAM) to propose FnCas9 variants that match or exceed **enFnCas9** (Acharya et al., *Nat Commun* 15:5471, 2024) on one of three axes: activity, PAM scope, or specificity.

**Status:** scoping + literature verification complete. Code scaffolding and primitives done. Design plan ratified. **No model inference has run yet** — that requires user action (Python env, GPU, gated HF access). See `docs/user-action-needed.md`.

## Read in this order

1. **`docs/design-plan.md`** — milestone-by-milestone plan with verification gates and decision rules.
2. **`notes/plm/enFnCas9-overview.md`** — what enFnCas9 is, exact mutations, performance numbers, primary-source-verified.
3. **`notes/plm/plm-nuclease-engineering.md`** — landscape of PLM-designed nucleases (OpenCRISPR-1, NmeN4G.1, AiCE, etc.), with verified citations.
4. **`docs/tools-inventory.md`** — verified open-source tools with license/maturity/install info.
5. **`docs/methods.md`** — exact scoring procedures for each model.
6. **`docs/reproducibility.md`** — how to re-execute any result from `results/runs/`.
7. **`docs/user-action-needed.md`** — what cannot be done autonomously.
8. **`notes/plm/verification-log.md`** — every claim cross-checked against primary sources; corrections recorded.

## Project structure

```
.
├── .claude/
│   ├── agents/                  # custom Claude Code subagents
│   │   ├── plm-scout.md         # literature scout
│   │   ├── nuclease-engineer.md # Cas9 design domain expert
│   │   └── plm-coder.md         # writes PLM pipeline code
│   └── settings.local.json      # project permissions
├── docs/                        # design plan, methods, reproducibility, tools, user-action
├── notes/plm/                   # verified knowledge base
│   ├── drafts/                  # raw draft survey output (kept for audit trail)
│   ├── enFnCas9-overview.md
│   ├── plm-nuclease-engineering.md
│   ├── verification-log.md
│   ├── proteingym-substitutions.md
│   └── proteingym-indels.md
├── src/nuclease_design/         # Python source
│   ├── variants.py              # Variant dataclass + parsing
│   ├── io.py                    # FASTA / PDB I/O
│   └── scoring/__init__.py      # Scorer Protocol
├── tests/                       # pytest tests (34 passing as of 2026-05-12)
├── scripts/                     # one-off scripts
├── configs/                     # YAML run configs
├── data/                        # raw, processed, external — all gitignored
├── results/runs/                # run outputs — gitignored
├── notebooks/                   # Jupyter exploration
└── pyproject.toml
```

## Scientific integrity commitment

Every numerical claim or attribution in this project is verified against the primary source and recorded in `notes/plm/verification-log.md`. Unverified claims are tagged `[UNVERIFIED]` in the relevant document. The verification round of 2026-05-12 caught several errors in the original literature-scout output — including a wrong first author, an incomplete mutation set for FnCas9-RHA, and a mis-attributed specificity number — all of which have been corrected.

## Quick start (once user-action steps are done)

```bash
source .venv/bin/activate
pytest tests/ -q                                  # 34 tests should pass
# Then follow docs/user-action-needed.md sections D–F.
```

## License

This project is for research use. Several tools we integrate carry non-commercial licenses (Protein2PAM, CRISPR-Cas-Atlas, ESM-3 default weights) — see `docs/tools-inventory.md` for the gates.

## Contributors

Vishal V. Bharti (project lead). Claude Code (Opus 4.7, 1M context) ran the autonomous session of 2026-05-12 that produced the verified knowledge base, agent definitions, design plan, and code scaffolding.
