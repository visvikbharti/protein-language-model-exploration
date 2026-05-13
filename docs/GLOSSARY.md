# Glossary

Every project-specific term, abbreviation, or non-obvious scientific concept used in this repository's documentation, in alphabetical order. Cross-references in *italics*.

---

**A0Q5Y3.** UniProt accession for the canonical FnCas9 protein sequence (1,629 aa). Source: `https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta`.

**Acharya 2024.** Reference to Acharya, Rauthan, et al. (2024), "PAM-flexible Engineered FnCas9 variants for robust and ultra-precise genome editing and diagnostics," *Nat Commun* 15:5471. The paper that produced en1, en15, en31. Source of all wet-lab calibration anchors in this project. DOI: 10.1038/s41467-024-49233-w.

**AiCE.** "AI-guided Cas9 engineering" — a 2025 paper (Gao lab, *Cell*) describing PLM-guided base-editor engineering. Cited in our PLM-engineering survey.

**Apo state.** A protein structure in the *absence* of its ligand/substrate. Compare to the *holo* state (with ligand bound). `proteinmpnn_ddg` predicts apo-state ΔΔG; Boltz-2 predicts holo (complex) structure.

**Autoregressive sampling.** A generation strategy where each output token is drawn conditioned on the tokens already generated. LigandMPNN samples sequences autoregressively. Implication: *per-position frequencies* across many independent samples reflect decode consistency rather than true per-position posteriors.

**β-branched amino acid.** Amino acid where the Cβ has two heavy-atom substituents (V, I, T). Sterically constrained side-chain orientations. Relevant to the T1535V substitution (both T and V are β-branched, so the swap is locally isosteric at Cβ).

**BLOSUM62.** A 20×20 amino-acid substitution score matrix derived from blocks of conserved protein sequences. Used in our Needleman-Wunsch sequence alignment.

**Boltz-2.** Open-source AlphaFold-3-class structure prediction model for protein + nucleic-acid + small-molecule complexes. Used in Phase 5 of our pipeline. GitHub: `jwohlwend/boltz`. Wohlwend et al., 2024-2025.

**Cas9.** A DNA-cleaving RNA-guided endonuclease from CRISPR-Cas systems. Multiple species variants: SpCas9 (most common), SaCas9, FnCas9, Nme1Cas9, CjCas9, etc. Used in genome editing.

**Chai-1.** Alternative open-weight structure prediction model (similar to Boltz-2 in scope). Apache-2.0 licensed. Listed in `tools-inventory.md` as a possible Boltz-2 cross-check.

**Class conservation.** Per-position conservation metric used by this project. Amino acids are grouped into 8 physicochemical classes (acidic / basic / hydrophobic / polar / aromatic / Gly / Pro / Cys). For each position, the fraction of ortholog residues at that position falling into the same class as FnCas9's residue is the class conservation. Higher = more conserved at the class level. Implemented in `src/nuclease_design/scoring/conservation.py`.

**ClabFold.** Open-source local replacement for AlphaFold's MSA server. Boltz-2 (when set to `--use_msa_server`) calls the public ColabFold endpoint.

**Composite score.** Our scoring formula combining model output and conservation penalty. For PLM3: `LLR − λ · class_conservation`. For PLM4/5: `log(top_freq / wt_freq) − λ · class_conservation`. Default `λ = 1.0`.

**Compute capability 7.0.** NVIDIA GPU architecture generation (Volta). The V100 has compute capability 7.0; no native bfloat16, supports fp16. Relevant to Boltz-2 precision selection.

**CUDA 11.8.** NVIDIA CUDA toolkit version. V100 driver on tejas is CUDA 12.2 forward-compatible but cu118 PyTorch wheels are stable for our use. cu12 wheels (which LigandMPNN's requirements.txt pins) cause runtime errors on our setup.

**Decode consistency.** Property of autoregressive sampling where multiple independent samples produce similar outputs because each is internally consistent with respect to its own decoding context, not because the underlying posterior is sharp. Discussed in *autoregressive sampling*.

**DGX.** NVIDIA DGX-1 server with 8× V100-SXM2-32GB GPUs. The compute platform we use on tejas.

**Distroless container.** A minimal Docker/Singularity image containing only the application binary and its direct runtime dependencies, with no shell, no `cat`, no `ls`. Common for production deployments to reduce attack surface. `peptoneltd/proteinmpnn_ddg` is distroless.

**Diffusion sampling (Boltz).** Boltz-2 uses a diffusion model for structure prediction; each "sample" is one full denoising trajectory producing one candidate structure. We use 5 diffusion samples per variant.

**Directed evolution.** Wet-lab method for evolving proteins toward a desired function via repeated rounds of random mutagenesis + selection. Acharya 2024 used directed evolution to produce en1/en15/en31.

**DMS (deep mutational scanning).** Wet-lab method for measuring fitness of every possible point mutation in a protein. ProteinGym benchmarks zero-shot PLM scores against DMS data.

**ΔΔG (Delta-Delta-G).** Change in folding free energy (`G_mut − G_WT`) caused by a mutation. Positive = destabilizing, negative = stabilizing. Units kcal/mol. Predicted by `proteinmpnn_ddg`.

**DNA target chain.** In a Cas9 complex, the DNA double helix containing the protospacer (the sequence matching the guide RNA) and the *PAM*. In PDB 5B2O, chains C (30 nt) and D (9 nt, PAM-containing).

**DU.** 2'-deoxyuridine — a non-canonical nucleotide used in chemically-synthesized RNA for stability. Present at one position in 5B2O's sgRNA. Mapped to U for Boltz prediction.

**en1, en15, en31.** Engineered FnCas9 variants from Acharya 2024. en1 = E1369R single. en15 = E1603H single. en31 = G1243T / E1369R / E1449H triple. All show >2× cleavage rate and other improvements vs WT.

**Embedding.** A learned vector representation of an input. In ESM-2 650M, each amino acid in a sequence is represented by a 1,280-d vector at every transformer layer. Final-layer embeddings are useful inputs for downstream supervised models.

**Epistasis.** Non-additive interactions between mutations — when the effect of mutation A depends on whether mutation B is present. Our independent-marginal scoring assumes no epistasis. Boltz-2 implicitly handles epistasis because it scores the full multi-mutant complex.

**ESM-2.** Lin et al. (2023, *Science*) — a family of transformer-based protein language models from Meta AI. Sizes 8M / 35M / 150M / 650M / 3B / 15B parameters. We use the 650M model. GitHub: `facebookresearch/esm`.

**ESM-IF1.** Hsu et al. (2022) — an inverse-folding model that takes a backbone structure and predicts sequence likelihoods. Listed in `methods.md` but not used in current runs.

**Falsifiable prediction.** A claim made by our in-silico analysis that can be unambiguously tested in the lab. E.g. "E1449L should give similar or better cleavage activity than en31's E1449H."

**fair-esm.** The Python package providing ESM-2 model weights and inference code. Repo archived 2024-02-07 (Meta moved to a closed model line at EvolutionaryScale).

**FELUDA.** *F*nCas9 *E*ditor *L*inked *U*niform *D*etection *A*ssay — a CSIR-IGIB diagnostic platform using FnCas9 for nucleic-acid detection (Azhar et al. 2021, Kumar et al. 2021).

**FnCas9.** Cas9 from *Francisella novicida*. 1,629 aa. UniProt A0Q5Y3. Higher specificity than SpCas9; used for diagnostic + therapeutic applications.

**Fp16, fp32.** Floating-point precision: half-precision (16-bit, faster on V100) vs full single-precision (32-bit, more numerically stable). We use fp16 for forward passes, fp32 for final softmax + LLR computation.

**Holo state.** A protein structure with its ligand/substrate bound. Compare to *apo*. Boltz-2 predicts holo.

**Hotspot window.** A 21-residue range chosen from the en31 mutation positions, used in earlier hotspot-based runs (Phase 2). Replaced by the full WED+PI design region in PLM3+.

**Hirano 2016.** Reference to Hirano, Endo, et al. (2016), "Structure and engineering of *Francisella novicida* Cas9," *Cell* 164:950-961. Source of PDB 5B2O. Reported FnCas9-RHA = E1369R/E1449H/R1556A.

**HPC (High-Performance Computing).** The CSIR-IGIB *tejas* cluster, where we run all GPU jobs.

**Identity conservation.** Per-position conservation metric: the fraction of ortholog residues at that position that are *exactly* the same amino acid as FnCas9's. Compare to *class conservation*. Implemented but not used in candidate filters (too coarse).

**iPTM (interface predicted TM-score).** A confidence metric output by Boltz-2 for the predicted geometry between two chains. Higher = more confident in the interface. We compare iPTM for the protein-DNA interface across WT/PLM3/PLM5/en31.

**Inverse folding.** Predicting a sequence given a backbone structure. ESM-IF1 and LigandMPNN are inverse folding models. Compare to *forward folding* (sequence → structure, e.g. AlphaFold).

**K_d (dissociation constant).** Wet-lab measurement of binding affinity (concentration at which half the protein is ligand-bound). Lower = stronger binding. Acharya 2024 reports en15 K_d = 49 nM vs WT 170 nM.

**LigandMPNN.** Dauparas et al. (2025, *Nat Methods*) — a structure-conditioned protein-design model that takes backbone coords + ligand atoms as input. Extension of ProteinMPNN to ligand contexts. Used in Phase 3. GitHub: `dauparas/LigandMPNN`.

**LLR (Log-Likelihood Ratio).** Per-mutation score from a PLM: `log P(MUT|context) − log P(WT|context)`. Computed by ESM-2 mask-marginal procedure. Natural log (nats). Positive = mutation preferred over WT.

**Lustre.** The shared parallel filesystem on tejas. Our working directory `/lustre/vishal.bharti/protein-language-model-exploration/` lives here, accessible from both login and compute nodes.

**Mask-marginal LLR.** The specific zero-shot scoring procedure we use with ESM-2. Replace one residue with `<mask>`, predict its identity distribution, compute LLR. See `docs/PLM_PRIMER.md` Section 3.

**Masked language modeling (MLM).** The training task for ESM-2: predict 15% of randomly masked amino acids given the rest of the sequence.

**Min spacing.** Filter parameter: minimum residue separation between picks in a multi-mutant candidate. Default 5. Prevents clustering at one local hotspot.

**MSA (Multiple Sequence Alignment).** A collection of homologous sequences aligned column-by-column. EVE and Tranception use explicit MSAs. ESM-2 does not.

**Multi-mutant.** A protein variant with more than one mutation. All our candidates are multi-mutants (k=4 typically).

**Naive Bayes.** Statistical model assuming independence of features. Our independent-marginal multi-mutant scoring is essentially a Naive Bayes-style approximation.

**Needleman-Wunsch.** Classical dynamic-programming algorithm for global sequence alignment. Used in our ortholog alignment with BLOSUM62 substitution matrix.

**NGG, NRG, NAG, NGA.** Cas9 PAM sequences (N = any nucleotide). FnCas9 WT recognizes NGG; en31 broadens to NGG/NGA/NAG.

**NJ (Neighbor-Joining).** Phylogenetic tree-building algorithm. Used in our sequence-based ortholog phylogeny.

**Off-target.** Cleavage at an unintended DNA site (sites resembling the target but not identical). Enzyme specificity is measured as the on/off-target ratio.

**OpenCRISPR-1.** Ruffolo et al. (2025, *Nature*) — first major published PLM-designed Cas9 variant. ~55% on-target / 0.32% off-target, vs SpCas9's 48% / 6%. Provides a benchmark for PLM-based Cas9 engineering at scale.

**Ortholog.** A protein from a different species but the same evolutionary origin (often the same function). Our four orthologs: SpCas9, SaCas9, Nme1Cas9, CjCas9.

**P (probability).** In our LLR computation, `P(MUT|context)` and `P(WT|context)` are values from ESM-2's softmax output at a masked position.

**PAM (Protospacer Adjacent Motif).** Short DNA sequence (typically 3 nt) immediately adjacent to the Cas9 protospacer. Cas9 requires this sequence for binding/cleavage. Different Cas9s recognize different PAMs.

**PDB 5B2O.** The Protein Data Bank entry for FnCas9 + sgRNA + DNA in the TGG-PAM state, 1.7 Å resolution. Hirano 2016. Our canonical structure.

**pLDDT (predicted Local Distance Difference Test).** A per-residue confidence metric output by AlphaFold/Boltz. Range 0-100. Higher = model is more confident in the local structure. Threshold conventions: >90 high confidence, 70-90 medium, <70 low.

**PI domain.** PAM-Interacting domain of FnCas9, residues ~1,340-1,620. The domain that reads the PAM nucleotides. Most en31 mutations are in this region.

**PLM (Protein Language Model).** Transformer trained on protein sequences via masked-language-modeling. ESM-2 is the prototypical example.

**PLM3, PLM4, PLM5.** Our three computed candidates. PLM3 = ESM-2-only. PLM4 = LigandMPNN. PLM5 = LigandMPNN + apo-ΔΔG filter.

**Polyform-NC license.** Non-commercial-use-only software license. Protein2PAM's weights are released under Polyform-NC, which constrains how we can use it.

**Protein2PAM.** Nayfach et al. (2026, *Nat Biotechnol*) — a PLM that predicts a Cas9's PAM PWM from its sequence. A *PAM oracle* — could be used as a fitness signal for PAM-relaxation engineering.

**ProteinGym.** A standardized benchmark suite for protein fitness prediction. Hundreds of DMS datasets used to evaluate zero-shot scorers (including PLMs). `https://proteingym.org`.

**ProteinMPNN.** Dauparas et al. (2023, *Science*) — a deep learning model for inverse folding (sequence design given backbone). LigandMPNN extends it with ligand context.

**proteinmpnn_ddg.** Peptone Ltd's tool for computing per-position saturation ΔΔG predictions from a PDB. Uses ProteinMPNN as the backbone. Container: `ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base`. Used in Phase 4.

**PWM (Position Weight Matrix).** A 4×N matrix giving the per-position nucleotide preference for a binding site. Used to summarize PAM specificity.

**Q1/Q2/Q3/Q4.** Statistical quartiles. "Q3" in our composite-rank discussion means the third quartile (positions 50%-75% of the ranked list — worse than median, better than the worst quartile).

**Rare-AA bias.** Tendency of ESM-2 to assign inflated probabilities to under-represented amino acids (W, C, M) in zero-shot scoring. A known limitation. Discussed in `PLM_PRIMER.md` Section 4.3.

**REC lobe (Recognition lobe).** The N-terminal portion of Cas9 that engages the sgRNA + target DNA duplex. Residues ~1-1,200 of FnCas9.

**RFdiffusion / RFdiffusion-AA.** Watson et al. (2023, *Nature*) / Krishna et al. (2024, *Science*) — diffusion-model protein design tools. Listed in `tools-inventory.md`; not used in current runs.

**RMSD (Root-Mean-Square Deviation).** A measure of structural similarity between two aligned structures. Lower = more similar. Used in our structural phylogeny.

**Saturation mutagenesis.** Computing/measuring every possible single-position substitution. ESM-2 scan, proteinmpnn_ddg, and DMS experiments are all saturation studies.

**Seq_rec (sequence recovery).** LigandMPNN's per-sample metric: fraction of designed positions where the sampled amino acid matches the input PDB. NaN if no positions were designed.

**SgRNA (single-guide RNA).** Engineered fusion of CRISPR tracrRNA + crRNA into a single RNA. In 5B2O, chain B (93 nt + 1 DU).

**Singularity.** Container runtime for HPC environments (replacement for Docker, which requires root). We use Singularity 3.7.4 on tejas.

**SLURM.** Job scheduler used on tejas (and most academic HPC clusters). Commands: `sbatch` (submit), `squeue` (check queue), `sacct` (history), `scancel` (cancel).

**Spearman correlation (ρ).** Rank-correlation coefficient. Used as the standard metric for PLM zero-shot performance on ProteinGym.

**Spm-Cas9, SpCas9.** *Streptococcus pyogenes* Cas9. The most common Cas9 in genome editing. Recognizes NGG PAM.

**Stability.** Thermodynamic stability of the folded protein (relative to unfolded). Measured by ΔΔG. Higher stability = more negative ΔΔG.

**Tejas.** Name of the CSIR-IGIB HPC cluster. `https://tejas.igib.res.in` (internal).

**TM-align / TM-score.** Pairwise structure alignment method/scoring. Higher TM-score = better structural similarity. Our iterative outlier-trimming procedure mimics TM-align's logic.

**Top_freq.** In LigandMPNN aggregation: pooled fraction of samples where the modal amino acid at a position is the chosen pick. Higher = more confident.

**top-K.** Selection rule: keep the top K candidates by composite score, subject to distinctness and spacing constraints.

**UniProt.** International protein database. Each protein has a unique accession (e.g. A0Q5Y3 for FnCas9). FASTAs available via REST: `https://rest.uniprot.org/uniprotkb/<ACCESSION>.fasta`.

**UniRef.** Clustered UniProt sequences, used to train ESM-2 etc. UniRef50/UniRef90 = 50%/90% sequence identity cluster representatives.

**V100.** NVIDIA Tesla V100 GPU. 32 GB HBM2 memory, compute capability 7.0, no native bfloat16. The accelerator on our DGX node.

**WED domain (Wedge domain).** A domain of Cas9 that bridges the REC and PI lobes. FnCas9 residues ~1,230-1,340. Contains G1243T (en31).

**WT (wild type).** The unmodified, canonical, reference sequence. For our project, FnCas9 WT = UniProt A0Q5Y3.

**YAML.** YAML Ain't Markup Language — the configuration file format used for Boltz-2 inputs. Indentation-sensitive; the formatter in `scripts/prepare_boltz_yamls.py` follows the Boltz schema exactly.

**Zero-shot.** Inference without any task-specific fine-tuning or labels. PLMs trained on UniRef do zero-shot variant effect prediction by computing LLRs at masked positions, without ever seeing functional labels.
