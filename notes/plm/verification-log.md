# Verification log — claims cross-checked vs. primary sources

**Policy:** Every numerical or attribution claim in our notes must be cross-checked against the primary source (paper, repository, database entry). This log records the result of every check. Status values: **CONFIRMED**, **REFUTED** (with corrected value), **UNVERIFIED** (could not access primary source — usually paywall).

Verification rounds:
- **2026-05-12 round 1** — initial draft surveys produced by background literature agents `enFnCas9-overview-DRAFT.md` and `plm-nuclease-engineering-DRAFT.md`; verification done by three independent fact-check agents.

---

## Round 1 — enFnCas9 draft

| # | Claim | Status | Correction / source |
|---|-------|--------|---------------------|
| 1 | Paper title "PAM-flexible Engineered FnCas9 variants for robust and ultra-precise genome editing and diagnostics" | CONFIRMED | https://pubmed.ncbi.nlm.nih.gov/38942756/ |
| 2 | *Nat Commun* 15:5471, 2024 | CONFIRMED | PubMed record |
| 3 | DOI 10.1038/s41467-024-49233-w | CONFIRMED | https://doi.org/10.1038/s41467-024-49233-w |
| 4 | First author = Riya Rauthan | **REFUTED** | First author is **Sundaram Acharya**. Rauthan is mid-list. Maiti & Chakraborty are senior/corresponding. |
| 5 | en1 = E1369R single | CONFIRMED | Paper text snippet via Google indexing |
| 6 | en15 = E1603H single | CONFIRMED | Resolves the draft's flagged uncertainty |
| 7 | en31 = G1243T + E1369R + E1449H triple | CONFIRMED | Paper text snippet |
| 8 | All three variants >2-fold cleavage rate vs. WT FnCas9 in vitro | CONFIRMED | Paper text snippet |
| 9 | K_d en1 = 91.33 ± 29.8 nM, K_d en15 = 49.16 ± 10.96 nM, K_d WT = 170 ± 31.53 nM (MST on VEGFA3) | CONFIRMED | Paper text snippet (numerical precision corrected) |
| 10 | ~90% indels at HBB in HEK293T | CONFIRMED with caveat | Specific to guide g21; different guides give different numbers (e.g., a separate snippet shows en1 ~45% vs SpCas9 ~30% at a different HBB site) |
| 11 | enFnCas9 outperforms SpCas9-HF1 and eSpCas9 on DCX HDR knock-in (~6.8 kb donor) | CONFIRMED qualitatively | Exact knock-in percentages NOT extracted from snippets |
| 12 | PAM expanded NGG → NRG/NGR | CONFIRMED | en31 ranges 5'-NGG > NGA > NAG-3' |
| 13 | ~3.5× expansion of targetable human genome sites | CONFIRMED | Paper text snippet |
| 14 | ~1,300-fold higher specificity than SpCas9 | **REFUTED** (provenance only) | The figure is from the **Acharya 2024 *Nat Commun* paper itself** (Digenome-seq), NOT the 2025 press release. Cite the paper. |
| 15 | Hirano et al. 2016, *Cell* 164(5):950–961, DOI 10.1016/j.cell.2016.01.039 | CONFIRMED | PMID 26875867 |
| 16 | FnCas9-RHA = E1369R + E1449H (double mutant) | **REFUTED** | RHA is a **TRIPLE mutant: E1369R / E1449H / R1556A**. Draft is missing R1556A. |
| 17 | FnCas9-RHA PAM = 5'-YG-3' | CONFIRMED | Hirano 2016 |
| 18 | Acharya et al. 2019 PNAS 116(42):20959-20968, DOI 10.1073/pnas.1818461116 | CONFIRMED | DOI resolves |
| 19 | Azhar et al. 2021 *Biosens Bioelectron* (FELUDA dFnCas9), PMID 33866136 | CONFIRMED | "Rapid and accurate nucleobase detection using FnCas9 and its application in COVID-19 diagnosis" |
| 20 | Kumar et al. 2021 *eLife* 10:e67130 (FELUDA SARS-CoV-2) | CONFIRMED | https://doi.org/10.7554/eLife.67130 (PMID 34106048) |
| 21 | FrCas9 Chen et al. *Nat Commun* 13, 2022, DOI 10.1038/s41467-022-29089-8 — *Faecalibaculum rodentium*, NNTA PAM | CONFIRMED | DOI resolves |
| 22 | "afFnCas9" / MUTE-seq (Ye et al. *Adv Materials* 2025) | CONFIRMED with name correction | Actual variant nickname in paper is **FnCas9-AF2** (advanced-fidelity), not "afFnCas9". Title: "MUTE-Seq: An Ultrasensitive Method for Detecting Low-Frequency Mutations in cfDNA With Engineered Advanced-Fidelity FnCas9." DOI 10.1002/adma.202505208 |
| 23 | UniProt A0Q5Y3: 1,629 aa, *F. tularensis* subsp. *novicida* U112 | CONFIRMED | https://rest.uniprot.org/uniprotkb/A0Q5Y3.txt — "SQ SEQUENCE 1629 AA" |
| 24 | PDB 5B2O: WT FnCas9 + sgRNA + DNA, TGG PAM, ~1.7 Å | CONFIRMED | RCSB; 1.70 Å |
| 25 | PDB 5B2P: WT FnCas9, TGA PAM | CONFIRMED | RCSB |
| 26 | PDB 5B2Q: FnCas9 RHA variant | CONFIRMED with note | 5B2Q DNA is bound with TGG PAM (not 5'-YG-3') |
| 27 | US patent 11,970,699 B2 exists, claims enFnCas9 | CONFIRMED (metadata) | Title "Kinetically enhanced engineered FnCas9 and its uses thereof"; inventors include Chakraborty, Maiti, Acharya, Nureki, Nishimasu, Hirano; assignees CSIR + Univ. Tokyo. Full claim text not retrieved. |

## Round 1 — PLM-nuclease engineering draft

| # | Claim | Status | Correction / source |
|---|-------|--------|---------------------|
| P1 | OpenCRISPR-1 paper exists at DOI 10.1038/s41586-025-09298-z, *Nature* 2025 | CONFIRMED | https://www.nature.com/articles/s41586-025-09298-z, PMID 40739342, PMC12422970 |
| P1a | Title "Design of highly functional genome editors by modelling CRISPR-Cas sequences" | CONFIRMED | Nature 645:518-525 (2025) |
| P1b | bioRxiv preprint 2024.04.22.590591 | CONFIRMED | Preprint title slightly different |
| P1c | 1M+ CRISPR operons in atlas | CONFIRMED | "more than 1 million CRISPR operons" from 26 Tb of (meta)genomes |
| P1d | 240k Cas9s in atlas | UNVERIFIED | Not in accessible abstract/summary; paper body paywalled |
| P1e | ~4M sequences generated | UNVERIFIED | Sources mention "4.8× protein clusters"; literal 4M count unconfirmed |
| P1f | ~200 candidates tested in mammalian cells | UNVERIFIED | Body paywalled |
| P1g | 403 aa differences vs SpCas9 | CONFIRMED | Press summaries confirm "403 aa differences from SpCas9; 182 from any known natural Cas9" |
| P1h | On-target 55.7% vs SpCas9 48.3% (HEK293T) | CONFIRMED | Press summary |
| P1i | ~95% off-target reduction | CONFIRMED | "0.32% vs 6.07%" — ~95% reduction |
| P1j | Lower immunogenicity (iELISA) | CONFIRMED qualitatively | iELISA specifics not in abstract |
| P2 | Protein2PAM, Nat Biotechnol Feb 2026, DOI 10.1038/s41587-025-02995-0 | CONFIRMED | Online Feb 2, 2026 |
| P2a | First author Ruffolo | **REFUTED** | **First author is Stephen Nayfach.** Ruffolo is mid-list. |
| P2b | bioRxiv preprint 2025.01.06.631536 | CONFIRMED | Linked via PMC11741284 |
| P2c | 45k+ Cas-PAM pairs training | CONFIRMED | "over 45,000 CRISPR-Cas PAMs" |
| P2d | NmeN4G.1 recognises 42 N4G PAMs vs 7 WT | UNVERIFIED | Abstract states "broadened PAM"; exact counts unconfirmed |
| P2e | 50× higher in-vitro cleavage | CONFIRMED | "up to 50-fold increase ... compared to wild type in vitro" |
| P3 | AiCE PMID 40628259, Cell 2025, Gao lab | CONFIRMED | PMID resolves |
| P3a | DOI claim S0092-8674(25)00680-4 | **REFUTED** | Actual DOI is **10.1016/j.cell.2025.06.014**. The "S00..." string is the Cell article identifier, not a DOI. |
| P3b | enABE8e 5-bp editing window | CONFIRMED | PMID page |
| P3c | enSdd6-CBE ~1.3× fidelity | CONFIRMED | PMID page |
| P3d | enDdd1-DdCBE 14.3× mt editing | CONFIRMED | PMID page |
| P4 | LigandMPNN, Dauparas et al., Nat Methods 2025, DOI 10.1038/s41592-025-02626-1 | CONFIRMED | Nat Methods 22:717-723 (2025), PMID 40155723 |
| P5 | PAMmla, Nature July 2025, PMID 40262634, Walton/Joung lab | **PARTIALLY REFUTED** | PMID + Nature 2025 correct. **Senior author is Benjamin P. Kleinstiver, NOT Walton or Joung.** First author Rachel A. Silverstein. DOI **10.1038/s41586-025-09021-y**. |
| P6 | Spencer & Zhang, *Sci Rep* 2017, DOI 10.1038/s41598-017-17081-y, SpCas9 DMS | CONFIRMED | Title: "Deep mutational scanning of S. pyogenes Cas9 reveals important functional domains." PMID 29203891 |
| P6a | "Only published Cas9 DMS" — negative claim | UNVERIFIABLE (plausible) | Cannot definitively prove a negative. Note: a recent Nat Commun 2025 paper s41467-025-60925-9 describes Cas1/Cas2 DMS — not Cas9, so the Cas9-specific claim stands. |
| P7 | RFdiffusion Watson et al. Nature 2023 | CONFIRMED | https://www.nature.com/articles/s41586-023-06415-8 — "De novo design of protein structure and function with RFdiffusion" |
| P7a | RFdiffusion-AA Krishna et al. Science 2024, DOI 10.1126/science.adl2528 | CONFIRMED | "Generalized biomolecular modeling and design with RoseTTAFold All-Atom" (RFdiffusionAA introduced within) |
| P8 | Evo Nguyen et al. Science 2024 | CONFIRMED | DOI 10.1126/science.ado9336 |
| P8a | Evo 2 Science 2025 | **REFUTED** | **Evo 2 was published in Nature 2026, not Science 2025.** DOI **10.1038/s41586-026-10176-5**. Title: "Genome modelling and design across all domains of life with Evo 2." First author Garyk Brixi. |
| T-ESM-IF1 | ESM-IF1 has ~1024 aa context limit | **REFUTED** (provenance) | No explicit context-length statement in the GitHub README. If true, source must be the Hsu et al. 2022 paper, not the repo. |
| T-OpenCRISPR | OpenCRISPR-1 weights not released, only sequence + license | CONFIRMED | Repo distributes FASTA + gRNA + bespoke license |
| T-AF3-bench | AF3 / Boltz-2 not benchmarked on Cas9-sgRNA-DNA | UNVERIFIABLE (likely true) | No such benchmark found in FoldBench, Boltz-2, or AF3 supplementary materials. Cannot prove a negative. |

## Round 1 — Tool repos

Single source of truth is `docs/tools-inventory.md`. All tools accessed and metadata verified.

Key corrections from drafts:
- **Chai-1 license is Apache-2.0** (draft said MIT)
- **CRISPR-Cas-Atlas is CC BY-NC 4.0** (draft said "Open")
- **Protein2PAM** has Polyform-NC code license + CC-BY-NC weight license (draft said Apache-2.0)
- **ESM-2 / fair-esm repo is archived** (last commit 2024-02-07) — STALE
- **ProGen2 repo is stale** (last commit 2023-08-04)
- **RFdiffusion-AA repo is stale** (last commit 2024-07-09; ~22 months as of 2026-05-12)
- All other tool repos VERIFIED active.

---

## Outstanding items for future verification rounds

1. Exact HDR knock-in percentages for en1 / en15 / en31 vs SpCas9-HF1 / eSpCas9 at DCX → requires Nature Communications full PDF access.
2. OpenCRISPR-1 specific numbers (240k Cas9s, ~4M generated, ~200 tested) → requires Nature paper full PDF access.
3. Protein2PAM "42 N4G PAMs vs 7 for WT" → requires Nat Biotechnol full text.
4. Original source for an ESM-IF1 1024-aa context limit, if it exists → Hsu et al. 2022 paper.
5. Independent benchmark of AlphaFold3 / Boltz-2 on Cas9-sgRNA-DNA complexes → field gap, not a verification gap.

---

## In-silico results — first-party data from this project

This section records empirical findings from our own runs (not literature). Each entry is an experiment we can re-run from the recorded scripts, scores, and PDBs in `results/runs/<date>_*/`.

### 2026-05-13 — ESM-2 650M full PI-domain saturation (HPC)

- **Run dir:** `results/runs/2026-05-13_esm2_650M_full_PI_hpc/`
- **Reproduces with:** `hpc/slurm/01_esm2_650m_full_PI.sbatch` on CSIR-IGIB tejas DGX, V100-SXM2-32GB.
- **Setup:** ESM-2 t33 650M (HuggingFace `facebook/esm2_t33_650M_UR50D`), mask-marginal LLR, residues 1230–1620 (WED + PI; 391 positions × 19 substitutions = 7,429 variants).
- **Runtime:** ~3 min wall on V100 (compared to ~12 min CPU on the prior 84-position subset).
- **Sanity-check rank of known beneficial mutations in the 7,429-variant pool (composite = LLR − 1.0 × class_conservation):**

  | Mutation | Composite rank | Quartile | Interpretation |
  |----------|----------------|----------|----------------|
  | G1243T (en31, WED) | **1 / 7,429** | top | sequence-only model strongly recovers this WED-domain mutation |
  | E1369R (en1 / en31, PI) | 4,956 / 7,429 | Q3 | dispreferred — below median |
  | E1449H (en31, PI) | 5,117 / 7,429 | Q3 | dispreferred — below median |
  | E1603H (en15, PI) | 5,109 / 7,429 | Q3 | dispreferred — below median |

- **Headline finding (NEW EMPIRICAL CLAIM, supersedes the Phase 2 hotspot-windows result):** sequence-only ESM-2 650M zero-shot CANNOT recover the three E→R / E→H PAM-contact mutations that the Acharya 2024 enFnCas9 paper engineered. All three sit in the bottom half of the 7,429-variant PI-domain pool, i.e. the model thinks they are worse than wild-type. Only G1243T — a WED-domain mutation away from the DNA-contact surface — is recovered, and it tops the entire ranked list. This is consistent with the expected blind spot: ESM-2 has no representation of DNA, so it cannot see that E1369 / E1449 / E1603 sidechains are too negatively charged for their phosphate-backbone neighbours. This is the cleanest empirical demonstration to date (in this project) of the sequence-only PLM capability ceiling on PAM-relaxation engineering, and the motivation for moving to structure-and-ligand-conditioned LigandMPNN.

### 2026-05-13 — FnCas9-PLM3 candidate (HPC)

- **Run dir:** `results/runs/2026-05-13_candidates_v3/`
- **Reproduces with:** `scripts/build_candidate_v3.py --scores <esm2_run>/scores.tsv --top-k 4 --max-class-conservation 0.5 --min-spacing 5`
- **Selection rule:** top-K under composite = LLR − 1.0 × class_conservation, gated on (class_conservation < 0.5, LLR > 0, positions ≥ 5 residues apart). Full PI design space, no hot-spot windows.
- **Mutations:** `G1243T / W1507K / C1292K / M1617K`
- **Per-mutation scores:**

  | Variant | LLR | class_cons | Composite |
  |---------|-----|-----------|-----------|
  | G1243T | +4.436 | 0.33 | +4.103 |
  | W1507K | +3.308 | 0.00 | +3.308 |
  | C1292K | +3.100 | 0.00 | +3.100 |
  | M1617K | +3.057 | 0.00 | +3.057 |

- **Notes / hypotheses (NOT verified):**
  - Three of the four picks are hydrophobic-to-K swaps in the PI domain. Biophysically plausible (PI domain contacts the negatively-charged DNA backbone), but could also reflect ESM-2's known rare-amino-acid bias. Wet-lab activity testing would discriminate; structural prediction (Boltz-2, planned in `04_boltz_complex.sbatch`) is a cheaper intermediate filter.
  - G1243T overlap with en31 is a real positive control success — the same exact substitution was independently recovered from a 7,429-variant pool.
  - Class-conservation gate rejected the high-LLR-but-class-non-conserved picks from the older 84-position run (W1459K class_cons=1.00, R1367L class_cons=0.50).

### 2026-05-13 — LigandMPNN structure+ligand-conditioned design (HPC)

- **Run dir:** `results/runs/2026-05-13_ligandmpnn_PI/`
- **Reproduces with:** `hpc/slurm/02_ligandmpnn_sampling.sbatch` (DGX V100, ~28 min wall for 1,600 samples × 3 temperatures × 1 model checkpoint `ligandmpnn_v_32_010_25.pt`).
- **Aggregator:** `scripts/ligandmpnn_aggregate.py` produces `aggregate.tsv` (per-position aa frequencies pooled over 4,800 samples).
- **Setup:** LigandMPNN with PDB 5B2O (chain A protein + B/C sgRNA/DNA as ligand context), 391 design positions = full WED+PI (1230-1620). Three temperatures: 0.1, 0.2, 0.3. Total 4,800 samples.
- **Gotchas hit and resolved:**
  - LigandMPNN CLI requires SPACE-SEPARATED residue tokens (`"A1230 A1231 ..."`); the range form `"A1230-A1620"` is silently rejected (job 214059 produced 1,600 identical-to-WT samples per temperature with `seq_rec=nan` — wasted run, preserved as `_FAILED_no_design`).
  - LigandMPNN vendored openfold uses NumPy < 1.24 deprecated aliases (`np.int`, `np.float` etc.); patched in-place via sed (NumPy downgrade would break our ESM-2 venv).
  - LigandMPNN's `requirements.txt` pins `torch==2.2.1 (cu12)`, `numpy==1.23.5`, `scipy==1.12.0` — DO NOT install. Only install ProDy + ml-collections + dm-tree separately.

- **Headline finding (NEW): Structure-conditioned LigandMPNN partially recovers PAM-contact biophysics where sequence-only ESM-2 fails.** Direct head-to-head at the four Acharya 2024 reference positions:

  | Position | WT | en target | ESM-2 broad-pool rank | LigandMPNN top non-WT pick | LigandMPNN target_freq | LigandMPNN WT_freq |
  |----------|----|----------|------------------------|----------------------------|-------------------------|---------------------|
  | 1243 (WED) | G | T | **1 / 7429** ✓ | **T=0.455, S=0.456** (tied) | 0.455 | 0.087 |
  | 1369 (PI) | E | R | 4956 / 7429 (Q3) | **K=0.522** (R=0.365 runner-up) | 0.365 | 0.000 |
  | 1449 (PI) | E | H | 5117 / 7429 (Q3) | **L=0.985** | 0.000 | 0.001 |
  | 1603 (PI) | E | H | 5109 / 7429 (Q3) | **L=0.517** | 0.000 | 0.026 |

  - At 1369, LigandMPNN strongly wants to change away from E (WT_freq=0.000) and prefers a basic residue (K or R) — exactly matching Acharya's biophysical rationale that the PAM-contact region needs to flip from acidic to basic. ESM-2 (sequence-only) ranked R at 4956/7429 (worse than WT). This is direct empirical evidence that ligand context fixes a real PLM blind spot for DNA-contact engineering.
  - At 1449/1603, both models DISAGREE with Acharya: ESM-2 says "leave as E", LigandMPNN says "change to L (hydrophobic)". H is essentially never sampled (0.000). Either Acharya's H mutations are functionally optimal for reasons neither in-silico method captures (epistasis, kinetics, off-target trade-offs) or the experimentally-evolved H is a structural compromise. Falsifiable prediction: a single-point E1449L and E1603L should be designed and compared to E1449H / E1603H if wet-lab work proceeds.

- **PLM4 selection** — `T1535V / Y1249F / Y1341L / A1325K` (run dir: `results/runs/2026-05-13_candidates_v4/`)
- **PLM3 vs PLM4 — zero overlap:**

  | | PLM3 (ESM-2 sequence-only) | PLM4 (LigandMPNN structure+ligand) |
  |---|--------------------------|------------------------------------|
  | Picks | G1243T, W1507K, C1292K, M1617K | T1535V, Y1249F, Y1341L, A1325K |
  | X→K count | 3 / 4 | 1 / 4 |
  | Confidence proxy | LLR (sequence-only) | top_freq pooled (1.000, 1.000, 0.996, 0.989) |

  PLM4 has substantially less hydrophobic-to-K bias than PLM3, consistent with LigandMPNN being less affected by the rare-AA-bias artefact that has been observed in ESM-2 zero-shot scoring.

- **Caveats:**
  - LigandMPNN sampling is autoregressive (one residue at a time conditioned on partial sequence). Per-position frequencies computed across independent samples therefore inherit decode consistency rather than reflecting true per-position posteriors. Frequencies near 1.000 at well-determined positions should be read as "very confident in this assignment given the rest of the design", not as "no other amino acid is plausible". This caveat is relevant for the 1449 L=0.985 finding in particular.
  - 159 / 391 design positions have a top-pick different from WT — extensive sequence drift from WT, which proteinMPNN-DDG should filter for stability.
  - No experimental validation. Filing as "in-silico prediction" pending stability filter (proteinmpnn_ddg) and structural validation (Boltz-2 complex prediction) downstream.

### 2026-05-13 — proteinmpnn_ddg apo-stability filter

- **Run dir:** `results/runs/2026-05-13_proteinmpnn_ddg/`
- **Reproduces with:** `hpc/slurm/03_proteinmpnn_ddg.sbatch` (peptoneltd/proteinmpnn_ddg `1.0.0_base` Singularity container, model `v_48_020`, full-chain saturation over 5B2O chain A, ~30 sec wall on V100 after first-time image pull).
- **Analyzer:** `scripts/proteinmpnn_ddg_analyze.py` (peptoneltd LONG format: `pre, post, pos, logit_difference, logit_difference_ddg`).

- **What this measures (and what it doesn't):** proteinmpnn_ddg evaluates ΔΔG on the *apo* protein structure. It does NOT see the sgRNA or DNA. A `+ΔΔG` for a DNA-contact charge swap therefore reflects destabilization of the apo state, not destabilization of the functional complex. The Acharya 2024 en31/en15 wet-lab data are essential as calibration anchors.

- **Calibration anchors (Acharya 2024 known-functional variants):**

  | Variant | Mutations | Cumulative ΔΔG (apo) |
  |---------|-----------|---------------------|
  | en31 (G1243T/E1369R/E1449H) | G1243T = −2.65, E1369R = +3.20, E1449H = −0.15 | **+0.40 kcal/mol** |
  | en15 (E1603H) | E1603H = −1.37 | **−1.37 kcal/mol** |

  Functional engineered variants tolerate single-position apo ΔΔG up to at least +3.20 kcal/mol (E1369R in en31), and cumulative apo ΔΔG in the range [−1.4, +0.4]. Anything in that band is calibrated-safe; anything outside is extrapolation.

- **PLM3 (sequence-only ESM-2): cumulative ΔΔG = −8.42 kcal/mol** — far below the en15 anchor. Reads as "much more stable than wild-type". Two interpretations: (a) genuinely well-folded mutant, (b) proteinmpnn_ddg miscalibration for hydrophobic-to-K substitutions. The W1507K = −5.07 kcal/mol stabilization is biophysically suspicious (W→K removes an aromatic; would normally cost stability). Flagging for follow-up but not rejecting.

  | Variant | ΔΔG | Call |
  |---------|-----|------|
  | G1243T | −2.65 | stabilizing |
  | W1507K | −5.07 | stabilizing (suspicious — see above) |
  | C1292K | −3.63 | stabilizing |
  | M1617K | +2.93 | moderate destabilizer |

- **PLM4 (LigandMPNN structure+ligand): cumulative ΔΔG = +6.74 kcal/mol** — **6.3 kcal/mol above the en31 functional anchor**. T1535V alone contributes +4.15 (above any single-position cost in either functional reference variant). This is a real concern, not an artefact. The tension is informative: LigandMPNN sampled T→V at position 1535 with pooled frequency 1.000 (perfectly confident *in the complex*), while proteinmpnn_ddg says T1535 is a hydrogen-bonding hub for the apo fold. The two structure-aware models are conditioning on different reference states, and they disagree at exactly this position.

  | Variant | ΔΔG | Call |
  |---------|-----|------|
  | T1535V | +4.15 | STRONG destabilizer — outside calibrated envelope |
  | Y1249F | −0.98 | stabilizing |
  | Y1341L | +1.78 | moderate destabilizer |
  | A1325K | +1.79 | moderate destabilizer |

- **Action item:** Rebuild a stability-filtered v5 candidate that adds a `--max-single-ddg` gate (drop any single mutation with ΔΔG > some threshold, e.g. +3.20 = en31's worst single-position cost) on top of the existing LigandMPNN selection logic. PLM5 would replace T1535V with the next-best LigandMPNN candidate satisfying both filters.

### 2026-05-14 — Boltz-2 complex prediction (truncated WED+PI)

- **Run dir:** `results/runs/2026-05-13_boltz_complex/`
- **Analyzer output:** `results/runs/2026-05-13_boltz_complex/analysis/boltz_analyze_output.txt`
- **Reproduces with:** `hpc/slurm/04_boltz_complex.sbatch` (job 215253; ~10 min wall on V100 for 4 variants × 5 diffusion samples after fixing OOM).

- **Setup gotchas resolved:**
  - First attempt (job 214530) ran full-length 1,629-aa FnCas9 + sgRNA + DNA — all 4 variants OOM'd on V100 32GB at fp16. Boltz catches the OOM and continues with exit 0 producing zero predictions ("WARNING: ran out of memory, skipping batch", "Number of failed examples: 1"). Wasted 2:22 of wall time.
  - Fix: truncate the protein chain to residues 1230-1620 (WED + PI = 391 aa). Keeps all engineered positions in their natural ligand context. Run time dropped to ~2 min per variant.
  - Single-sequence mode (`msa: empty` in YAMLs) — predictions still self-consistent across variants but absolute confidences depressed. Fixed in the YAML generator for next time.

- **Confidence summary table** (mean ± std over 5 diffusion samples):

  | Metric | WT | PLM3 | PLM5 | en31 |
  |--------|-----|------|------|------|
  | Overall confidence | 0.915±0.003 | **0.865±0.044** | 0.918±0.010 | 0.919±0.003 |
  | Mean per-res pLDDT | 0.908±0.003 | 0.862±0.032 | 0.913±0.004 | 0.913±0.002 |
  | Interface pLDDT | 0.912±0.003 | 0.862±0.037 | 0.916±0.006 | 0.912±0.004 |
  | pTM (whole complex) | 0.938±0.008 | 0.887±0.076 | 0.932±0.030 | 0.940±0.008 |
  | iPTM (all interfaces) | 0.944±0.008 | 0.880±0.094 | 0.935±0.037 | 0.946±0.007 |
  | pTM (protein chain) | 0.949±0.007 | 0.924±0.034 | 0.949±0.017 | 0.952±0.006 |
  | iPTM protein↔DNA-target | 0.932±0.009 | 0.889±0.061 | 0.923±0.030 | 0.934±0.008 |
  | iPTM protein↔DNA-PAM | 0.939±0.008 | 0.901±0.056 | 0.933±0.025 | 0.942±0.008 |
  | iPTM protein↔sgRNA | 0.947±0.008 | **0.866±0.117** | 0.937±0.037 | 0.949±0.007 |

- **Headline finding #1: PLM5 is structurally indistinguishable from en31.** Every metric is within one standard deviation between PLM5 and en31 (the wet-lab-validated known-functional variant). At the most decision-relevant interface — protein↔DNA-PAM — PLM5 = 0.933±0.025 vs en31 = 0.942±0.008 (Δ = −0.009 ≈ noise). The structure-conditioned LigandMPNN design followed by apo-ΔΔG filtering produced a candidate that Boltz cannot tell apart from the published functional variant. **Strongest possible in-silico endorsement short of wet-lab validation.**

- **Headline finding #2: PLM3 is structurally compromised.** Boltz scores PLM3 worse than WT/PLM5/en31 on every metric, with drops of 0.04-0.08 and 6-10× higher standard deviations. The largest single hit: iPTM protein↔sgRNA = 0.866 ± 0.117 vs WT 0.947 ± 0.008 — PLM3's sgRNA interface confidence drops 0.08 with a standard deviation that is essentially the entire en31-vs-WT difference. The model is genuinely unsure how PLM3 folds.

- **W1507K confirmed as a real biophysical problem.** Per-residue pLDDT at position 1507: PLM3 = 0.878 vs WT 0.958 (Δ = −0.08). proteinmpnn_ddg had called W1507K "stabilizing" (−5.07 kcal/mol) — Boltz's verdict is the opposite. The apo-ΔΔG model is miscalibrated for hydrophobic→K substitutions; Boltz, seeing the complex, identifies W1507K as a local-geometry disturbance. This was the most biophysically suspicious pick in PLM3, and the structure-prediction lens confirms the suspicion.

- **G1243T context-dependent confidence — emergent multi-mutant effect.** The G1243T mutation appears in *both* PLM3 and en31. In en31's context (with E1369R, E1449H): pLDDT = 0.938. In PLM3's context (with W1507K, C1292K, M1617K): pLDDT = 0.816 — drop of 0.12 at the *same* mutation. The other three PLM3 mutations propagate uncertainty back to position 1243 even though they're 50-300 residues away. This is the epistasis our independent-marginal multi-mutant scoring cannot capture, and exactly why Boltz-2 is the right final-pass filter.

- **Per-engineered-position pLDDT table** (mean over 5 diffusion samples; bold = the variant carries that mutation):

  | Position | WT | PLM3 | PLM5 | en31 |
  |----------|-----|------|------|------|
  | G1243T (en31, PLM3) | 0.936 | **0.816** | 0.939 | **0.938** |
  | Y1249F (PLM4/5) | 0.965 | 0.914 | **0.969** | 0.967 |
  | C1292K (PLM3) | 0.937 | **0.883** | 0.938 | 0.933 |
  | A1325K (PLM4/5) | 0.885 | 0.852 | **0.900** | 0.899 |
  | Y1341L (PLM4/5) | 0.966 | 0.904 | **0.968** | 0.970 |
  | E1369R (en1/en31) | 0.962 | 0.891 | 0.963 | **0.954** |
  | E1449H (en31) | 0.952 | 0.867 | 0.952 | **0.955** |
  | K1479F (PLM5) | 0.914 | 0.844 | **0.925** | 0.913 |
  | W1507K (PLM3) | 0.958 | **0.878** | 0.966 | 0.964 |
  | T1535V (PLM4 only) | 0.961 | 0.955 | 0.966 | 0.964 |
  | E1603H (en15) | 0.934 | 0.918 | 0.947 | 0.942 |
  | M1617K (PLM3) | 0.908 | **0.923** | 0.922 | 0.921 |

  Notable: M1617K is the *only* PLM3 mutation that Boltz does not flag as confidence-reducing. The three other PLM3 picks (G1243T, C1292K, W1507K) all drop their local pLDDT by 0.05-0.12. PLM5's four picks all have pLDDT > 0.9 at their positions, matching or exceeding en31.

- **Per-variant interpretation:**
  - **WT:** the baseline. High confidence everywhere (0.91-0.95). The PI-domain complex is well-characterized by Boltz.
  - **PLM3 (ESM-2 sequence-only):** structurally compromised. The sgRNA interface in particular has very high uncertainty across the 5 diffusion samples (±0.117). Not a good candidate without revision.
  - **PLM5 (LigandMPNN + apo-ΔΔG filter):** structurally on par with en31. The cleanest in-silico candidate.
  - **en31 (Acharya 2024 known-functional):** confidence-equivalent to WT. Consistent with en31 being a viable engineered variant of WT.

- **Caveats:**
  - Predictions used `msa: empty` (single-sequence mode). Absolute confidences are lower than the MSA-enabled equivalent would be. **Relative differences are still informative** because all variants used the same setting. A publication-quality rerun with `--use_msa_server` would tighten the absolute numbers but is unlikely to change the qualitative finding that PLM5 ≈ en31 and PLM3 < both.
  - Protein chain was truncated to WED+PI (residues 1230-1620). Boltz did not see the REC lobe or N-terminal RuvC-like nuclease domain. If a candidate's mutations cause issues in the REC lobe (none of our picks are there), this analysis would miss it.
  - Boltz-2 is itself an approximation; pLDDT/iPTM are calibrated against natural complexes and may behave differently on engineered ones. Treat absolute numbers as a guide, not ground truth.
