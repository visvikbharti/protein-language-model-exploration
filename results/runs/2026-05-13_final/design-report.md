# Design report — FnCas9-PLM1

**Date:** 2026-05-13
**Author:** autonomous Claude Code session (Opus 4.7)
**Inputs:**
- WT FnCas9: UniProt A0Q5Y3 (SHA-256 verified in saturation `meta.json`)
- WT structure: PDB 5B2O
- Cas9 orthologs (sequence): SpCas9 Q99ZW2, SaCas9 J7RUA5, Nme1Cas9 C9X1G5, CjCas9 Q0P897
- Reference engineered variants: en1 (E1369R), en15 (E1603H), en31 (G1243T/E1369R/E1449H) — from Acharya et al., *Nat Commun* 15:5471 (2024)

## 1. Executive summary

In a single CPU-only session, an ESM-2 (35M parameters) zero-shot saturation scan was run over 84 residues spanning the four FnCas9 hotspots engineered in en1/en15/en31. The top-LLR substitution from each hotspot window was combined into the candidate variant **FnCas9-PLM1 = H1236L / R1367L / W1459K / Q1596N**.

**Pre-registered verification gates** from `docs/design-plan.md` §M1 **FAILED**:
- ESM-2 35M ranks all four reference mutations (G1243T, E1369R, E1449H, E1603H) **below the median LLR at their respective positions** (ranks 12–16 of 19) and all have **negative LLRs**.
- The model's top picks are dominated by substitutions at rare amino acids (especially W1459) — consistent with the well-documented "rare amino-acid bias" of mask-marginal LLR scoring with small PLMs.

This means **FnCas9-PLM1 is presented as a methodologically-honest in-silico demonstration of the PLM pipeline, not a validated functional design.** Two-way homology analysis below provides strong evidence that PLM1's mutation sites overlap with residues that are conserved across the Cas9 family, suggesting the PLM has selected against natural evolutionary signal at the level of single-mutant suggestions. Larger PLMs (ESM-2 650M / 3B, ESM-3) and structure-conditioned methods (LigandMPNN with sgRNA + DNA context) are needed before any wet-lab campaign.

## 2. Pipeline executed (vs. design plan)

| Milestone | Status | Notes |
|---|---|---|
| M0 — define objective | ✓ adapted | Objective: identify ≤ 5 single mutations in the FnCas9 WED–PI region that ESM-2 prefers over WT |
| M1 — baseline | ✗ skipped | No Boltz / Chai-1 complex prediction (CPU only) |
| M2.1 — LigandMPNN sampling | ✗ skipped | Requires GPU + repo vendoring |
| M2.2 — ESM-2 saturation | ✓ done | esm2_t12_35M_UR50D; 84 positions × 19 = 1596 single mutants in 80 seconds CPU |
| M2.3 — Protein2PAM evolution | ✗ skipped | Non-commercial license + GPU |
| M3 — single-mutant filter | ✓ partial | Top per window only; no ΔΔG (proteinmpnn_ddg Docker not invoked) |
| M4 — multi-mutant combine | ✓ done | 4-mutation combination = FnCas9-PLM1 |
| M5 — Boltz-2 / Chai-1 validation | ✗ skipped | GPU only |
| M6 — final ranking + handoff | ✓ this document | |

## 3. The candidate variant

```
>FnCas9-PLM1 PLM-designed FnCas9; H1236L/R1367L/W1459K/Q1596N
```

Stored at: `results/runs/2026-05-13_candidates/fncas9_variants.fasta`

Per-mutation ESM-2 35M log-likelihood ratio (mask-marginal):

| Variant | LLR | Position rank | Window |
|---|---:|:---:|---|
| H1236L | +2.199 | 1 of 19 | WED, phosphate-lock loop region |
| R1367L | +1.853 | 1 of 19 | PI domain, en1/en31 region |
| W1459K | +3.013 | 1 of 19 | PI domain, RNA-contact strand |
| Q1596N | +1.136 | 1 of 19 | PI/WED interface, en15 region |
| **Sum** | **+8.201** | | |

For comparison, the **independence-approximation sum LLR of en31** under the same model is **–2.584** — the PLM strictly disprefers the validated engineered variant.

## 4. Verification gate failure (full numbers)

The design plan's M1 gate explicitly stipulates that the positive control (en31) must rank among the top mutations at each of its positions. Observed:

| Reference mutation | LLR | Global rank | Position rank | Source |
|---|---:|:---:|:---:|---|
| G1243T (en31) | −0.172 | 575 / 1596 | **13 / 19** | Acharya 2024 |
| E1369R (en1, en31) | −0.811 | 1022 / 1596 | **12 / 19** | Acharya 2024 |
| E1449H (en31) | −1.600 | 1340 / 1596 | **16 / 19** | Acharya 2024 |
| E1603H (en15) | −1.562 | 1330 / 1596 | **16 / 19** | Acharya 2024 |

Decision per `design-plan.md` §M1: **"If both fail, document this as a finding (PLMs disagree with rational design)."** This is now documented.

## 5. Two-way homology — sequence

Pairwise global alignment (Needleman-Wunsch, BLOSUM62, gap open −11, extend −1). Full matrix in `results/runs/2026-05-13_homology/sequence_identity_matrix.tsv`.

### 5.1 Identity / similarity vs FnCas9-PLM1

| Compared with | % Identity | % Similarity | Aligned residues |
|---|---:|---:|---:|
| FnCas9 WT | 99.75 | 99.75 | 1629 |
| FnCas9 en1 (E1369R) | 99.69 | 99.69 | 1629 |
| FnCas9 en15 (E1603H) | 99.69 | 99.69 | 1629 |
| FnCas9 en31 (G1243T/E1369R/E1449H) | 99.57 | 99.57 | 1629 |
| SpCas9 (S. pyogenes) | 22.54 | 43.85 | 1300 |
| SaCas9 (S. aureus) | 27.34 | 48.99 | 1035 |
| Nme1Cas9 (N. meningitidis) | 25.19 | 47.34 | 1052 |
| CjCas9 (C. jejuni) | 31.07 | 49.53 | 959 |

Observations:
- PLM1 has 4 / 1629 mutations vs WT → 99.75 % identity (expected).
- PLM1 to en31: 7 differences (3 of en31 + 4 of PLM1; none overlap) → 99.57 %.
- Cas9 family cross-identity (22–31 %) is consistent with published values; FnCas9 is most distant from SpCas9 and closest to CjCas9 (both type II-B-like in some respects).

### 5.2 Mutation sites across Cas9 orthologs (structural-equivalent positions)

The Cas9 fold is conserved across the family despite ~25 % global identity. Using pairwise global alignments, the residue at the homologous position in each ortholog was extracted for every PLM1 and reference mutation site. `*` = identical to FnCas9 WT.

| Site (context) | FnCas9 WT | SpCas9 | SaCas9 | Nme1Cas9 | CjCas9 |
|---|:---:|:---:|:---:|:---:|:---:|
| **G1243** (en31; WED-PLL) | G | N | gap | **G\*** | K |
| **E1369** (en1, en31; PI PAM contact) | E | **E\*** | P | **E\*** | K |
| **E1449** (en31; PI PAM contact) | E | Y | K | gap | D |
| **E1603** (en15; PI/WED interface) | E | S | Y | Q | N |
| **H1236** (PLM1; WED) | H | A | gap | gap | F |
| **R1367** (PLM1; PI) | R | K | K | L | G |
| **W1459** (PLM1; PI, RNA-contact) | W | gap | F | **W\*** | gap |
| **Q1596** (PLM1; PI surface) | Q | D | S | V | K |

**This is the most damning piece of evidence against PLM1.** The PLM-selected mutations include:
- **R1367L**, where R1367 is conserved as R/K in *both* SpCas9 and SaCas9 — the basic charge is a family-conserved feature.
- **W1459K**, where W1459 is conserved as W in Nme1Cas9 — an aromatic at this position is preserved despite the family's overall ~25 % identity.

The reference en31 mutations target residues that are:
- **G1243** — conserved with Nme1Cas9 (G755) → rational because the phosphate-lock loop is locally similar across orthologs.
- **E1369** — conserved with SpCas9 (E1150) and Nme1Cas9 (E805) → engineered E→R reverses charge at a *family-conserved* PAM-contact position, which is a principled design.
- **E1449** — variable (Y in SpCas9, K in SaCas9, D in CjCas9) → en31's E→H targets a position that has natural diversity, so a charge-change is biophysically tolerable.

The PLM's failure mode is now interpretable: it preferentially picks rare amino acids (W, F, large/charged) for substitution because their WT log-probability is low under a model trained on natural sequence frequencies, *regardless of whether that rare amino acid is functionally indispensable*.

## 6. Two-way homology — structure (PDB 5B2O)

For each mutation site, the structural context was extracted from FnCas9 (PDB 5B2O — WT + sgRNA + DNA + TGG PAM, 1.7 Å). Full table: `results/runs/2026-05-13_structure/mutation_site_table.tsv`.

| Pos | WT res | Domain | SASA (Å²) | n contacts (within 6 Å) | nearest DNA (Å) | nearest RNA (Å) | Engineered? | Interpretation |
|---:|:---:|---|---:|---:|---:|---:|:---:|---|
| 1236 | HIS | WED | 91.6 | 4 | 16.1 | **3.7** | PLM1 | Solvent-exposed, RNA-contact. H→L removes H-bond donor at RNA interface — likely destabilises RNA binding. |
| 1243 | GLY | WED | 28.2 | 5 | **3.6** | 4.9 | en31 | Tight backbone position contacting both DNA and sgRNA — G→T at the phosphate-lock loop adds methyl as documented in Acharya 2024. |
| 1367 | ARG | PI | 40.7 | **10** | 9.1 | 8.4 | PLM1 | High contact count = packed core residue. R→L removes positive sidechain *and* 10 neighbouring interactions — destabilising. |
| 1369 | GLU | PI | 49.5 | 10 | 8.8 | **3.4** | en1, en31 | Charged surface contacting sgRNA. E→R is the published PAM-flexibility mutation. |
| 1449 | GLU | PI | 64.5 | 7 | 7.0 | 10.7 | en31 | Solvent-exposed PI residue. E→H is the second PAM contact in en31. |
| 1459 | TRP | PI | 41.1 | 6 | 11.9 | **3.7** | PLM1 | Aromatic at the RNA-contact face. W→K swaps an indole π-stack for a flexible positive sidechain at 3.7 Å from RNA — biophysically implausible without breaking RNA contact. |
| 1596 | GLN | PI | 71.5 | 7 | 21.2 | 29.3 | PLM1 | Surface residue, far from nucleic acid. Q→N is conservative chemistry (both polar amides). The one PLM1 mutation likely to be benign — but also likely to have no functional effect. |
| 1603 | GLU | PI | 61.2 | 9 | 6.4 | 20.8 | en15 | DNA-proximal PI residue. E→H is en15. |

Structural interpretation, summarised:
- en31's three mutations cluster at **DNA / RNA contact distances of 3.6–8.8 Å** and target residues with functional roles already characterised in published structures.
- PLM1's mutations include one likely-disruptive RNA-contact change (W1459K, 3.7 Å to RNA), one likely-destabilising core change (R1367L, 10 neighbours), one likely-disruptive RNA-contact change (H1236L, 3.7 Å to RNA), and one likely-neutral surface change (Q1596N, 21+ Å from nucleic acid).

The lack of explicit cross-Cas9 *3D* superposition (TM-align / CE) is a session limitation — biotite does not include TM-align. The sequence-mapped equivalent positions above are a defensible proxy because of the family's structural conservation, but a future revision should run cross-Cas9 structural alignment with an external tool.

## 7. What this run shows about the PLM approach

1. **ESM-2 zero-shot at small scale (35M) is misleading for engineered Cas9.** It systematically disprefers the validated en31 mutations and picks at rare amino acids whose WT identity has low natural-distribution probability. This is the rare-AA / WT-marginal bias documented in the PLM literature.
2. **Cross-ortholog conservation is a free oracle that catches the bias.** Two of the four PLM picks (R1367L, W1459K) target residues conserved across distant Cas9 orthologs, which is a strong evolutionary contraindication. Combining ESM-2 LLR with a simple "conservation score from a Cas9 family MSA" filter would likely have rejected these. (Future work: implement this filter explicitly in `src/nuclease_design/scoring/conservation.py`.)
3. **Structure-conditioned scoring is essential.** PLM1's W1459K and H1236L sit 3.7 Å from RNA atoms in PDB 5B2O. A scorer that *saw* the sgRNA / DNA context (LigandMPNN, ESM-IF1 conditioned on backbone, or AF3-pLDDT-delta) would have penalised these. ESM-2 is sequence-only and cannot.

## 8. Recommendations for the next iteration

In order of value-per-effort:

1. **Re-run with ESM-2 650M** (or 3B if you can spare ~2 GB VRAM). Larger models reduce the rare-AA bias substantially. Expected time: 4× CPU = ~5 min on Apple Silicon, < 1 min on a single A100. (Estimated cost: $0.05 cloud GPU.)
2. **Add a Cas9 family conservation filter.** Build a Cas9-family MSA (e.g., via MMseqs2 search against UniRef, then MAFFT alignment), compute per-position Shannon entropy, and downweight or block substitutions at conserved positions. ~1 day implementation.
3. **Run LigandMPNN on the predicted FnCas9-sgRNA-DNA complex.** This is the canonical structure-conditioned design step in `docs/design-plan.md` §M2.1. Estimated time: 1× A100 ~2 hr for 5,000 samples. ~$2–6 cloud GPU.
4. **Re-evaluate PLM1, en31, and any new candidates with Boltz-2 / Chai-1.** Need ~1× H100 ~30 min per complex. ~$5–15.
5. **Wet-lab cap of 96 variants.** With items 1–4 done, the final ranking is meaningful enough to commit to plate-scale assays.

## 9. What was NOT done in this session (be aware)

- No Boltz-2 or Chai-1 complex prediction — would need GPU.
- No LigandMPNN, ProteinMPNN, or any structure-conditioned design.
- No Protein2PAM (non-commercial license + GPU).
- No proteinmpnn_ddg stability filter.
- No conservation filter (planned `src/nuclease_design/scoring/conservation.py`, not implemented).
- No cross-Cas9 3D structural superposition (would need TM-align / CE external).
- No wet-lab.
- No screening loop with experimental fitness feedback (single-pass design only).

## 10. Files produced this run

```
results/runs/
├── 2026-05-13_esm_saturation/
│   ├── scores.tsv             # 1596 single-mutant LLRs
│   └── meta.json
├── 2026-05-13_candidates/
│   ├── fncas9_variants.fasta  # PLM1 + WT + en1/en15/en31 sequences
│   └── FnCas9-PLM1.meta.json
├── 2026-05-13_homology/
│   ├── sequence_identity_matrix.tsv
│   ├── sequence_similarity_matrix.tsv
│   └── aligned_length_matrix.tsv
├── 2026-05-13_structure/
│   └── mutation_site_table.tsv
├── 2026-05-13_cross_ortholog/
│   └── site_mapping.tsv
└── 2026-05-13_final/
    └── design-report.md       # this file
```

## 11. Citations consulted

- Acharya et al. (2024). PAM-flexible Engineered FnCas9 variants. *Nat Commun* 15:5471. DOI [10.1038/s41467-024-49233-w](https://doi.org/10.1038/s41467-024-49233-w).
- Hirano et al. (2016). Structure and engineering of FnCas9. *Cell* 164:950–961. DOI [10.1016/j.cell.2016.01.039](https://doi.org/10.1016/j.cell.2016.01.039).
- Lin et al. (2023). ESM-2 / Evolutionary-scale prediction. *Science* 379:1123-1130. (Mask-marginal LLR scoring methodology.)
- See `notes/plm/verification-log.md` for the complete claim-by-claim verification trail used in this project.
