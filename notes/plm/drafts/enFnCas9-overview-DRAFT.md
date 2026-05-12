# enFnCas9 — DRAFT survey (pending verification)

**Status:** DRAFT — every numerical claim and citation below must be cross-checked against the primary source before this draft is promoted to a non-DRAFT note. Verification pass tracked in `notes/plm/verification-log.md`.

**Surveyed by:** background literature agent, 2026-05-12
**Promoted to:** `notes/plm/enFnCas9-overview.md` after verification

---

## Canonical references claimed by the survey agent

- **Acharya et al. (2019)**, "Francisella novicida Cas9 interrogates genomic DNA with very high specificity and can be used for mammalian genome editing." *PNAS* 116(42): 20959–20968. DOI: 10.1073/pnas.1818461116. URL: https://www.pnas.org/doi/10.1073/pnas.1818461116
- **Acharya et al. (2024)**, "PAM-flexible Engineered FnCas9 variants for robust and ultra-precise genome editing and diagnostics." *Nature Communications* 15:5471. DOI: 10.1038/s41467-024-49233-w. PMC: PMC11213958. PubMed: 38942756. [VERIFY: paper title — exact wording, exact author list, exact article number]
- **Hirano et al. (2016)**, "Structure and Engineering of *Francisella novicida* Cas9." *Cell* 164(5): 950–961. DOI: 10.1016/j.cell.2016.01.039. PMC: PMC4899972
- **Patents**: US 11,970,699 B2 and WO 2023/275892 A1 (CSIR)

## WT FnCas9 baseline

- **UniProt**: A0Q5Y3, length 1,629 aa
- **PDB**: 5B2O (WT, TGG PAM, 1.7 Å), 5B2P (WT, TGA PAM), 5B2Q (RHA variant, TGG PAM)
- **Native PAM**: strict 5'-NGG-3' (R1556 and R1585 read dG2/dG3 of non-target strand)
- **Native activity**: low and locus-dependent in mammalian cells

## Mutations defining enFnCas9 (CLAIMED — VERIFY EACH)

| Position | WT → Variant | Domain | Mechanistic role (claimed) | Verification status |
|----------|--------------|--------|----------------------------|---------------------|
| G1243 | G → T | WED (phosphate-lock loop) | New H-bond to +1 phosphate of target strand at PLL; increases cleavage k_cat | [UNVERIFIED — pull Suppl Table 1 of Nat Commun 2024] |
| E1369 | E → R | PI (PAM-duplex binding) | Reverses charge; new contact with dA(−1) phosphate; relaxes PAM | [UNVERIFIED — pull paper] |
| E1449 | E → H | PI (PAM-duplex binding) | Partners with E1369R for non-canonical PAM stabilisation | [UNVERIFIED — pull paper] |

**Variant compositions claimed:**
- en1 = **E1369R** [UNVERIFIED]
- en15 = **E1603H** [UNVERIFIED — agent flagged this as uncertain]
- en31 = **G1243T + E1369R + E1449H** [UNVERIFIED]

## Performance numbers (CLAIMED — VERIFY EACH)

- *In vitro* cleavage: en1, en15, en31 each >2× WT FnCas9; en31 highest [UNVERIFIED]
- DNA binding K_d (catalytically dead): en1 = 91 ± 30 nM; en15 = 49 ± 11 nM [UNVERIFIED]
- HEK293T indels at HBB (sickle, guide g21): up to ~90% with enFnCas9 vs <10% WT FnCas9 [UNVERIFIED]
- Matches or exceeds SpCas9-HF1, eSpCas9 at on-target NGG sites; no detectable editing at mismatched off-targets [UNVERIFIED]
- HDR knock-in at DCX (~6.8 kb donor): outperforms SpCas9-HF1, eSpCas9 [UNVERIFIED — only qualitative]
- PAM landscape: WT NGG → enFnCas9 NRG/NGR → ~3.5× expansion [UNVERIFIED]
- Whole-genome off-target: ~1,300× higher specificity than SpCas9 [UNVERIFIED — sciencechronicle.in is not a primary source; find primary]

## FELUDA

FnCas9 Editor Linked Uniform Detection Assay using **dFnCas9** + FAM-labeled sgRNA + lateral-flow paper strip. Distinguishes SNPs (sickle), SARS-CoV-2 variants. References claimed: Azhar et al. *Biosens Bioelectron* 2021 (PMID 33866136); Kumar et al. *eLife* 2021;10:e67130. Commercialised as TATA MD CHECK COVID-19 kit. [UNVERIFIED]

## Limitations cited as design targets

- Size 1,629 aa > AAV single-vector cap (~4.7 kb)
- PAM still NRG/NGR (no PAM-less FnCas9 published)
- Cellular accessibility at closed chromatin
- Non-standard guide architecture
- No PDB structure of enFnCas9 itself as of search date
- HNH checkpoint slower than SpCas9

## Other engineered FnCas9 variants

- **FnCas9-RHA** (Hirano 2016): E1369R + E1449H — 5'-YG-3' PAM. Structural parent of enFnCas9.
- **afFnCas9** (Ye et al., *Adv Materials* 2025, "MUTE-seq") — ultra-sensitive cfDNA mutation detection [UNVERIFIED]
- **FrCas9** (Chen et al., *Nat Commun* 13, 2022, doi 10.1038/s41467-022-29089-8) — *Faecalibaculum rodentium*; NNTA PAM; high-fidelity ortholog [UNVERIFIED]

## Accessions and URLs to download

- UniProt FASTA: https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta
- PDB 5B2O: https://files.rcsb.org/download/5B2O.pdb
- PDB 5B2Q: https://files.rcsb.org/download/5B2Q.pdb
- AlphaFold A0Q5Y3: https://alphafold.ebi.ac.uk/entry/A0Q5Y3
- Nat Commun 2024: https://www.nature.com/articles/s41467-024-49233-w
- PMC mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC11213958/
- PNAS 2019: https://www.pnas.org/doi/10.1073/pnas.1818461116

## Gaps the survey agent flagged

1. Exact identity for en15 (E1603H vs. other)
2. Quantitative HDR percentages at DCX
3. Whether enFnCas9 tested in primary human T cells
4. No PDB entry for enFnCas9 itself
