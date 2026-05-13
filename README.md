# protein-language-model-exploration

PLM-guided redesign of FnCas9 toward enFnCas9-class performance.

## What this project is

A small-lab in-silico campaign to use protein language models (ESM-2/3, LigandMPNN, ProteinMPNN, Boltz-2, Protein2PAM) to propose FnCas9 variants that match or exceed **enFnCas9** (Acharya et al., *Nat Commun* 15:5471, 2024) on one of three axes: activity, PAM scope, or specificity.

**Status:** Phase 2 complete. Two PLM-designed candidates produced — **FnCas9-PLM1** (ESM-2 35M, no filter) and **FnCas9-PLM2** (ESM-2 650M + Cas9-family conservation filter). PLM2 recovers en31's G1243T mutation independently. Pre-registered hypothesis H1 (model scale alone fixes the rare-AA bias) was **refuted** by cross-validation; conservation filter recovered design credibility. See `results/runs/2026-05-13_final/design-report-phase2.md`.

## Read in this order

1. **`results/runs/2026-05-13_final/design-report-phase2.md`** — the latest design report (FnCas9-PLM2 + cross-validation results).
2. **`results/runs/2026-05-13_final/design-report.md`** — Phase 1 report (FnCas9-PLM1, the failed M1-gate result).
3. **`docs/design-plan.md`** — milestone-by-milestone master plan.
4. **`docs/design-plan-phase2.md`** — Phase 2 plan (pre-registered hypotheses, checkpoints).
5. **`notes/plm/enFnCas9-overview.md`** — what enFnCas9 is, exact mutations, performance numbers, primary-source-verified.
6. **`notes/plm/plm-nuclease-engineering.md`** — landscape of PLM-designed nucleases (OpenCRISPR-1, NmeN4G.1, AiCE, etc.), with verified citations.
7. **`docs/tools-inventory.md`** — verified open-source tools with license/maturity/install info.
8. **`docs/methods.md`** — exact scoring procedures for each model.
9. **`docs/reproducibility.md`** — how to re-execute any result from `results/runs/`.
10. **`docs/user-action-needed.md`** — what cannot be done autonomously.
11. **`notes/plm/verification-log.md`** — every claim cross-checked against primary sources; corrections recorded.

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
