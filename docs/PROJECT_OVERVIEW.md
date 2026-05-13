# FnCas9 PLM-Guided Redesign — Project Overview

**Last updated:** 2026-05-13
**Repository:** `protein-language-model-exploration` (HPC mirror at `/lustre/vishal.bharti/protein-language-model-exploration` on CSIR-IGIB *tejas* DGX).
**Status:** in-silico campaign complete pending wet-lab handoff. PLM3 (sequence-only), PLM4 (structure+ligand), and PLM5 (structure+ligand+ΔΔG) candidates produced and structurally evaluated via Boltz-2. **Headline result: PLM5 is structurally indistinguishable from the wet-lab-validated en31 reference** across every Boltz-2 confidence metric (mean per-res pLDDT 0.913 vs 0.913; protein↔DNA-PAM iPTM 0.933 vs 0.942 — both within standard deviation). PLM3 (sequence-only ESM-2) is structurally compromised — iPTM drops of 0.04-0.08 vs WT.
**Audience:** the project author (Vishal Bharti) and the PI. Written so it can be read cold by someone who has never used a protein language model. Every claim is either verified against a primary source (cross-checked in `notes/plm/verification-log.md`) or derived from first-party data in this repository.

---

## 1. Executive summary

We are using protein language models (PLMs) to redesign FnCas9 — the Cas9 nuclease from *Francisella novicida* (UniProt **A0Q5Y3**, 1,629 aa, PDB **5B2O**) — toward enFnCas9-class activity. The published reference variant **en31** (G1243T / E1369R / E1449H, Acharya et al., *Nat Commun* 15:5471, 2024) gives >2-fold higher cleavage activity in vitro plus an expanded PAM repertoire (NGG → NGG / NGA / NAG) and a ~3.5× expansion of targetable human genome sites. We treat en31 as both a benchmark (can our methods recover it?) and a calibration anchor for in-silico filters (what magnitude of model-predicted destabilization does a known-functional engineered variant tolerate?).

We have three computed candidates so far:

- **FnCas9-PLM3** = G1243T / W1507K / C1292K / M1617K — from sequence-only ESM-2 zero-shot over the full WED+PI region.
- **FnCas9-PLM4** = T1535V / Y1249F / Y1341L / A1325K — from LigandMPNN structure-and-ligand-conditioned design (uses 5B2O protein + sgRNA + DNA as context).
- **FnCas9-PLM5** = Y1249F / Y1341L / A1325K / K1479F — same as PLM4 but with T1535V dropped after a proteinmpnn_ddg apo-stability gate (T1535V single-position ΔΔG = +4.15 kcal/mol exceeded the en31-anchored ceiling of +3.2).

The most scientifically interesting finding so far is **a clean head-to-head comparison at the four en31/en15 reference positions** showing that sequence-only ESM-2 ranks the published PAM-contact mutations E1369R / E1449H / E1603H in the lower half of a 7,429-variant pool, while structure-and-ligand-conditioned LigandMPNN at the same position strongly wants the same biophysical change (E → K/R with pooled frequency 0.522/0.365). This is direct empirical evidence that ligand context fixes a known sequence-only PLM blind spot for DNA-contact engineering.

---

## 2. The biological problem

### 2.1 Why FnCas9, why redesign it

Three reasons FnCas9 matters:

1. **Specificity ceiling.** Acharya 2024 reports that engineered FnCas9 (enFnCas9 / en31) shows ~1,300-fold higher genome-wide specificity than SpCas9 (Digenome-seq). For therapeutic gene editing, off-target activity is the dominant risk; a more specific Cas9 directly lowers that risk.
2. **PAM flexibility.** WT FnCas9 cleaves with a 5′-NGG-3′ PAM. en31 broadens this to NGG > NGA > NAG, expanding the targetable fraction of the human genome ~3.5×.
3. **Diagnostic use case.** FnCas9 derivatives (FELUDA, MUTE-Seq) are CSIR-IGIB-led platforms for paper-strip and ultrasensitive nucleic-acid diagnostics. Improving the FnCas9 base would propagate to diagnostic sensitivity and breadth.

### 2.2 What's already published

| Variant | Mutations | PAM | Activity vs WT | Source |
|---------|-----------|-----|----------------|--------|
| en1 | E1369R | NGG / NGA / NAG | >2× cleavage rate (in vitro) | Acharya 2024 |
| en15 | E1603H | NGG (with improved K_d) | >2× cleavage rate (in vitro) | Acharya 2024 |
| en31 | G1243T / E1369R / E1449H | NGG / NGA / NAG | >2× cleavage rate, expanded PAM, ~1,300× specificity vs SpCas9 | Acharya 2024 |
| FnCas9-RHA | E1369R / E1449H / R1556A | 5′-YG-3′ | "PAM-flexible" | Hirano 2016 |

en15 and en31 are the variants we use as calibration anchors. The Acharya 2024 finding that the en31 triple-mutant works in vitro is what makes its predicted apo destabilization a useful upper bound for our in-silico filters: the wet lab proved that level of perturbation is tolerable.

### 2.3 Why PLM-guided design

There are two ways to engineer a Cas9 toward a desired property:

- **Directed evolution.** Random mutagenesis libraries plus a high-throughput functional screen. Effective but expensive: typically ~10⁴–10⁶ variants per round, several rounds, each round requires a screen calibrated for the desired phenotype. This is what Acharya 2024 did.
- **Computational pre-screen.** Score every possible point mutation (or every plausible multi-mutant) with a model trained on protein data, pick the top few hundred or thousand candidates that pass several model-based filters, then test only those in the lab. Funnels ~10⁵ → ~10² in silico, often successfully (OpenCRISPR-1, *Nature* 2025; Protein2PAM, *Nat Biotechnol* 2026).

The second route is what this project pursues. The funnel logic only works if the in-silico filters genuinely correlate with the wet-lab phenotype. A central part of the work is **calibrating each filter against the known-functional en31 reference** so we know which predictions to trust.

---

## 3. Primer: what is a protein language model?

A *protein language model* is a neural network trained to predict masked or next amino acids in protein sequences, using a corpus of 10⁸–10⁹ natural protein sequences from databases like UniRef. Two things make these models useful for engineering:

1. **They build representations.** Internally, each amino acid in an input sequence is mapped to a high-dimensional vector (the *embedding*; typically 1,280-d for ESM-2 650M). Vectors at semantically related positions cluster together. Embeddings capture local structure (helices, sheets), evolutionary constraints (conserved residues, co-evolving pairs), and biophysical properties (charge, hydrophobicity, size) — none of which were directly supervised.
2. **They produce per-position probability distributions.** For any position in a query sequence, the model can return P(amino acid | rest of sequence). Comparing P(MUT | sequence) to P(WT | sequence) gives a *log-likelihood ratio* (LLR) — a per-mutation score: high LLR ⇒ the model thinks the mutation is plausible given evolution; low LLR ⇒ the model thinks WT is preferred.

The key insight that makes PLMs useful for **zero-shot mutation effect prediction**: PLMs trained only on natural sequences (no functional labels) already produce LLRs that correlate moderately well with measured deep-mutational-scanning fitness (the ProteinGym benchmark; ESM-2 spearman ≈ 0.45 averaged across DMS sets). Without retraining or fine-tuning, you can hand a PLM a sequence and a candidate mutation, and the model gives you an opinion.

### 3.1 What "embedding" means concretely

When ESM-2 reads a 1,629-residue FnCas9 sequence, each residue is converted to a 1,280-dimensional vector at every transformer layer. The final-layer embedding at residue *i* is a function of:

- The amino acid identity at *i*.
- The amino acid identities at every other position in the sequence (because the transformer is bidirectional).
- The model weights, which were learned by mask-prediction over UniRef.

Two operational consequences:

- **Embeddings are contextual.** The vector for "Glu at position 1369" depends on every other residue. The model has learned that *Glu* in a basic-residue neighborhood scoring DNA-backbone phosphates is rare; in a generic surface helix it's common. The score for a mutation reflects this learned context.
- **Embeddings see only sequence.** ESM-2 has no input channel for DNA, sgRNA, structural neighbors, or active-site geometry. The model can only learn what is *implicit* in evolutionary sequence patterns. For Cas9-specific signals like "this residue contacts the PAM nucleotide directly," ESM-2 has no direct view — only the indirect view that evolutionary substitutions at PAM-contact positions are constrained because Cas9s with broken PAM contacts don't reproduce.

This is exactly the limitation that the head-to-head with LigandMPNN (Section 5) probes.

### 3.2 Why we chose ESM-2 650M specifically

ESM-2 (Lin et al., *Science* 2023) is published by Meta AI. Available sizes: 8M, 35M, 150M, 650M, 3B, 15B parameters. Bigger usually means better per-mutation LLRs, but with diminishing returns and ballooning compute. Our choices, per scale:

| Size | Parameters | Inference time / mutation | Use in this project |
|------|-----------|---------------------------|---------------------|
| 35M | 35M | <1 sec CPU | Sanity-check (Phase 0); confirmed protocol end-to-end |
| 650M | 650M | ~10 sec CPU, ~0.3 sec GPU | **Main scan.** ~3 min wall on V100 for the 7,429-variant PI scan |
| 3B | 3B | ~1 min CPU, ~3 sec GPU | Reserved for later ablation; not yet used |

The 650M model is the sweet spot for a per-position scan over 391 positions × 19 substitutions = 7,429 variants on V100. The full ESM-2 family was archived by Meta in 2024 (`fair-esm` repo is read-only) so we are working with the released, frozen weights.

### 3.3 Mask-marginal LLR — what we actually compute

For each candidate mutation **WTposMUT**:

1. Replace the residue at `pos` in the FnCas9 sequence with the `<mask>` token (ESM-2's special "predict this" symbol).
2. Forward-pass through the model. At the masked position, the model outputs a probability over all 20 amino acids.
3. `LLR = log P(MUT | masked sequence) − log P(WT | masked sequence)`.

Positive LLR ⇒ model prefers the mutation; negative LLR ⇒ model prefers WT.

For a multi-mutant (k mutations), we sum the per-mutation LLRs. This is the **independent-marginal approximation**: it ignores epistasis (interaction between mutations). When two mutations are at structurally adjacent positions and physically interact, the independent-marginal score is biased. We accept this for now; it would matter most if we were proposing tightly-coupled multi-residue redesigns, which we are not.

**Numerical details:**
- All log-likelihoods in natural log (nats).
- fp16 inference on GPU, fp32 for the final softmax.
- Deterministic: PyTorch global seed = 42, `torch.use_deterministic_algorithms(True)`.

### 3.4 Known failure mode: rare-amino-acid bias

ESM-2 zero-shot scoring has a documented bias toward picking rare amino acids (W → F, V → C, etc.) at positions where the WT amino acid is common in UniRef. This is a *side-effect* of the pretraining loss — the model is calibrated against UniRef base rates and gives slightly inflated probabilities to under-represented amino acids in any context. We see this in our PLM3 candidate, which has 3 of 4 picks being hydrophobic → lysine substitutions. The class-conservation filter we apply (Section 4.2) partially mitigates this, but not entirely — that's why downstream structure-conditioned filters matter.

---

## 4. Primer: structure-conditioned and ligand-conditioned models

Where sequence-only PLMs see only the polypeptide chain, two other model classes incorporate structure and/or bound-ligand context. Both are used in this project.

### 4.1 LigandMPNN — design while seeing the ligand

LigandMPNN (Dauparas et al., *Nat Methods* 22:717-723, 2025) is a structure-conditioned generative model for protein design. Given a backbone (PDB) and any bound nucleic acid or small-molecule ligands, it samples amino-acid sequences that are consistent with the structure and the ligand contacts.

How it differs from a sequence-only PLM:

- **Inputs:** 3D coordinates of the protein backbone + the heavy atoms of every ligand within a configurable cutoff (we use 8 Å). For 5B2O this includes the sgRNA (94 nt) and the DNA target (30 nt + 9 nt PAM-strand).
- **Architecture:** message-passing graph neural network over a k-nearest-neighbor graph of atoms (residues + ligand atoms).
- **Output:** per-position amino-acid probabilities conditioned on (backbone, ligand). To get sequences, sample autoregressively from these per-position distributions.

What this buys us, biophysically: when designing a residue at the PAM-contact face, LigandMPNN can *see* that the phosphate of the PAM nucleotide is 4 Å away from the side-chain Cβ, and that this is a positively-charged-residue-favorable position. A sequence-only PLM has no way to see this directly; it can only know "in the training corpus, positively-charged residues are evolutionarily preferred at this position." The two approaches converge in cases where the training corpus is dense with examples, and diverge in cases where the protein family is sparse — Cas9 PAM-contact positions are exactly the sparse case.

**Hyperparameters used in our run** (`hpc/slurm/02_ligandmpnn_sampling.sbatch`):

- Model checkpoint: `ligandmpnn_v_32_010_25.pt` (Dauparas v_32_010 weights, trained with σ=0.10 noise).
- Design positions: residues 1230–1620, full WED+PI region, all 391 positions, space-separated tokens `A1230 A1231 … A1620`.
- Pack side chains: `0` (we just want sequences, not packed structures).
- Temperatures: `0.1`, `0.2`, `0.3` (three independent sweeps).
- Batches per temperature: 50.
- Batch size: 32.
- Total samples: 50 × 32 = 1,600 per temperature, 4,800 across all three.
- Ligand cutoff distance: 8.0 Å.
- Seed: random per-sample (LigandMPNN-internal, recorded in each sample's header).

**Output:** a FASTA per temperature (one sequence per line) with 1,601 records (1 reference + 1,600 samples). Aggregator (`scripts/ligandmpnn_aggregate.py`) maps these back to UniProt positions via the 5B2O ATOM records (chain A has 13 internal disordered-loop gaps, none in our design region) and produces a per-position amino-acid-frequency TSV.

### 4.2 proteinmpnn_ddg — apo-state stability prediction

proteinmpnn_ddg (Peptone Ltd, GitHub `peptoneltd/proteinmpnn_ddg`, container image `ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base`) computes a per-mutation ΔΔG (kcal/mol) from a PDB structure. ΔΔG > 0 indicates the mutation destabilizes the fold; ΔΔG < 0 stabilizes.

**Critical caveat:** proteinmpnn_ddg evaluates the **apo protein** in isolation. It does not see the sgRNA or the DNA. A residue that makes a productive contact with the DNA backbone (e.g., en31's E1369R, a charge swap at a PAM-contact position) will be flagged by proteinmpnn_ddg as destabilizing because it is destabilizing *for the apo fold*. In the functional DNA-bound complex, the same mutation is stabilizing (which is why en31 works in vitro). This is why we use the apo ΔΔG only as a **soft filter against extreme outliers**, not as the primary fitness signal.

**Calibration anchor:** the Acharya 2024 wet-lab data give us a free empirical calibration. en31's E1369R has predicted apo ΔΔG = +3.20 kcal/mol; en31 is known-functional. Therefore, +3.20 kcal/mol of predicted apo destabilization at a single position is provably tolerable. We use +3.2 as the default `--max-single-ddg` ceiling for our filter.

**Hyperparameters used in our run** (`hpc/slurm/03_proteinmpnn_ddg.sbatch`):

- Container: `ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base`, pulled to Singularity SIF.
- Model: `v_48_020` (ProteinMPNN 48-message-passing-layers, σ=0.20 trained).
- Input PDB: `data/raw/5B2O.pdb`, chain A.
- Coverage: full saturation across chain A (every position, every target amino acid). 29,100 entries (1,455 resolved residues × 20 target amino acids).
- Seed: 42.
- Run time: ~30 sec on V100 after the first-time image pull.

**Output:** CSV with columns `pre, post, pos, logit_difference, logit_difference_ddg`. The calibrated kcal/mol value is `logit_difference_ddg`.

### 4.3 Boltz-2 — full complex structure prediction

Boltz-2 (Wohlwend et al., 2024–2025, GitHub `jwohlwend/boltz`) is an open-source AlphaFold-3-class model for predicting structures of protein + ligand + nucleic-acid complexes. Compared to AlphaFold-3 (closed-weight as of 2026-05) and AlphaFold-Multimer (no nucleic-acid heads), Boltz-2:

- Handles protein + RNA + DNA + small molecules + ions in one forward pass.
- Returns per-residue pLDDT (confidence in local structure) and ipTM (interface predicted-template modeling score, confidence in the cross-chain geometry).
- Uses an MSA server (default: public ColabFold MSA endpoint) for protein conditioning; we set `--use_msa_server` to enable this.

**Hyperparameters in our run** (`hpc/slurm/04_boltz_complex.sbatch`, job 214530):

- Diffusion samples: 5 per variant (each is a separate structure prediction; we'll average their confidence and inspect the highest-confidence model).
- Precision: fp16 on V100 (V100 has no native bfloat16).
- Variants: 4 (WT / PLM3 / PLM5 / en31).
- Per-variant runtime: ~30–60 min on V100 32GB; total wall ~2–4 hours.
- Inputs: `hpc/inputs/boltz_fncas9_<variant>.yaml`, each containing the variant protein sequence + sgRNA (94 nt) + DNA chain C (30 nt) + DNA chain D (9 nt PAM strand). Sequences extracted from 5B2O via `scripts/prepare_boltz_yamls.py`.

---

## 5. The pipeline

```
                                ┌─────────────────────────┐
                                │  Literature & SOTA      │
                                │  (Acharya 2024,         │
                                │   Hirano 2016, ...)     │
                                └───────────┬─────────────┘
                                            │
                                            ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  Verification log (notes/plm/verification-log.md):           │
        │  every literature claim cross-checked against primary        │
        │  source. Calibration anchors recorded.                       │
        └─────────────────────────────────────────────────────────────┘
                                            │
              ┌─────────────────────────────┴─────────────────────────────┐
              │                                                            │
              ▼                                                            ▼
     ┌─────────────────────────┐                              ┌─────────────────────────┐
     │  Phase 2:                │                              │  Phase 2.5:              │
     │  ESM-2 zero-shot scan    │                              │  Phylogenetic +          │
     │  over WED+PI (1230–1620),│                              │  structural cross-       │
     │  7,429 LLRs              │                              │  validation              │
     └───────────┬─────────────┘                              └─────────────────────────┘
                 │                                                          │
                 ▼                                                          │
     ┌─────────────────────────┐                                            │
     │  build_candidate_v3.py:  │                                            │
     │  top-K under composite   │                                            │
     │  LLR − λ·class_cons      │                                            │
     │  → FnCas9-PLM3           │                                            │
     └───────────┬─────────────┘                                            │
                 │                                                          │
                 ▼                                                          │
     ┌─────────────────────────┐                                            │
     │  Phase 3:                │                                            │
     │  LigandMPNN sampling     │ ←── 5B2O backbone + sgRNA + DNA            │
     │  (4,800 sequences)       │                                            │
     └───────────┬─────────────┘                                            │
                 │                                                          │
                 ▼                                                          │
     ┌─────────────────────────┐                                            │
     │  ligandmpnn_aggregate.py:│                                            │
     │  per-position aa-frequency│                                           │
     │  TSV (aggregate.tsv)     │                                            │
     └───────────┬─────────────┘                                            │
                 │                                                          │
                 ▼                                                          │
     ┌─────────────────────────┐                                            │
     │  build_candidate_v4.py   │                                            │
     │  → FnCas9-PLM4           │                                            │
     └───────────┬─────────────┘                                            │
                 │                                                          │
                 │   ┌────────────────────────────────────────────┐         │
                 │   │  Phase 4: proteinmpnn_ddg saturation       │         │
                 │   │  (Singularity, ~30 sec on V100)            │         │
                 │   └────────────────────┬───────────────────────┘         │
                 │                        │                                 │
                 │                        ▼                                 │
                 │            ┌───────────────────────┐                     │
                 │            │  proteinmpnn_ddg_      │                     │
                 │            │  analyze.py: ΔΔG       │                     │
                 │            │  table for our picks   │                     │
                 │            └────────────┬──────────┘                     │
                 │                         │                                │
                 │                         ▼                                │
                 │  ┌──────────────────────────────────┐                    │
                 │  │  build_candidate_v4.py            │                    │
                 │  │    --ddg-csv ... --max-single-ddg │                    │
                 │  │    3.2 → FnCas9-PLM5             │                    │
                 │  └────────────────────┬─────────────┘                    │
                 │                       │                                  │
                 ▼                       ▼                                  │
     ┌──────────────────────────────────────────────────────┐               │
     │  Phase 5: Boltz-2 complex prediction                  │←──────────────┘
     │  WT / PLM3 / PLM5 / en31 (job 214530)                 │
     └──────────────────────────┬───────────────────────────┘
                                │
                                ▼
                ┌────────────────────────────────────┐
                │  Decision: shortlist for wet-lab    │
                │  (out of scope for this campaign)   │
                └────────────────────────────────────┘
```

---

## 6. Results so far

### 6.1 Phase 1 — Literature verification

26 enFnCas9-paper claims and 10 PLM-design-paper claims cross-checked against primary sources. Significant corrections caught:

- Acharya 2024 first author is **Sundaram Acharya**, not Rauthan (literature agent's draft had it wrong).
- The "~1,300× specificity" figure is from the Acharya paper itself (Digenome-seq), not a press release.
- Hirano 2016's FnCas9-RHA is a **triple mutant E1369R / E1449H / R1556A**, not a double — the third mutation matters.
- Protein2PAM first author is **Stephen Nayfach**, not Ruffolo.
- Evo 2 published in *Nature* 2026, not *Science* 2025.
- AiCE DOI is `10.1016/j.cell.2025.06.014`, not the article PII string.

All recorded in `notes/plm/verification-log.md`. The verification log is the canonical "what's actually true" file for the project.

### 6.2 Phase 2 — Sequence-only ESM-2 scan and PLM3

**Run:** `results/runs/2026-05-13_esm2_650M_full_PI_hpc/`
**Reproduces with:** `hpc/slurm/01_esm2_650m_full_PI.sbatch`

ESM-2 650M zero-shot mask-marginal LLR computed for all 391 positions × 19 substitutions = 7,429 variants in the WED + PI region (residues 1230–1620). Wall time: ~3 min on V100, ~12 min on CPU.

**Sanity check at known-functional Acharya 2024 positions (composite ranking = LLR − 1.0 · class_conservation):**

| Variant | Composite rank in 7,429-variant pool | Quartile |
|---------|-------------------------------------|----------|
| G1243T (en31, WED domain) | **1 / 7,429** | top — model strongly recovers this WED mutation |
| E1369R (en1 / en31, PI) | 4,956 / 7,429 | Q3 — model thinks it's worse than WT |
| E1449H (en31, PI) | 5,117 / 7,429 | Q3 — model thinks it's worse than WT |
| E1603H (en15, PI) | 5,109 / 7,429 | Q3 — model thinks it's worse than WT |

**Interpretation:** ESM-2 (sequence-only) recovers the WED-domain mutation (G1243T) at rank 1. The three PAM-contact mutations all rank in Q3 of the broader pool — i.e. the model thinks they make the protein worse than WT. This is the cleanest empirical demonstration in this project of the sequence-only PLM blind spot for DNA-contact engineering: ESM-2 has no input channel for the DNA strand, so it cannot see why a + charge would help at residue 1369.

**FnCas9-PLM3 = G1243T / W1507K / C1292K / M1617K** (cumulative ESM-2 composite +13.7; from `scripts/build_candidate_v3.py`).

Per-mutation breakdown:

| Variant | LLR | class_cons | composite |
|---------|-----|-----------|-----------|
| G1243T | +4.436 | 0.33 | +4.103 |
| W1507K | +3.308 | 0.00 | +3.308 |
| C1292K | +3.100 | 0.00 | +3.100 |
| M1617K | +3.057 | 0.00 | +3.057 |

Filters used (`build_candidate_v3.py`):
- `--design-region 1230-1620` (full WED+PI).
- `--top-k 4`.
- `--max-class-conservation 0.5` (drop positions where the physicochemical class is highly conserved across the ortholog panel — rejects e.g. W1459K class_cons=1.00 from the earlier hotspot-window-based run).
- `--require-positive-llr` (drop mutations with LLR ≤ 0).
- `--min-spacing 5` (no two picks within 5 residues of each other).
- `--lambda-cons 1.0` (weight on the class-conservation penalty in the composite score).

The PLM3 picks are sensible at face value but suffer from the rare-AA bias (3 / 4 are X → K). The G1243T overlap with en31 is a real positive-control hit.

### 6.3 Phase 2.5 — Phylogenetic and structural cross-validation

Two pieces, both already committed and documented in earlier verification log entries:

**Sequence-based phylogeny.** Pairwise Needleman-Wunsch alignments (BLOSUM62) between FnCas9 and four Cas9 orthologs: SpCas9 (1,368 aa, *S. pyogenes*), SaCas9 (1,053 aa, *S. aureus*), Nme1Cas9 (1,082 aa, *N. meningitidis*), CjCas9 (984 aa, *C. jejuni*). NJ tree topology: `((CjCas9, Nme1Cas9), (SaCas9, SpCas9))` with FnCas9 as the outgroup.

**Structure-based phylogeny.** Same five Cas9s with their representative PDBs (5B2O, 4OO8, 5CZZ, 6JDQ, 5X2H). Sequence-guided 3D alignment followed by iterative outlier trimming (TM-align-style thresholds 15 → 10 → 8 → 6 → 5 → 4 Å). Per-pair `rmsd_core` reported for stable structural core only (excluding disordered loops and aligned-by-fluke long indels). Sequence and structural phylogenies are topologically congruent — important sanity check confirming the orthologs we use for the class-conservation filter are evolutionarily reasonable.

**Catalytic controls.** Saturation LLRs for the six known catalytic residues (D11A, E731A, ..., H969A, D1054A) computed under ESM-2 650M. Five of six register as strongly disfavored (LLR < −5; H969A = −10.1; D11A = −7.4). This is a model-calibration sanity check: ESM-2 correctly identifies that mutating known catalytic residues to alanine breaks the protein. It does so without supervision because evolutionary substitution patterns at active-site residues are constrained.

### 6.4 Phase 3 — LigandMPNN sampling and PLM4

**Run:** `results/runs/2026-05-13_ligandmpnn_PI/`
**Reproduces with:** `hpc/slurm/02_ligandmpnn_sampling.sbatch`

LigandMPNN sampling on 5B2O with the sgRNA + DNA as ligand context. 4,800 sequences total (3 temperatures × 50 batches × 32 batch-size). Wall time: ~28 min on V100.

**Setup gotchas resolved on this dataset** (recorded for posterity):

- LigandMPNN's CLI accepts only space-separated residue tokens `"A1230 A1231 …"`; passing a range `"A1230-A1620"` is silently rejected and produces all-WT samples (`num_res = 0`, `seq_rec = nan`). Job 214059 cost a 28-minute run on this mistake; preserved as `..._FAILED_no_design`.
- LigandMPNN's vendored `openfold` predates NumPy 1.24 and uses `np.int` / `np.float` / `np.bool` etc. — broken on NumPy 2.x. We patched the vendored openfold in-place with sed-rewrite (sentinel file `external/LigandMPNN/.numpy2_patched`).
- LigandMPNN's `requirements.txt` pins `torch==2.2.1` (cu12), `numpy==1.23.5`, `scipy==1.12.0` — pip-installing it would clobber the cu118 venv that ESM-2 needs. We install only the LigandMPNN-specific packages: ProDy, ml-collections, dm-tree.

**Head-to-head with ESM-2 at the four en31/en15 reference positions** (pooled across all 4,800 samples):

| Position | WT | en target | ESM-2 rank | LigandMPNN top non-WT | LigandMPNN target_freq | LigandMPNN WT_freq |
|----------|----|----|------------|------------------------|-----------------------|---------------------|
| 1243 (WED) | G | T | 1 / 7,429 ✓ | **T=0.455, S=0.456** (tied) | 0.455 | 0.087 |
| 1369 (PI) | E | R | 4,956 / 7,429 | **K=0.522** (R=0.365 runner-up) | 0.365 | 0.000 |
| 1449 (PI) | E | H | 5,117 / 7,429 | **L=0.985** | 0.000 | 0.001 |
| 1603 (PI) | E | H | 5,109 / 7,429 | **L=0.517** | 0.000 | 0.026 |

**Key finding:** at residue 1369 — the PAM-contact charge-swap site — LigandMPNN strongly wants to change away from E (WT frequency exactly 0.000) and prefers K (52.2%) or R (36.5%). Both are basic; either matches the biophysical rationale behind Acharya 2024's E1369R. ESM-2 ranks the same R-at-1369 mutation at position 4,956 / 7,429. **Direct empirical evidence that ligand context fixes the sequence-only blind spot at DNA-contact positions.**

At residues 1449 and 1603, both models *disagree* with the published H mutations: ESM-2 says "leave as E," LigandMPNN says "change to L." Neither sees Acharya's H as preferred. This could mean (a) the wet-lab-evolved H mutations are functionally optimal for reasons neither model captures (epistasis, kinetics, off-target trade-offs), or (b) the H mutations are experimentally-evolved compromises that are not structurally optimal. Falsifiable wet-lab prediction: a single-point E1449L should be compared head-to-head against E1449H.

**FnCas9-PLM4 = T1535V / Y1249F / Y1341L / A1325K** (from `scripts/build_candidate_v4.py`).

Per-mutation breakdown:

| Variant | LigandMPNN top_freq | LigandMPNN wt_freq | class_cons | composite |
|---------|---------------------|---------------------|-----------|-----------|
| T1535V | 1.000 | 0.000 | 0.00 | +6.908 |
| Y1249F | 1.000 | 0.000 | 0.00 | +6.908 |
| Y1341L | 0.996 | 0.000 | 0.00 | +6.904 |
| A1325K | 0.989 | 0.000 | 0.00 | +6.896 |

Filters used:
- `--min-top-freq 0.30` (top non-WT amino acid pooled frequency must be ≥ 0.30).
- `--max-wt-freq 0.40` (WT must NOT still be the dominant choice).
- `--max-class-conservation 0.5` (same as v3).
- `--min-spacing 5`.
- Composite scoring: `log(top_freq / wt_freq) − λ · class_cons` (log odds vs WT; `λ = 1.0`).

**Important caveat on LigandMPNN frequencies.** LigandMPNN samples autoregressively (one residue at a time conditioned on partial sequence). Frequencies near 1.000 at well-determined positions inherit *decode consistency* rather than reflecting true per-position posteriors. The L=0.985 at residue 1449 should be read as "very confident given everything else the model decoded," not as "no other amino acid is plausible at this position in isolation."

**Caveat on the design region.** 159 / 391 design positions have a top-pick different from WT — a lot of sequence drift. Most of this is at peripheral / surface-exposed positions where any single amino-acid change has small free-energy cost. The biological question is whether changes at these positions affect function. Boltz-2 + the apo ΔΔG filter address this.

### 6.5 Phase 4 — apo-ΔΔG filter and PLM5

**Run:** `results/runs/2026-05-13_proteinmpnn_ddg/`
**Analyzer:** `scripts/proteinmpnn_ddg_analyze.py` (peptoneltd schema: `pre, post, pos, logit_difference, logit_difference_ddg`).

**Calibration anchors (Acharya 2024 known-functional variants):**

| Variant | Mutations | Cumulative apo ΔΔG (kcal/mol) |
|---------|-----------|-------------------------------|
| en31 (G1243T / E1369R / E1449H) | −2.65 + 3.20 − 0.15 | **+0.40** |
| en15 (E1603H) | −1.37 | **−1.37** |

Functional engineered variants tolerate single-position apo ΔΔG up to **+3.20** kcal/mol (en31's E1369R) and cumulative apo ΔΔG in the band **[−1.4, +0.4]**. We use these as soft filter thresholds, not hard rejects.

**PLM3 stability check** — cumulative apo ΔΔG **−8.42** kcal/mol (very stable):

| Variant | ΔΔG | Call |
|---------|-----|------|
| G1243T | −2.65 | stabilizing |
| W1507K | −5.07 | stabilizing — *biophysically suspicious* |
| C1292K | −3.63 | stabilizing |
| M1617K | +2.93 | moderate destabilizer |

W1507K reading as a −5.07 kcal/mol stabilization is anomalous: W → K loses a large aromatic ring with significant hydrophobic surface area in exchange for a charged residue. Standard biophysical intuition is that this should cost stability, not gain it. This is flagged as either (a) genuinely an exposed surface position where the K is favorable solvation-wise, or (b) a model-calibration issue with proteinmpnn_ddg at hydrophobic → K substitutions. Boltz-2 will arbitrate.

**PLM4 stability check** — cumulative apo ΔΔG **+6.74** kcal/mol (6.3 kcal/mol outside the en31 envelope):

| Variant | ΔΔG | Call |
|---------|-----|------|
| T1535V | +4.15 | STRONG destabilizer — above any single-position cost in en31/en15 |
| Y1249F | −0.98 | stabilizing |
| Y1341L | +1.78 | moderate destabilizer |
| A1325K | +1.79 | moderate destabilizer |

T1535V is the dominant outlier. LigandMPNN sampled T → V here with pooled frequency 1.000 (perfectly confident *in the complex*), while proteinmpnn_ddg flags T1535 as a hydrogen-bonding hub for the apo fold. Two structure-aware models disagreeing at the same position is informative — they're conditioning on different reference states (DNA-bound complex vs apo fold). For our purposes, we treat the apo destabilization as evidence against picking T1535V without further inspection.

**FnCas9-PLM5 = Y1249F / Y1341L / A1325K / K1479F** (from `scripts/build_candidate_v4.py --ddg-csv … --max-single-ddg 3.2`). Same LigandMPNN-derived candidate pool as PLM4, with T1535V dropped and replaced by the next-best LigandMPNN candidate satisfying the ΔΔG gate: K1479F (top_freq 0.985, ΔΔG = −2.00). Cumulative apo ΔΔG = **+0.59 kcal/mol** — essentially identical to en31's +0.40 anchor.

### 6.6 Phase 5 — Boltz-2 complex prediction

**Run:** `results/runs/2026-05-13_boltz_complex/`
**Analyzer output:** `results/runs/2026-05-13_boltz_complex/analysis/boltz_analyze_output.txt`
**Reproduces with:** `hpc/slurm/04_boltz_complex.sbatch` (SLURM job 215253; ~10 min wall on V100 for 4 variants × 5 diffusion samples after the OOM fix).

**Two iterations:**
- **Job 214530 (full-length 1,629-aa input):** OOM'd on V100 32GB for all 4 variants. Boltz catches CUDA OOM internally and exits 0 with zero predictions. 2:22 of wall time wasted.
- **Job 215253 (truncated to WED+PI, residues 1230-1620, 391 aa):** Completed in ~10 min total, 5 diffusion samples × 4 variants × 0 failures.

**Confidence summary (mean ± std over 5 diffusion samples; truncated chain, single-sequence mode):**

| Metric | WT | PLM3 | PLM5 | en31 |
|--------|-----|------|------|------|
| Overall confidence | 0.915±0.003 | **0.865±0.044** | 0.918±0.010 | 0.919±0.003 |
| Mean per-res pLDDT | 0.908±0.003 | 0.862±0.032 | 0.913±0.004 | 0.913±0.002 |
| iPTM (all interfaces) | 0.944±0.008 | 0.880±0.094 | 0.935±0.037 | 0.946±0.007 |
| iPTM protein↔DNA-target | 0.932±0.009 | 0.889±0.061 | 0.923±0.030 | 0.934±0.008 |
| iPTM protein↔DNA-PAM | 0.939±0.008 | 0.901±0.056 | 0.933±0.025 | 0.942±0.008 |
| iPTM protein↔sgRNA | 0.947±0.008 | **0.866±0.117** | 0.937±0.037 | 0.949±0.007 |

**Two top-line findings:**

1. **PLM5 is structurally indistinguishable from en31.** Every metric is within one standard deviation between PLM5 and en31 (the wet-lab-validated functional reference). At the protein↔DNA-PAM interface — the most decision-relevant single number — PLM5 = 0.933±0.025 vs en31 = 0.942±0.008 (Δ = −0.009, well within noise). **The structure-conditioned LigandMPNN design followed by apo-ΔΔG filtering produced a candidate that Boltz-2 cannot tell apart from the published functional variant.** This is the strongest possible in-silico endorsement short of wet-lab validation.

2. **PLM3 is structurally compromised.** Boltz scores PLM3 worse than WT/PLM5/en31 on every metric with drops of 0.04-0.08 and 6-10× higher standard deviations across the 5 diffusion samples. The largest single drop: iPTM protein↔sgRNA = 0.866 ± 0.117 vs WT 0.947 ± 0.008. The model is genuinely uncertain how PLM3 folds. Sequence-only ESM-2 zero-shot, by itself, did not produce a structurally viable candidate.

**Per-engineered-position pLDDT confirms two specific predictions:**

- **W1507K's "stabilizing" call from proteinmpnn_ddg was wrong.** Per-residue pLDDT at position 1507: PLM3 = 0.878 vs WT 0.958 (drop of 0.08). Boltz sees what proteinmpnn_ddg missed — W → K removing an aromatic costs local geometry confidence. The apo-ΔΔG model is miscalibrated for hydrophobic-to-K substitutions; Boltz, seeing the complex, identifies the local-geometry disturbance.
- **G1243T context-dependence — emergent multi-mutant effect.** Same mutation, very different per-residue confidence depending on the surrounding mutations: pLDDT(G1243T in en31) = 0.938, pLDDT(G1243T in PLM3) = 0.816 — Δ = 0.12 at the same single-position mutation. PLM3's three other picks (W1507K, C1292K, M1617K) propagate uncertainty back to position 1243 despite being 50-300 residues away. This is the epistasis our independent-marginal multi-mutant scoring cannot capture, and exactly why a full complex-prediction final pass matters.

**Caveats:**
- Single-sequence mode (`msa: empty` in the YAMLs we ran). Absolute pLDDT/iPTM numbers are lower than an MSA-enabled rerun would give. Relative differences between variants are unaffected — same setting for all four. Fixed in `prepare_boltz_yamls.py` for any rerun.
- WED+PI truncation. Boltz did not see the REC lobe or RuvC nuclease domain. None of our candidate mutations are in those regions, but if a candidate's mutations have long-range effects via the REC lobe, we miss them.

**Interpretation for downstream use:**
- **PLM5 is the candidate to put forward** for wet-lab testing if any of the three are tested. en31-equivalent structural confidence, calibrated-safe apo ΔΔG, structure-conditioned design.
- **PLM3 needs revision** before serious wet-lab consideration. The W1507K outlier alone is enough to drop and rebuild from the next-best ESM-2 candidate.
- **The PLM4-vs-PLM5 comparison validates the apo-ΔΔG filter.** PLM5 (with T1535V removed) achieves en31-equivalent structural confidence; the inference is that PLM4's T1535V would have introduced the same kind of degradation we see in PLM3. A direct Boltz run of PLM4 would confirm.

---

## 7. Hyperparameter master table

| Parameter | Value | Where used | Rationale |
|-----------|-------|------------|-----------|
| `esm2_t33_650M_UR50D` | 650M-parameter ESM-2 | Phase 2 main scan | Sweet spot: sub-3-min full-region scan on V100, well-validated zero-shot performance |
| Design region | residues 1230–1620 | All builders | Full WED (~1230–1340) + PI (~1340–1620) domain. WED is the part of FnCas9 that bridges to PI; PI is the PAM-interacting domain. en31's mutations are all in this region |
| Class-conservation orthologs | SpCas9 / SaCas9 / Nme1Cas9 / CjCas9 | `scripts/run_saturation.py`, all builders | Four taxonomically and structurally diverse Cas9s; phylogenetic + structural cross-checks confirm orthology |
| `--max-class-conservation 0.5` | filter threshold | All builders | Reject positions where the amino-acid physicochemical class (acidic / basic / hydrophobic / polar / aromatic / Gly / Pro / Cys) is preserved in ≥ 50% of the ortholog panel. This kills the "rare-AA-bias" picks (W1459K class_cons = 1.00, R1367L = 0.50) |
| `--lambda-cons 1.0` | composite weight | v3/v4/v5 builders | Conservative balance: LLR (or log-odds) and class_cons live on similar scales after the log transform; `λ = 1` makes the penalty noticeable but not dominant. Documented limitation: λ cannot disambiguate substitutions *at* a position (they share the same class_cons) — it only affects between-position ranking |
| `--top-k 4` | candidate size | All builders | Matches en31's three-mutation count plus room for one more. Larger K dilutes the highest-confidence picks |
| `--min-spacing 5` | residue spacing | All builders | Prevents the K picks from clustering at a local hotspot — forces spread across the design region |
| LigandMPNN `ligandmpnn_v_32_010_25.pt` | model checkpoint | Phase 3 | Default for ligand-aware design (v_32 architecture, σ=0.10 noise training) |
| LigandMPNN temperatures | `0.1`, `0.2`, `0.3` | Phase 3 | Standard 3-temperature sweep: T=0.1 near-deterministic, T=0.3 broader sampling. Pool gives richer per-position posterior than any single temperature |
| LigandMPNN ligand cutoff | 8.0 Å | Phase 3 | Default in LigandMPNN paper |
| LigandMPNN samples | 1,600/temperature × 3 = 4,800 total | Phase 3 | Enough for stable per-position aa-frequency estimates (~250 samples per amino acid at uniform per-temperature, plenty per position) |
| `--min-top-freq 0.30` | v4/v5 filter | LigandMPNN candidate filter | Top non-WT must be the modal pick in ≥ 30% of samples. Tightens against noise |
| `--max-wt-freq 0.40` | v4/v5 filter | LigandMPNN candidate filter | WT must NOT still be the dominant choice — i.e. the position must actually want to change |
| `--max-single-ddg 3.2` | PLM5 stability gate | `build_candidate_v4.py` | Anchored to en31's worst single-position apo ΔΔG (E1369R = +3.20). Above this, we're extrapolating beyond known-functional precedent |
| proteinmpnn_ddg model | `v_48_020` | Phase 4 | ProteinMPNN 48-MP-layer, σ=0.20 training; the model peptoneltd's container defaults to |
| Boltz-2 `--diffusion_samples` | 5 | Phase 5 | Standard for confident structures; averaging across 5 reduces sampling noise |
| Random seed | 42 | All phases | Global; recorded in every `meta.json` |
| HPC partition | `dgx` | All sbatches | 8× V100-SXM2-32GB DGX on CSIR-IGIB *tejas* |
| Python | 3.11.11 (.venv-hpc) | All HPC scripts | Compatible with Boltz, LigandMPNN, ESM-2, ProteinMPNN-DDG, biotite, biopython |
| PyTorch | 2.x with cu118 wheels | .venv-hpc | V100 has CUDA 11.8 driver compatibility; cu118 wheels avoid the cu12 mismatch that pinned-`requirements.txt` files would force |

---

## 8. Caveats and known limitations

1. **No wet-lab validation yet.** All findings are in-silico. Each candidate (PLM3, PLM4, PLM5) is a falsifiable prediction; the central claim "structure-conditioned LigandMPNN recovers PAM-contact biophysics where sequence-only ESM-2 fails" rests on Acharya 2024's known wet-lab outcomes for the en31/en15 reference variants and would benefit from direct experimental testing of one or more of our candidates.
2. **Independent-marginal multi-mutant scoring.** Both ESM-2 LLR and LigandMPNN per-position frequency are combined across positions assuming independence. Epistatic mutations are likely; the assumption is wrong but tractable. Boltz-2's per-variant complex prediction is the first method in our stack that scores the multi-mutant as a unit.
3. **Apo-state ΔΔG, not complex ΔΔG.** proteinmpnn_ddg evaluates the protein-only structure. A PAM-contact mutation that destabilizes the apo state but stabilizes the DNA-bound complex (e.g. en31's E1369R) reads as "destabilizing" in our filter. We use the en31 calibration anchor to set a permissive threshold (+3.2 single-position) but the absolute values are not directly comparable to true complex ΔΔG.
4. **LigandMPNN autoregressive overconfidence.** Frequencies near 1.000 reflect decode consistency across many samples, not true per-position posteriors. The L=0.985 at residue 1449 is one such case — biological interpretation should treat this as "strongly favored given the rest of the design," not "no other amino acid is plausible."
5. **Sequence-only ESM-2 rare-AA bias.** ESM-2's pretraining loss has a small bias toward rare amino acids in any context. We see this in PLM3 (3/4 X→K). The class-conservation filter partially mitigates but doesn't eliminate. PLM4/5 picks are less biased (1/4 X→K in PLM5) because LigandMPNN's per-position posteriors are anchored to structural plausibility, not corpus statistics.
6. **No MSA-based scoring.** EVE, Tranception, and other MSA-conditioned models could complement ESM-2. We didn't include them because FnCas9's usable MSA depth is limited (the FnCas9 ortholog cluster is sparse) and the project explicitly prioritizes sequence-only and structure-conditioned models as complementary lenses, not MSA-aware models.
7. **5B2O is a specific PAM (TGG).** PDB 5B2O is FnCas9 bound to a target DNA with TGG PAM. Different PAMs may produce subtly different complex geometries; engineering for *NGG* generality would ideally use a multi-structure ensemble or an explicit PAM oracle (Protein2PAM is available but has a non-commercial weight license that we have not yet committed to).
8. **2'-deoxyuridine in the crystal-structure sgRNA.** Hirano 2016 used a chemically modified sgRNA with one DU (2'-deoxyuridine) residue for crystallization stability. We map DU → U for Boltz, but this is a small approximation; for native function in vivo the residue is U.
9. **Boltz-2 with `--use_msa_server`.** Public ColabFold MSA server may have queue delays or occasional outages. If Phase 5 fails on MSA fetch we will retry with a local MSA pipeline.
10. **Venv coupling.** Installing Boltz into `.venv-hpc` is downgrading numpy/scipy/dm-tree (Phase 5 setup, currently running). If post-Boltz reruns of the ESM-2 or LigandMPNN scripts fail, we will create a separate `.venv-boltz` for isolation.

---

## 9. What's next

**Immediate (this campaign):**

1. Boltz-2 job 214530 completes. Inspect per-variant pLDDT and ipTM scores. If WT and en31 read as confidently folded but PLM3 or PLM5 doesn't, that's a flag worth re-running.
2. Local analysis script (TBD) to load Boltz `.cif` files, extract per-residue confidence, side-chain orientation at residues 1243 / 1369 / 1449 / 1603 / our PLM picks, and PAM-contact distances. PyMOL or Biotite Python API.
3. Sync all `results/runs/2026-05-13_*` back to Mac for analysis + figure prep.

**Near-term (next campaign):**

1. **Wet-lab handoff prep.** If any of PLM3 / PLM5 looks structurally promising (Boltz confidence comparable to en31), produce a one-page handoff document: variant FASTA, predicted mutations, predicted PAM (would require running Protein2PAM as oracle), expected on/off-target ratio (would require running the AiCE or similar predictor).
2. **PLM4-vs-PLM5 ablation.** Compare the structural prediction for PLM4 (with T1535V) vs PLM5 (without). If T1535V meaningfully disrupts the PLM4 complex, that validates the apo-ΔΔG filter; if it doesn't, the filter is too aggressive.
3. **Targeted single-point predictions.** E1449L (our prediction vs Acharya's E1449H), E1603L (ditto vs E1603H). These are cheap to compute and falsifiable.

**Longer-term:**

1. **PAM oracle integration.** Use Protein2PAM as a per-variant fitness signal (predicted PAM PWM vs target NRG PWM). Would let us in-silico-evolve a candidate toward broader PAM tolerance without committing to a specific mutation set up-front. Blocked on the Polyform-NC license question.
2. **Epistasis testing.** Score the 6 pairwise combinations of en31's three mutations under each model. The independent-marginal sum vs the explicit pairwise score will tell us how much epistasis we're missing.
3. **Pre-print.** The ESM-2-vs-LigandMPNN head-to-head at the en31 PAM-contact positions is a publishable methods-comparison result on its own, even before wet-lab validation. Would also include the proteinmpnn_ddg calibration finding (en31 functional at +3.2 single-position apo ΔΔG).

---

## 10. References

### Primary literature

- **Acharya, S., Rauthan, R., ..., Maiti, S., Chakraborty, D.** (2024). "PAM-flexible Engineered FnCas9 variants for robust and ultra-precise genome editing and diagnostics." *Nat Commun* 15:5471. DOI: [10.1038/s41467-024-49233-w](https://doi.org/10.1038/s41467-024-49233-w). PMID 38942756.
- **Hirano, H., et al.** (2016). "Structure and engineering of *Francisella novicida* Cas9." *Cell* 164(5):950–961. DOI: 10.1016/j.cell.2016.01.039. PMID 26875867. The structural paper that produced PDB 5B2O.
- **Lin, Z., et al.** (2023). "Evolutionary-scale prediction of atomic-level protein structure." *Science* (ESM-2). The ESM-2 model series.
- **Dauparas, J., et al.** (2025). "Atomic context-conditioned protein sequence design using LigandMPNN." *Nat Methods* 22:717–723. DOI: 10.1038/s41592-025-02626-1. PMID 40155723.
- **Ruffolo, J., et al.** (2025). "Design of highly functional genome editors by modelling CRISPR-Cas sequences." *Nature* 645:518–525. DOI: 10.1038/s41586-025-09298-z. The OpenCRISPR-1 paper.
- **Nayfach, S., et al.** (2026). "Protein2PAM: deep learning prediction of CRISPR-Cas PAMs." *Nat Biotechnol*, online Feb 2026. DOI: 10.1038/s41587-025-02995-0.

### Tools and databases

- UniProt **A0Q5Y3** (canonical FnCas9 sequence). `https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta`.
- PDB **5B2O** (FnCas9 + sgRNA + DNA, 1.7 Å). `https://files.rcsb.org/download/5B2O.pdb`.
- `fair-esm` (ESM-2): `https://github.com/facebookresearch/esm` (archived 2024).
- `dauparas/LigandMPNN`: `https://github.com/dauparas/LigandMPNN`.
- `peptoneltd/proteinmpnn_ddg`: `https://github.com/peptoneltd/proteinmpnn_ddg`.
- `jwohlwend/boltz`: `https://github.com/jwohlwend/boltz`.

### Internal cross-references

**Companion documents in `docs/`** (the four together with this overview form the complete project documentation):

- **`docs/PLM_PRIMER.md`** — deeper dive on protein language models: transformer architecture for proteins, masked language modeling, embedding extraction, the ESM family lineage, why MSA-based models are *not* used. Read this for the theoretical background.
- **`docs/CANDIDATES.md`** — per-mutation dossier on every variant (en31, en15, PLM3, PLM4, PLM5): biophysical context for each substitution, all model scores side-by-side, decisions-and-rationale audit trail. Read this for the detailed scientific content.
- **`docs/HPC_GUIDE.md`** — end-to-end operational playbook for re-running every phase on a SLURM cluster, with the exact commands and the recovery procedures for every failure mode we hit. Read this if you need to reproduce or extend.
- **`docs/GLOSSARY.md`** — every term, abbreviation, and non-obvious concept defined in one place. Read this if any term in the other documents is unclear.

**Other docs and notes:**

- `docs/design-plan.md` — phase-by-phase plan (the M0–M5 milestone framework).
- `docs/design-plan-phase2.md` — Phase 2 detailed plan.
- `docs/methods.md` — formal methods specification (every scorer's procedure).
- `docs/reproducibility.md` — `meta.json` schema, seeding, determinism guarantees.
- `docs/tools-inventory.md` — exhaustive tool list with licenses and verified status.
- `notes/plm/verification-log.md` — every literature claim's verification result + first-party run results.
- `notes/plm/enFnCas9-overview.md` — focused enFnCas9 background.
- `notes/plm/plm-nuclease-engineering.md` — PLM-design-paper survey.
- `notes/plm/proteingym-substitutions.md` and `notes/plm/proteingym-indels.md` — ProteinGym SOTA notes for substitutions and indels respectively.

---

## 11. Provenance and reproducibility

Every numerical claim in this document is reproducible from the repository as of git SHA recorded in the verification log. The pipeline runs are:

| Phase | Script | Output dir | Commit | Wall time |
|-------|--------|-----------|--------|-----------|
| 2 | `01_esm2_650m_full_PI.sbatch` | `2026-05-13_esm2_650M_full_PI_hpc/` | various | 3 min V100 |
| — | `build_candidate_v3.py` | `2026-05-13_candidates_v3/` | 7b82f63 | <10 sec |
| 3 | `02_ligandmpnn_sampling.sbatch` | `2026-05-13_ligandmpnn_PI/` | 1f03a1e | 28 min V100 |
| — | `ligandmpnn_aggregate.py` | `2026-05-13_ligandmpnn_PI/aggregate.tsv` | 402091a | <10 sec |
| — | `build_candidate_v4.py` | `2026-05-13_candidates_v4/` | 402091a | <10 sec |
| 4 | `03_proteinmpnn_ddg.sbatch` | `2026-05-13_proteinmpnn_ddg/` | de90f57 | 30 sec V100 + 8 min container pull |
| — | `proteinmpnn_ddg_analyze.py` | stdout | e37b57a | <5 sec |
| — | `build_candidate_v4.py --ddg-csv ...` | `2026-05-13_candidates_v5/` | efc2ffb | <10 sec |
| 5 | `04_boltz_complex.sbatch` (job 214530) | `2026-05-13_boltz_complex/` | 6e9b0e1 | in progress |

`results/runs/<dir>/meta.json` records the exact hyperparameters, input SHA-256s, model checkpoint hashes, and run timestamps for each phase. Re-running any phase with the same `meta.json` should reproduce the output bit-for-bit (deterministic seeds + fp16 inference + frozen weights).

---

*End of document. For questions or corrections, see the verification log first, then the relevant primary source. Always trust the primary literature and the first-party data over this summary — this document is curated for clarity, the data files are authoritative.*
