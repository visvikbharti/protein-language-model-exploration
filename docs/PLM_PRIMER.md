# Protein Language Models — A Deeper Primer

**Purpose:** the project-overview document gives a 3-paragraph primer; this document explains how protein language models work, why they work, what they cannot do, and how the specific design choices in our pipeline follow from those properties. Written so a reader with biology background but no ML background can follow it end-to-end.

**Companion to:** `docs/PROJECT_OVERVIEW.md`.

---

## 1. The intuition: why predicting masked amino acids learns biology

Imagine a protein sequence of length *L* amino acids — for FnCas9, *L* = 1,629. Now imagine taking that sequence, randomly masking out ~15% of the residues (replacing them with a special `<mask>` token), and training a neural network on a single task: *given the unmasked residues, predict what the masked ones should be*. This is called **masked language modeling** (MLM), borrowed directly from natural-language models like BERT.

Three things happen during this training, all without supervision from any functional or structural label:

1. **The model learns local structure.** When it sees `…X X X G L X X X…` and there's a strong evolutionary tendency for that GL pair to be in a β-strand, the model learns to predict residues compatible with β-strand chemistry at nearby positions. It has never seen a structure, but the sequence-level co-occurrence patterns of structural elements are very strong.

2. **The model learns biophysical co-variation.** Two residues 50 positions apart along the sequence may be 5 Å apart in 3D — a stable contact. If they co-evolve (i.e. when one mutates, the other often mutates compensatorily), the model picks up on this. This is the same signal that direct-coupling-analysis methods exploit, but expressed inside neural-network weights rather than as a pairwise score matrix.

3. **The model learns evolutionary constraint.** Conserved catalytic residues, signal peptides, signal sequences, salt-bridge networks — anything where natural sequences are constrained — gets baked into the model's prior. Mutating a catalytic residue to something natural sequences never tolerate produces a high cross-entropy loss during training; the model learns to predict the catalytic residue with high confidence whenever the surrounding context is "this looks like an active site."

By the end of training (typically months on hundreds of GPUs, over tens of billions of tokens of protein sequence from UniRef), the model is a compact, parameterized summary of evolutionary patterns in proteins.

---

## 2. The transformer for proteins

ESM-2 (Lin et al., *Science* 2023) is a *transformer encoder*. The architecture has three pieces:

### 2.1 Token embedding

Each amino acid becomes a vector. ESM-2 650M uses 1,280-dimensional vectors. There's also a `<mask>` token, a `<bos>` (beginning-of-sequence) token, and a `<pad>` token. The mapping from one-letter amino acid → 1,280-d vector is *learned* during training (the embedding matrix has shape `33 × 1280`, where 33 = 20 standard amino acids + non-standard codes + special tokens).

After embedding, the input sequence is a *L × 1,280* matrix: every position has its own vector.

### 2.2 Self-attention layers

The core of the transformer. Each layer takes the *L × 1,280* matrix and produces another *L × 1,280* matrix where every position's vector is updated based on *every other* position's vector. The update is weighted: position *i* "attends" more to position *j* if the model has learned they are biologically related.

ESM-2 650M has 33 transformer layers, each with 20 attention heads. By layer 33, a single position's 1,280-d vector has been refined by 33 × 20 = 660 different attention mixings of the entire sequence. The result is a *contextual embedding*: the vector at position 1369 in FnCas9 depends on what's at positions 1, 12, 800, 1622, and everywhere else.

This is the key difference between PLM embeddings and older "feature" methods like BLOSUM-based encodings. BLOSUM gives every Glu the same vector; ESM-2 gives "Glu at position 1369 in FnCas9 specifically" its own vector.

### 2.3 Language-modeling head

A small classifier on top of the final embeddings that maps each position's 1,280-d vector → probability over 20 amino acids. During training, the model is rewarded for putting probability mass on the *original* amino acid at every masked position.

The output of this head is `softmax(linear(embedding))` → a categorical distribution over the 20 amino acids at each position. We use this distribution directly for zero-shot mutation effect prediction.

---

## 3. From a trained model to a zero-shot mutation predictor

We never fine-tune ESM-2 in this project. Instead, we ask the *pretrained* model: "How surprised are you by this mutation?"

**Procedure for one mutation V = WTposMUT:**

1. Start with the WT FnCas9 sequence, length 1,629.
2. Replace the amino acid at `pos` (0-indexed: `pos-1`) with the `<mask>` token. The rest of the sequence is unchanged.
3. Run the masked sequence through ESM-2. Read the output distribution at the mask position. Call it *P*.
4. The model assigns some probability to every amino acid at this position: P("A"), P("R"), ..., P("Y"). These sum to 1.
5. Compute the log-likelihood ratio:
   ```
   LLR(V) = log P(MUT) − log P(WT)
   ```
   (Both probabilities are evaluated under *P*, the same distribution; we just read two of the 20 entries.)

**Interpretation:**

- `LLR > 0`: model gives the mutant higher probability than WT under masked-position prediction. The model thinks "given the rest of the protein, the masked position would more likely have been MUT than WT in a natural protein." Loosely: the mutation looks evolutionarily reasonable.
- `LLR < 0`: model gives WT higher probability. The mutation looks evolutionarily unlikely.
- `LLR ≈ 0`: model is indifferent.

**Why this is useful:** in the ProteinGym benchmark (Notin et al., *Nat Methods* 2023), the LLR for ESM-2 650M correlates with measured deep-mutational-scanning fitness with Spearman *ρ* ≈ 0.45 averaged over ~80 protein families. That's far above random; not as good as the best supervised method on each protein (which can hit ρ ≈ 0.65), but available *without any wet-lab labels*. For engineering tasks where wet-lab labels are expensive or unavailable, that zero-shot signal is the whole game.

---

## 4. What ESM-2 cannot do — the blind spots

This is the most important section for understanding our project's design choices.

### 4.1 No structure input

ESM-2 has no input channel for 3D structure. It cannot read a PDB. It only sees a sequence.

It *implicitly* learns about structure because evolutionary patterns are constrained by structure (residues that pack into a hydrophobic core stay hydrophobic; residues in active sites stay catalytically active). But this learning is approximate and indirect.

**Implication:** for proteins where the structural context is well-represented in the training data (e.g. typical globular enzymes), ESM-2's LLR correlates well with structural fitness. For proteins where the structural context is *unusual* — like a Cas9 making sequence-specific contacts with a DNA backbone — ESM-2 may miss the specific structural constraint that defines function.

### 4.2 No ligand input

ESM-2 has no input channel for ligands, nucleic acids, ions, or small molecules. The model has never seen "this residue contacts an RNA phosphate" or "this Lys makes an electrostatic interaction with a DNA backbone."

What ESM-2 *can* learn indirectly: in proteins from the same family (e.g. type-II Cas9s), residues that contact a ligand will tend to be conserved across orthologs. The model's per-position distribution at those residues will be sharper. But it can't reason: "if I mutate this residue to a positive charge, it will contact the negatively-charged phosphate at 4 Å distance." That requires explicit structural reasoning.

**Our project's central finding** is exactly this blind spot in action: at the PAM-contact position E1369 in FnCas9, ESM-2 ranks the known-functional E1369R mutation at 4,956 / 7,429 (Q3, below median) while LigandMPNN — which sees the DNA — ranks the same E→basic biophysical change as the strongly preferred move (K=0.522, R=0.365 pooled frequencies).

### 4.3 Rare-amino-acid bias

ESM-2's training corpus (UniRef) has unequal amino acid frequencies: L is common, W is rare. The model's pretraining loss is calibrated against these base rates. As a side-effect, when computing the per-position distribution, the model assigns slightly inflated probabilities to under-represented amino acids in *any* context.

**Operational consequence:** if you score every possible single-substitution at a position, the high-LLR picks will be biased toward rare amino acids (W → F, V → K, etc.) even when those substitutions are biophysically unreasonable. This is well-documented in the PLM-engineering literature.

**Our mitigations:**

1. **Class-conservation filter.** Group amino acids into 8 physicochemical classes (acidic / basic / hydrophobic / polar / aromatic / Gly / Pro / Cys). If a position is conserved at the class level across an ortholog panel (FnCas9 vs SpCas9/SaCas9/Nme1Cas9/CjCas9), reject mutations to a different class. This drops e.g. W1459 → K (class_cons = 1.00 — all four orthologs are W or close).
2. **Composite score.** `LLR − λ · class_cons` with λ = 1.0. Penalize mutations that break class conservation even if the LLR is high.
3. **Cross-model validation.** LigandMPNN's frequencies at the same positions are anchored to structural plausibility, not corpus statistics. PLM4/5 use LigandMPNN, which has a different bias profile (1/4 X→K vs PLM3's 3/4). The agreement vs disagreement between models is informative.

### 4.4 Independent-marginal multi-mutant scoring

For a multi-mutant (k mutations at k distinct positions), we score by *summing* the per-position LLRs. This assumes the positions don't interact — an *independence assumption*.

In reality, mutations *do* interact (epistasis). Two mutations that are each beneficial alone may be detrimental together (negative epistasis) or even more beneficial than expected (positive epistasis).

**Why we accept this:** scoring all 2-mutant combinations is O(L²) cost, all 3-mutant is O(L³), etc. — quickly infeasible. The independent-marginal approximation is the standard tradeoff in PLM-engineering pipelines (used in OpenCRISPR-1, Protein2PAM, AiCE, etc.). The error is small when mutations are well-separated in 3D (we enforce `--min-spacing 5` residues to help).

**Our handoff to a non-independent method:** Boltz-2 predicts the full multi-mutant complex as a single object. The pLDDT / ipTM scores from Boltz incorporate epistasis automatically because the structure is predicted as a unified system.

---

## 5. Embeddings as a feature representation

The same ESM-2 model can be used in a second mode: *embedding extraction*. Instead of using the language-modeling head, you read the contextual embeddings out of an intermediate layer (typically the final layer or a layer near the top of the stack).

For a 1,629-aa FnCas9 sequence, you get a 1,629 × 1,280 matrix — every residue has its own 1,280-d feature vector. This matrix is a *learned representation* of the sequence, with three useful properties:

1. **Geometric closeness reflects similarity.** Two embeddings that are cosine-close came from positions that ESM-2 "thinks" are similar — usually because they're at homologous positions in related proteins, or because they play the same structural role.
2. **Embeddings are useful inputs for downstream supervised models.** A classifier trained on top of ESM-2 embeddings (e.g. to predict cleavage efficiency, off-target rate, expression level) needs far less labeled data than a classifier trained from scratch. This is the transfer-learning use of PLMs.
3. **Embeddings disentangle factors.** Different linear projections of the embedding space capture different properties (secondary structure, solvent exposure, contact prediction). The same 1,280-d vector encodes many useful signals.

**In our project:** we do not yet use embeddings as a downstream feature for a supervised model. We use the LM head's per-position distributions (Section 3) directly. Embedding-based fine-tuning is a possible future extension if we get wet-lab labels (e.g. measured cleavage rates for a small variant library, used to train a regressor on top of ESM-2 embeddings).

---

## 6. The ESM family — a brief lineage

| Model | Year | Params | Architecture | Notes |
|-------|------|--------|--------------|-------|
| ESM-1b | 2020 | 650M | encoder | First widely-used PLM. Used in PASTA, EGNN-DDG. |
| ESM-1v | 2021 | 650M × 5 ensemble | encoder | Variant-effect-prediction-focused. Trained on 5 different seeds for ensembling. |
| ESM-IF1 | 2022 | 142M | encoder + GVP backbone reader | *Inverse folding* — input is backbone coords, output is sequence likelihood. Uses GVP (geometric vector perceptron) layers to read 3D structure. ~1,024-aa context window historically. |
| **ESM-2** | 2023 | 8M / 35M / 150M / 650M / 3B / 15B | encoder | Improved training data + recipe. **Used in this project at 650M.** |
| ESM-3 | 2024 | 1.4B / 7B / 98B | encoder + extra tokenizers | Multi-track (sequence + structure + function tokens). Closed-weights at the largest scale. |
| ESM Cambrian | 2025 | — | — | Latest from EvolutionaryScale (the for-profit spinoff). |

**Why ESM-2 650M specifically:**

1. **Open weights.** Available, frozen, reproducible. Re-running the same scan in 2030 will give the same numbers.
2. **Validated.** Hundreds of papers since 2023 use this exact model for zero-shot variant scoring. Performance is well-characterized.
3. **Compute sweet spot.** Full saturation scan over a 391-position region takes ~3 minutes on a single V100. The 3B model would take ~10 minutes; the 15B model would not fit on a 32 GB V100 without sharding.
4. **No major performance gap with 3B on ProteinGym.** The 3B model is slightly better (+0.02 to +0.05 Spearman) but the gap shrinks for protein families with limited usable MSA (Cas9 is exactly this case).

---

## 7. Why MSA-based models (EVE, Tranception) are *not* used here

A major class of variant predictors uses multiple sequence alignments (MSAs) — explicit homolog alignments — rather than a single-sequence model. EVE (Frazer et al., *Nature* 2021) and Tranception (Notin et al., *ICML* 2022) are two notable examples. On many ProteinGym families they outperform ESM-2 because the explicit MSA encodes evolutionary information more directly.

**Why we skip them for Cas9 engineering:**

1. **FnCas9 has a sparse MSA.** Available Cas9 orthologs are dominated by SpCas9-like clades; FnCas9 has only a handful of close homologs at >50% sequence identity. MSA-based models work best when the MSA depth is hundreds or thousands of sequences — Cas9 doesn't meet that bar.
2. **MSA construction is sensitive.** Different MSA tools (JackHMMER, HHblits, MMseqs2) produce different MSAs from the same query. Reproducibility depends on pinning the MSA construction pipeline, which adds operational complexity.
3. **ProteinGym performance:** for sparsely-aligned protein families, ESM-2's single-sequence performance is within ~0.05 Spearman of MSA-based models. Not worth the operational complexity for our use case.
4. **The OpenCRISPR-1 line of work** (which is the closest published analog to our project) uses a single-sequence transformer (a custom CRISPR-LM) and explicitly does *not* rely on MSAs. They reason that the protein family is too sparse for MSAs to add value, and we agree.

---

## 8. Summary of design choices and their reasoning

| Choice | Reason |
|--------|--------|
| ESM-2 over ESM-1b/1v/IF1/3 | ESM-2 is open, frozen, validated, and a published standard for zero-shot variant scoring as of 2026 |
| 650M parameters over 3B/15B | Sweet spot of validation, compute, and reproducibility; minimal performance gap on sparse-MSA families |
| Mask-marginal LLR (single residue masked) | Simplest scoring; well-documented; reproducible |
| Independent-marginal multi-mutant scoring | Tractable; standard in the literature; epistasis caught downstream by Boltz-2 |
| No fine-tuning | Zero-shot scoring is the use case; fine-tuning would require labels we don't have |
| Class-conservation filter (λ = 1.0) | Mitigates rare-AA bias; uses 8-class biophysical grouping, anchored to a 4-Cas9-ortholog panel |
| LigandMPNN as the complementary lens | Sees the DNA; explicitly addresses ESM-2's ligand blind spot |
| proteinmpnn_ddg with en31-anchored threshold | Soft stability filter; threshold (+3.2 single-position) calibrated against a known-functional reference variant |
| Boltz-2 for full-complex final pass | Combines all signals (sequence, structure, ligand, multi-mutant) into a single prediction |

Each choice is reproducibility-friendly: pinned model versions, fixed seeds, documented thresholds.

---

## 9. Common questions

**Q: If ESM-2 misses PAM-contact engineering, why use it at all?**

A: Three reasons. (1) Sequence-only signal is fast and broad — 7,429-variant scan in 3 minutes lets us survey the entire WED+PI region in one shot. (2) Some mutations *are* recoverable from sequence alone — G1243T (en31's WED mutation) is rank 1 / 7,429. The model isn't useless, just biased. (3) Comparing ESM-2 to LigandMPNN at the same positions is itself a scientific finding (the head-to-head head-table in `verification-log.md`).

**Q: Why not just use LigandMPNN for everything?**

A: LigandMPNN requires a PDB structure with ligand atoms. Not every Cas9 we might want to design has a high-quality structure. ESM-2 works on sequence alone, which is universal. They are complementary tools, not substitutes. Also, LigandMPNN's autoregressive overconfidence is itself a limitation (Section 4.4 of `PROJECT_OVERVIEW.md`).

**Q: Where does Boltz-2 fit in?**

A: As the final, most expensive arbiter. Boltz-2 takes a candidate full-mutant + sgRNA + DNA, predicts the complex structure, and reports per-residue confidence (pLDDT) and per-interface confidence (ipTM). If WT, PLM5, and en31 all predict at high confidence but PLM3 predicts poorly, that's strong evidence PLM3's mutations break the complex geometry — a signal neither ESM-2 nor LigandMPNN can produce.

**Q: How would I extend this with my own model?**

A: Two routes. (a) Embedding-based: extract ESM-2 final-layer embeddings for a variant library, train a small regressor (linear or shallow MLP) on top to predict your phenotype of interest, given a labelled subset. (b) Fine-tuning: take ESM-2's pretrained weights, continue training on a labelled dataset (low-rank adapters / LoRA are common for the small-data regime). Both require labelled data that we don't currently have.

---

## 10. Further reading

- Lin et al. (2023). *Evolutionary-scale prediction of atomic-level protein structure*. Science (ESM-2 paper).
- Notin et al. (2023). *ProteinGym: large-scale benchmarks for protein fitness prediction and design*. Nat Methods.
- Dauparas et al. (2023). *Robust deep learning–based protein sequence design using ProteinMPNN*. Science. (ProteinMPNN; LigandMPNN is the ligand-aware extension.)
- Frazer et al. (2021). *Disease variant prediction with deep generative models of evolutionary data*. Nature (EVE).
- Watson et al. (2023). *De novo design of protein structure and function with RFdiffusion*. Nature.

For practical use, the ESM GitHub repo's README and the ProteinGym benchmark site (`https://proteingym.org`) are the most current resources.
