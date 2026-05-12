# Methods

Authoritative description of every scoring and prediction procedure used in this project. Every run must follow these exactly; deviations are documented in the run's `meta.json`.

## 1. Reference sequence and structure

- **Canonical sequence:** UniProt **A0Q5Y3** FASTA (1629 aa). Downloaded from `https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta` and SHA-256 recorded in `data/raw/manifest.tsv`.
- **Canonical structure:** PDB **5B2O** (`https://files.rcsb.org/download/5B2O.pdb`). WT FnCas9 + sgRNA + DNA, TGG PAM, 1.7 Å.
- **Coordinate frame:** PDB numbering. Note that PDB 5B2O numbering may not match UniProt numbering exactly (missing residues, alternative conformers). The `io.py` loader checks consistency at load time and refuses to proceed if the WT residue identity at any position used by `Variant.apply_mutant` disagrees with the canonical sequence.

## 2. Variant nomenclature

All variants follow the standard literature form `WTposMUT`, 1-indexed against UniProt A0Q5Y3 numbering. Multi-mutants are joined with `/` (e.g. `G1243T/E1369R/E1449H` for en31). Parsing and validation: `nuclease_design.variants` (see test suite in `tests/test_variants.py`).

## 3. Scoring procedures

### 3.1 ESM-2 zero-shot mask-marginal log-likelihood ratio

- **Model:** `esm2_t33_650M_UR50D` by default. Optionally `esm2_t36_3B_UR50D` for the higher-accuracy ablation.
- **Procedure (per variant V = WTposMUT):**
  1. Build masked input: original sequence with position `pos − 1` replaced by `<mask>`.
  2. Forward pass; read softmax logits at the mask position.
  3. Score `LLR(V) = log P(MUT | masked) − log P(WT | masked)`.
- **Multi-mutant:** independent-marginal score = sum of single-mutant LLRs. (Documented limitation: independence assumption is wrong for epistatic mutations; M4 milestone explicitly tests epistasis.)
- **Ensembling:** for ESM-1v fairness comparisons, average across the 5 ESM-1v checkpoints; for ESM-2 we use a single 650M model unless ablation explicitly switches.
- **Determinism:** PyTorch with `torch.use_deterministic_algorithms(True)`, CUDA seed fixed.
- **Numerical precision:** fp16 inference; fp32 for the final softmax + LLR computation.

### 3.2 ESM-IF1 inverse-folding score

- **Model:** `esm_if1_gvp4_t16_142M_UR50` (Hsu et al. 2022).
- **Procedure:** condition on backbone atoms of PDB 5B2O for the residue's local neighborhood; compute conditional log-likelihood of the mutant identity vs WT.
- **Context handling:** because of the historically practical ~1000-residue ceiling, we chunk FnCas9 (1629 aa) into overlapping 512-residue windows when needed. The window for any scored residue includes ±256 residues of context; if the residue is within 256 of a chain terminus we shift the window to keep it centered.

### 3.3 LigandMPNN sampling and scoring

- **Repo:** `dauparas/LigandMPNN`, vendored under `external/LigandMPNN/`.
- **Model:** default v_32_010.pt checkpoint unless overridden.
- **Context:** target DNA + sgRNA from PDB 5B2O are included as ligand atoms.
- **Sampling:** `run.py` with `--temperature 0.1 0.2 0.3` (three sweeps), 5,000 sequences per sweep at the designed-residue mask. Designed residues vary per milestone; see design-plan.md.
- **Per-mutant scoring:** `score.py` against the variant sequence threaded onto the WT backbone; returns log-likelihood under LigandMPNN's distribution. Higher = better.

### 3.4 ProteinMPNN_ddg (Peptone Ltd)

- **Repo:** `PeptoneLtd/proteinmpnn_ddg`, Docker `ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base`.
- **Procedure:** saturation-mutagenesis ΔΔG against PDB 5B2O, output one row per (position, residue) pair. We extract only the rows for variants in our pool.
- **Filter threshold:** drop variants with predicted ΔΔG > **+3 kcal/mol** (configurable in `configs/design.yaml`).

### 3.5 Boltz-2 structure prediction

- **Repo:** `jwohlwend/boltz`.
- **Input YAML:** one file per variant, listing the protein chain (with variant applied) + sgRNA sequence + dsDNA target with the relevant PAM.
- **Output:** mmCIF complex prediction. Read pLDDT per residue, ipTM for the Cas9-DNA interface.
- **Cross-validation:** every 5th variant is re-predicted with Chai-1 and the per-residue pLDDT agreement is recorded.

### 3.6 Chai-1

- **Package:** `chai_lab==0.6.1` (Apache-2.0).
- **Entry point:** `chai_lab.chai1.run_inference`.
- **Input:** same FASTA as Boltz-2 (protein + sgRNA + DNA).

### 3.7 Protein2PAM (PAM oracle)

- **Repo:** `Profluent-AI/protein2pam`. License: Polyform-NC 1.0 (non-commercial only). Document this in any results that use the oracle.
- **Class:** `PAMOracle`. Input: Cas9 sequence; output: predicted PAM PWM (4 × N matrix).
- **Use in M2.3:** as a fitness oracle for in-silico evolution. Fitness = −KL(predicted PWM ‖ target PWM).

## 4. Configuration schema

All runs are driven by a YAML config under `configs/`. Mandatory keys:

```yaml
run:
  name: baseline_2026-05-12
  seed: 42
  output_dir: results/runs/2026-05-12_baseline

reference:
  uniprot_id: A0Q5Y3
  pdb_id: 5B2O
  fasta_path: data/raw/A0Q5Y3.fasta

scorers:
  - name: esm2
    model: esm2_t33_650M_UR50D
    precision: fp16
  - name: ligandmpnn
    checkpoint: v_32_010
    temperatures: [0.1, 0.2, 0.3]
  - name: proteinmpnn_ddg
    pdb: data/raw/5B2O.pdb
    max_ddg: 3.0

design_region:
  positions: [1230, 1240, 1243, ...]   # explicit positions, or a range
```

The CLI (to be implemented) reads this and dispatches.

## 5. Run metadata (`meta.json`)

Every `results/runs/<name>/` directory contains a `meta.json` written by the pipeline runner:

```json
{
  "run_name": "baseline_2026-05-12",
  "started_at_utc": "2026-05-12T18:42:00Z",
  "finished_at_utc": "2026-05-12T19:12:33Z",
  "git_sha": "<full-sha>",
  "config_path": "configs/baseline.yaml",
  "config_sha256": "...",
  "python_version": "3.11.11",
  "torch_version": "2.5.1+cu121",
  "gpu": "NVIDIA H100 80GB",
  "cuda_version": "12.4",
  "pip_freeze_path": "results/runs/baseline_2026-05-12/pip-freeze.txt",
  "input_hashes": {
    "data/raw/A0Q5Y3.fasta": "sha256:...",
    "data/raw/5B2O.pdb": "sha256:..."
  },
  "model_weight_hashes": {
    "esm2_t33_650M_UR50D.pt": "sha256:..."
  },
  "random_seed": 42,
  "tool_versions": {
    "boltz": "1.2.3",
    "ligandmpnn": "1.0.0",
    "proteinmpnn_ddg": "1.0.0_base"
  }
}
```

## 6. Determinism and seeds

- Single global seed passed to every scorer.
- `torch.manual_seed(seed)`, `numpy.random.seed(seed)`, Python `random.seed(seed)`.
- `torch.use_deterministic_algorithms(True)` for inference.
- Sampling procedures (LigandMPNN sampling, Protein2PAM evolution) record their internal seed and the resulting state.

## 7. Numerical conventions

- All log-likelihoods in **natural log** (nats).
- All ΔΔG in **kcal/mol**.
- All distances in **angstroms** (Å).
- All PAM PWMs normalised per-column (sum to 1).
- Higher score = better in **every** scorer's output; if a tool returns lower=better, the wrapper inverts before storing.

## 8. Out-of-scope methods

- **Free-energy MD perturbations** (FEP+, Amber TI): too expensive for design-loop scale. May appear in retrospective validation.
- **EVE / Tranception-style MSA models**: not used; FnCas9 has limited usable MSA and our pipeline is structure-conditioned.
- **GNN-based DDG (DDGPredictor, FoldX-ML)**: superseded by proteinmpnn_ddg in our hands. Could add as ablation.
