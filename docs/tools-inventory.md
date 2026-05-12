# Tools inventory — PLM-guided nuclease design

**Last verified:** 2026-05-12 (round 1 verification via `notes/plm/verification-log.md`)
**Source of truth:** GitHub APIs + README + repo LICENSE files, accessed directly.

Status legend:
- **VERIFIED** — repo at claimed URL, license confirmed, last commit within the last 12 months.
- **STALE** — repo exists at claimed URL but last commit > 12 months ago (still installable, no upstream support).
- **MOVED / RENAMED** — repo at a different URL than originally claimed.
- **NOT FOUND** — could not locate.

| # | Tool | Repo (verified) | Last commit | Stars | License | GPU | Maintainer | Entry-point | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ESM-2 / fair-esm | https://github.com/facebookresearch/esm | 2024-02-07 | ~4,067 | MIT | Recommended | Meta (FAIR) — archived 2024-08 | `esm.pretrained.esm2_t33_650M_UR50D()` | **STALE** |
| 2 | ESM-IF1 | https://github.com/facebookresearch/esm/tree/main/examples/inverse_folding | 2024-02-07 | (parent) | MIT | Recommended | Meta (FAIR) | `examples/inverse_folding/sample_sequences.py` | **STALE** |
| 3 | ESM-3 / ESM Cambrian | https://github.com/evolutionaryscale/esm | 2026-05-11 | ~2,327 | Mixed: Cambrian community license + commercial option | Recommended | EvolutionaryScale | `ESM3.from_pretrained()` / `ESMC.from_pretrained()` | **VERIFIED** |
| 4 | ProGen2 | https://github.com/salesforce/progen | 2023-08-04 | ~700 | BSD-3-Clause | Recommended | Salesforce | `progen2/sample.py`, `progen2/likelihood.py` | **STALE** |
| 5 | ProteinMPNN | https://github.com/dauparas/ProteinMPNN | 2024-08-14 | ~1,722 | MIT | Optional (small) | Baker lab (J. Dauparas) | `protein_mpnn_run.py` | **STALE** (just past 12 mo) |
| 6 | LigandMPNN | https://github.com/dauparas/LigandMPNN | 2025-02-06 | ~576 | MIT | Optional | Baker lab (J. Dauparas) | `run.py` (design), `score.py` (score) | **STALE** (~15 mo since last push) |
| 7 | RFdiffusion | https://github.com/RosettaCommons/RFdiffusion | 2026-04-24 | ~2,862 | BSD-style (NOASSERTION SPDX) | Required | RosettaCommons / Baker lab | `scripts/run_inference.py` | **VERIFIED** |
| 8 | RFdiffusion-AA | https://github.com/baker-laboratory/rf_diffusion_all_atom | 2024-07-09 | ~481 | NOASSERTION (custom) | Required (--nv) | Baker lab | `run_inference.py` (Apptainer) | **STALE** (~22 mo) |
| 9 | Boltz / Boltz-2 | https://github.com/jwohlwend/boltz | 2026-03-29 | ~3,960 | MIT | Required (CPU very slow) | Wohlwend / MIT CSAIL | CLI: `boltz predict <input.yaml>` | **VERIFIED** |
| 10 | Chai-1 | https://github.com/chaidiscovery/chai-lab | 2026-04-11 | ~1,935 | **Apache-2.0** (corrected from "MIT") | Required (bfloat16; A100/H100/L40S/4090 OK) | Chai Discovery | `chai_lab.chai1.run_inference` | **VERIFIED** |
| 11 | Protein2PAM | https://github.com/Profluent-AI/protein2pam | 2025-12-06 | ~11 | Polyform-NC 1.0 (code) + CC-BY-NC 4.0 (weights) | Required (CUDA) | Profluent-AI | `PAMOracle` class | **VERIFIED** |
| 12 | OpenCRISPR-1 | https://github.com/Profluent-AI/OpenCRISPR | 2025-09-26 | ~1,190 | Bespoke ethical-use (sign-up; allows research + commercial w/ agreement) | n/a (sequence release; no weights) | Profluent-AI | `OpenCRISPR-1/` FASTA + gRNA | **VERIFIED** |
| 13 | CRISPR-Cas Atlas | https://github.com/Profluent-AI/CRISPR-Cas-Atlas | 2025-08-05 | ~25 | **CC BY-NC 4.0** (corrected from "Open") | None (data) | Profluent-AI | `crispr-cas-atlas-v1.0.json` | **VERIFIED** |
| 14a | Evo (v1) | https://github.com/evo-design/evo | 2026-03-20 | ~1,508 | Apache-2.0 | Required (FlashAttention-2) | evo-design / Arc Institute | `Evo('evo-1-131k-base')` | **VERIFIED** |
| 14b | Evo 2 | https://github.com/ArcInstitute/evo2 | 2026-03-20 | ~3,881 | Apache-2.0 | Required (CUDA 12.1+; Hopper for FP8 40B/20B/1B) | Arc Institute | `Evo2('evo2_7b')` | **VERIFIED** |
| 15 | biotite | https://github.com/biotite-dev/biotite | 2026-05-10 | ~948 | BSD-3-Clause | None | biotite-dev community | `biotite.structure`, `biotite.sequence` | **VERIFIED** |
| 16 | biopython | https://github.com/biopython/biopython | 2026-05-11 | ~5,017 | Biopython License (BSD-like) | None | Biopython community | `Bio.PDB`, `Bio.SeqIO` | **VERIFIED** |
| 17 | proteinmpnn_ddg | https://github.com/PeptoneLtd/proteinmpnn_ddg | 2025-05-21 | ~64 | MIT | Optional (CPU image available; V100 tested) | Peptone Ltd | `predict.py` (saturation ΔΔG from PDB) | **VERIFIED** |
| 18 | METL (Mutational Effect Transfer Learning) | https://github.com/gitter-lab/metl | 2026-02-03 | ~64 | MIT | Optional | Gitter lab (UW-Madison) + Romero | `train_source_model.py`, `train_target_model.py`, `inference.ipynb` | **VERIFIED** |

## License gates — non-commercial restrictions

These are usable for academic research only without further licensing:
- **CRISPR-Cas Atlas** — CC BY-NC 4.0
- **Protein2PAM** — Polyform-NC 1.0 / CC-BY-NC 4.0
- **ESM-3 default weights** — EvolutionaryScale community license is non-commercial; a commercial license is available on request.
- **OpenCRISPR-1** — bespoke "ethical use" license; permits commercial use after Profluent agreement.

## Readiness assessment by design stage

| Stage | Tool first choice | Backup | Notes |
|---|---|---|---|
| Complex structure prediction (FnCas9 + sgRNA + DNA) | **Boltz-2** | Chai-1, AF3 server | Validate against PDB 5B2O before trusting |
| Domain-scoped backbone-conditioned sequence design | **LigandMPNN** | ProteinMPNN | LigandMPNN respects DNA atoms; required for PI-domain redesign |
| Zero-shot variant scoring | **ESM-3 / ESM Cambrian** | ESM-2 (stale) | ESM-3 is the actively maintained option |
| Inverse folding for re-sequencing a domain | ESM-IF1 (stale) | ESM-3 (sequence design head) | Chunk FnCas9 by domain |
| Generative full-Cas9 sequence | ProGen2 (stale) | ESM-3 | OpenCRISPR-1 used ProGen2; weights/method are reproducible despite stale repo |
| PAM oracle for in-silico PAM evolution | **Protein2PAM** | retrain from CRISPR-Cas Atlas | Non-commercial license — academic only |
| Predicted ΔΔG / stability filter | proteinmpnn_ddg | FoldX (commercial), METL | Docker-only |
| Fine-tuned fitness head after round-1 assays | METL | custom transformer head | Has nuclease-relevant configurations |
| DNA-aware generative for operon context | **Evo 2** | Evo (v1) | Useful for sgRNA scaffold + Cas operon context |
| Protein I/O, structure parsing | **biotite** | biopython | biotite is faster + more modern |

## Likely install plan for our pipeline (NOT YET EXECUTED)

Required Python: **≥3.10**. The session shell on this machine has Python 3.9, so a separate environment is needed:

```bash
# 1. Get a Python 3.10+ interpreter
brew install python@3.11   # or: pyenv install 3.11

# 2. Make project venv with that interpreter
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. For each tool we actually want to run (lazy install — only what you'll use)
pip install fair-esm                          # ESM-2 (stale but works)
pip install esm                               # ESM-3 — requires HuggingFace gated access
pip install boltz                             # Boltz-2 complex prediction
pip install chai_lab==0.6.1                   # Chai-1
git clone https://github.com/dauparas/LigandMPNN.git external/LigandMPNN
git clone https://github.com/dauparas/ProteinMPNN.git external/ProteinMPNN
git clone https://github.com/Profluent-AI/protein2pam.git external/Protein2PAM
```

## Hardware that this project will actually need

| Stage | Minimum | Recommended |
|---|---|---|
| ESM-2 scoring (8M/35M) | CPU | M-series Mac or any GPU |
| ESM-2 650M scoring | 16 GB GPU | A6000 / H100 |
| ESM-3 small | 8 GB GPU | 24 GB |
| Boltz-2 / Chai-1 (Cas9 + sgRNA + DNA, ~1700 aa) | 40 GB GPU | H100 / L40S |
| RFdiffusion | 16 GB GPU | 40 GB |
| LigandMPNN inference | CPU OK | small GPU |

The user will need to provide GPU access. Cloud options: Lambda (4090/A100), RunPod, vast.ai, or institutional HPC.
