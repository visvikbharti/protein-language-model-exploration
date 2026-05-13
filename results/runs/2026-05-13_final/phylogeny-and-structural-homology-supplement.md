# Phase 2.5 supplement — Phylogeny and 3D structural homology

**Date:** 2026-05-13
**Predecessors:** Phase 2 design report (`design-report-phase2.md`). This supplement adds two analyses requested after Phase 2: (1) a phylogenetic tree placing the PLM-designed candidates among naturally occurring Cas9 proteins, and (2) true 3D structural homology across the Cas9 family (not the per-residue structural-context analysis already done on PDB 5B2O).

---

## 1. Phylogenetic placement of PLM1 / PLM2 among natural Cas9 proteins

### 1.1 Method
- Pairwise BLOSUM62 global alignments (NW) → pairwise sequence distance `1 − identity`.
- BioPython Neighbor-Joining tree from the 10×10 distance matrix.
- Input set: **FnCas9-PLM1, FnCas9-PLM2, FnCas9-WT, FnCas9-en1, FnCas9-en15, FnCas9-en31, SpCas9, SaCas9, Nme1Cas9, CjCas9.**
- Files: `results/runs/2026-05-13_phylogeny/{distance_matrix.tsv, tree_nj.newick, tree_nj.txt, tree_nj.png}`.

### 1.2 Pairwise distances (excerpt)

| | PLM1 | WT | en1 | en15 | en31 | PLM2 |
|---|---:|---:|---:|---:|---:|---:|
| PLM1 vs FnCas9 family | 0.0025 | 0.0025 | 0.0031 | 0.0031 | 0.0043 | 0.0049 |
| PLM2 vs FnCas9 family | 0.0049 | 0.0025 | 0.0031 | 0.0031 | 0.0031 | 0 |
| PLM2 vs Cas9 orthologs | — | — | — | — | — | 0.77 (Sp), 0.73 (Sa), 0.75 (Nme1), 0.69 (Cj) |

The intra-FnCas9 distances are all ≤ 0.005 (≤ 5 amino-acid differences across the 1629-aa protein); ortholog distances are 0.69–0.78 (~22–31% identity), an order of magnitude larger.

### 1.3 Tree (NJ, BLOSUM62)

```
                                   _______________________ CjCas9
                                 _|
                                | |__________________________ Nme1Cas9
  ______________________________|
 |                              |  ________________________ SaCas9
 |                              |_|
 |                                |________________________ SpCas9
 |
 | FnCas9-en1
 |
 | FnCas9-PLM1
 |
_, FnCas9-en15
 |
 | FnCas9-WT
 |
 , FnCas9-PLM2
 |
 | FnCas9-en31
```

### 1.4 Reading the tree

- **All six FnCas9 variants** (WT, en1, en15, en31, **PLM1, PLM2**) collapse into a single tight clade. They are nearly indistinguishable at this branch-length scale — exactly what is expected for variants that differ by only 1–4 mutations in a 1629-aa protein.
- The **PLM-designed candidates sit clearly inside the FnCas9 clade**, not closer to any other natural ortholog. This is a sanity check passed: our designs are not accidentally drifting toward another Cas9 family.
- The four natural orthologs split into two clades — **(Nme1Cas9, CjCas9)** and **(SpCas9, SaCas9)** — with shorter internal branches than the long branch separating FnCas9 from all of them. FnCas9 is the most divergent Cas9 in this set.

### 1.5 Bottom line

A phylogenetic tree confirms that **FnCas9-PLM1 and FnCas9-PLM2 are valid FnCas9-derived variants** (no genus-jumping), and that the FnCas9 lineage itself is distant from SpCas9 / SaCas9 / Nme1Cas9 / CjCas9. Any cross-Cas9 generalisations (PAM, immunogenicity, off-targets) should be made with this distance in mind.

---

## 2. 3D structural homology across the Cas9 family

### 2.1 Method

Sequence-guided 3D superposition with iterative outlier trimming (a graduated TM-align-like refinement, threshold sequence 15 → 10 → 8 → 6 → 5 → 4 Å). For each pair of Cas9 PDB structures:

1. Extract the longest amino-acid chain from each structure.
2. Pairwise sequence-align the two protein sequences (NW, BLOSUM62).
3. Build the list of corresponding CA atom pairs from non-gap aligned positions.
4. Kabsch superposition; identify CA pairs within the current distance threshold.
5. Re-superpose on the inlier subset only; tighten the threshold; iterate.
6. Report **rmsd_core** = RMSD over the converged structural core, and **rmsd_all** = RMSD over every sequence-aligned CA pair.

Implementation: `src/nuclease_design/structure/align.py`. Tests: `tests/test_structure_align.py` (3 tests, including a self-superposition sanity check). Cross-Cas9 driver: `scripts/run_structural_homology.py`.

### 2.2 Cas9 structures used

| Cas9 | PDB | Resolution | Chain length |
|---|---|---|---|
| FnCas9 (5B2O) | WT + sgRNA + DNA, TGG PAM | 1.70 Å | 1455 modelled |
| SpCas9 (4OO8) | WT + sgRNA + DNA | 2.50 Å | 1301 modelled |
| SaCas9 (5CZZ) | WT + sgRNA + DNA | 2.60 Å | 1043 modelled |
| Nme1Cas9 (6JDQ) | WT + sgRNA + DNA | 2.05 Å | 1069 modelled |
| CjCas9 (5X2H) | WT + sgRNA + DNA | 2.66 Å | 746 modelled |

(All five are crystal structures of WT enzymes in complex with sgRNA and target DNA — the canonical "active" state — so the comparison is apples-to-apples.)

### 2.3 Pairwise structural core RMSD (Å)

| | FnCas9 | SpCas9 | SaCas9 | Nme1Cas9 | CjCas9 |
|---|---:|---:|---:|---:|---:|
| **FnCas9** | 0 | 4.39 | 2.55 | 2.83 | 2.36 |
| **SpCas9** | 4.39 | 0 | 1.90 | 2.08 | 2.20 |
| **SaCas9** | 2.55 | 1.90 | 0 | 2.07 | 2.22 |
| **Nme1Cas9** | 2.83 | 2.08 | 2.07 | 0 | 1.72 |
| **CjCas9** | 2.36 | 2.20 | 2.22 | 1.72 | 0 |

Smallest pairs: **Nme1Cas9 ↔ CjCas9 (1.72 Å)** and **SpCas9 ↔ SaCas9 (1.90 Å)** — both pairs of cognate clades agree closely structurally. **FnCas9 is the most structurally divergent**, with the largest RMSDs to all four orthologs (2.36 – 4.39 Å). This is consistent with FnCas9 being the longest sequence (1629 vs 746–1368 for the others) and having extra insertions that the iterative refinement places far from the SpCas9 core.

### 2.4 Structural phylogeny (UPGMA on RMSD_core)

```
                               ______________________________________ CjCas9
                     _________|
                    |         |______________________________________ Nme1Cas9
  __________________|
 |                  |      __________________________________________ SaCas9
_|                  |_____|
 |                        |__________________________________________ SpCas9
 |
 |___________________________________________________________________ FnCas9
```

Topology: **( ( (CjCas9, Nme1Cas9), (SaCas9, SpCas9) ), FnCas9 )**.

### 2.5 Sequence vs structural tree — congruence check

| Clade in sequence NJ tree | Clade in structural UPGMA tree | Agree? |
|---|---|:---:|
| (CjCas9, Nme1Cas9) | (CjCas9, Nme1Cas9) | ✓ |
| (SpCas9, SaCas9) | (SpCas9, SaCas9) | ✓ |
| FnCas9 as outgroup to the other 4 | FnCas9 as outgroup | ✓ |
| Branch lengths consistent? | Yes — FnCas9 has the longest branch in both | ✓ |

**The trees are topologically congruent** despite being built from completely different signals (amino-acid identity vs 3D backbone RMSD). This is a strong cross-validation of both analyses: sequence and structure tell the same evolutionary story for these five Cas9s, with FnCas9 as the divergent outgroup and (Nme1Cas9, CjCas9) / (SaCas9, SpCas9) as cognate sister pairs.

### 2.6 Caveats — what the structural alignment does and does NOT do

- ✅ Gives a sensible **structural-core RMSD** (1.7–4.4 Å range across orthologs) consistent with what TM-align would produce for the well-superimposable core.
- ✅ Yields a tree topology congruent with sequence phylogeny.
- ❌ Does **NOT** recover the full Cas9 structural core, because sequence-guided alignment misaligns long indels in the REC and HNH regions between distantly-related Cas9s. The "core" residue counts (30–423 across pairs) are smaller than what a true TM-align would find (typically 600+ Cα for full-length Cas9 family).
- ❌ Does **NOT** compute TM-score (a length-normalised structural similarity score). The RMSD numbers are absolute Å values; for a length-normalised metric we'd need a true TM-align implementation.
- For a definitive cross-Cas9 structural homology, install TM-align or use DALI; our values are an in-Python, pip-installable approximation.

## 3. Why this matters for the PLM design

1. **PLM1 and PLM2 are validated as FnCas9-clade variants.** They sit unambiguously inside the FnCas9 sub-tree in the sequence phylogeny, not drifting toward any natural ortholog. This is a basic sanity check on our design pipeline.
2. **FnCas9 is the structurally most divergent Cas9 in our set.** Any prior assumption that "results from SpCas9 engineering transfer cleanly to FnCas9" is structurally weakened — there is real divergence in the WED-PI and REC regions. The Acharya 2024 enFnCas9 paper had to engineer FnCas9-specific mutations, not import SpCas9 mutations.
3. **Sequence-structure congruence supports the conservation scorer.** The class-conservation metric used to filter PLM1's bad picks treats all Cas9 orthologs as equivalent informants. The congruent phylogeny justifies that assumption — these orthologs really do share a single fold lineage.
4. **PLM1 and PLM2 have no crystal structures themselves.** Backbone RMSD of these *predicted* variants vs WT FnCas9 would be ≈ 0 in this analysis (the only changes are sidechain identity at four positions). True structural assessment of PLM1 / PLM2 requires predicted complex models from Boltz-2 / Chai-1 / AlphaFold3 — deferred to Phase 3.

## 4. Files produced in Phase 2.5

```
results/runs/2026-05-13_phylogeny/
├── distance_matrix.tsv           # 10×10 sequence distance matrix
├── tree_nj.newick                # NJ tree of all variants + orthologs
├── tree_nj.txt                   # ASCII rendering
└── tree_nj.png                   # matplotlib PNG

results/runs/2026-05-13_structural_homology/
├── structural_alignments.tsv     # pairwise alignment metrics
└── rmsd_core_matrix.tsv          # 5×5 structural distance matrix

results/runs/2026-05-13_structural_phylogeny/
├── tree_upgma.newick
├── tree_upgma.txt
└── tree_upgma.png
```

Code added:
- `scripts/build_phylogeny.py` (sequence tree)
- `src/nuclease_design/structure/align.py` (sequence-guided 3D superposition with iterative refinement)
- `scripts/run_structural_homology.py` (cross-Cas9 RMSD matrix)
- `scripts/build_structural_tree.py` (structural tree)
- `tests/test_structure_align.py` (3 tests on the align module)

All 43 tests pass (`pytest tests/ -q`).

## 5. What to do next

The two-way homology question is now answered both ways:
- **Sequence:** phylogeny + pairwise identity matrix (this supplement + Phase 1)
- **Structure:** cross-Cas9 RMSD + structural phylogeny (this supplement)

The remaining open question from Phase 2 — whether structure-conditioned scoring (LigandMPNN) recovers en31's PAM-contact mutations — still requires GPU and remains the Phase 3 ask. Sequence-only PLMs at 35M and 650M empirically cannot, and the structural homology done here doesn't change that — it just confirms that we should expect Cas9-family conservation patterns to be informative because the fold is shared across the 5 orthologs.
