# enFnCas9 — Engineered FnCas9 from CSIR-IGIB

**Last verified:** 2026-05-12 (round 1; see `verification-log.md`)
**Primary source:** Acharya, S. et al. (2024). *Nature Communications* 15:5471. DOI: [10.1038/s41467-024-49233-w](https://doi.org/10.1038/s41467-024-49233-w). PubMed [38942756](https://pubmed.ncbi.nlm.nih.gov/38942756/). Open-access PMC: [PMC11213958](https://pmc.ncbi.nlm.nih.gov/articles/PMC11213958/).

## TL;DR

enFnCas9 is the CSIR-IGIB (Maiti & Chakraborty labs) engineered variant of FnCas9. **Three published variants — en1, en15, en31** — each at least 2× the in-vitro cleavage rate of WT FnCas9, with the PAM relaxed from strict NGG to **5'-NRG/NGR-3'** (~3.5× expansion of accessible human genome sites), while **retaining FnCas9's intrinsic high specificity** (~1,300-fold fewer off-targets than SpCas9, by Digenome-seq).

## Lineage

| Variant | Year | Mutations | PAM | Source |
|---|---|---|---|---|
| WT FnCas9 | 2013 / structurally 2016 | none | 5'-NGG-3' | UniProt A0Q5Y3; PDB 5B2O |
| FnCas9-RHA | 2016 | **E1369R / E1449H / R1556A** (triple) | 5'-YG-3' | Hirano et al. *Cell* 164:950 |
| en1 | 2024 | **E1369R** (single, PI domain) | 5'-NRG/NGR-3' | Acharya et al. *Nat Commun* 15:5471 |
| en15 | 2024 | **E1603H** (single, PI/WED interface) | 5'-NRG/NGR-3' | Acharya et al. *Nat Commun* 15:5471 |
| en31 | 2024 | **G1243T / E1369R / E1449H** (triple; PLL + PI) | 5'-NGG > NGA > NAG-3' | Acharya et al. *Nat Commun* 15:5471 |

> **Watchpoint:** Earlier drafts described FnCas9-RHA as the double E1369R/E1449H. The actual Hirano 2016 RHA variant is the **triple including R1556A** — verify in PI-domain modeling.

## What the mutations do (paper-stated mechanism)

- **G1243T** — phosphate-lock loop (WED domain). Adds a new H-bond to the target-strand +1 phosphate. Accelerates DNA unwinding (cleavage k_cat).
- **E1369R** — PI domain. Reverses surface charge, contacts dA(−1) backbone phosphate of the target strand. Relaxes PAM toward purine flexibility.
- **E1449H** — PI domain. Pairs with E1369R to stabilise non-canonical PAM duplexes. (Note: this is one of the residues of the Hirano 2016 RHA double; here it appears as a component of en31 only.)
- **E1603H** (en15) — PI / WED interface. Single substitution sufficient to stabilise non-NGG PAM binding; binding K_d to mismatched substrate substantially lower than WT.

## Performance numbers (primary-source verified)

| Assay | Substrate / context | Number | Source |
|---|---|---|---|
| In-vitro DNA cleavage rate | various targets | ≥2× WT FnCas9 for en1, en15, en31 | Acharya 2024 |
| DNA binding K_d (MST, VEGFA3 substrate, 20-nt gRNA) | dFnCas9 variants | WT 170 ± 31.5 nM; en1 91.3 ± 29.8 nM; en15 49.2 ± 11.0 nM | Acharya 2024 |
| HEK293T indels at HBB (guide g21) | sickle-cell locus | ~90% with enFnCas9 (guide-dependent) | Acharya 2024 |
| HDR knock-in at DCX (~6.8 kb donor) | iPSC | en1 outperforms SpCas9-HF1 and eSpCas9 (qualitative only — exact % not extracted) | Acharya 2024 |
| PAM landscape | targetable human genome sites | ~3.5× expansion over WT | Acharya 2024 |
| Off-target specificity | Digenome-seq, whole genome | up to **~1,300×** fewer off-targets than SpCas9; ~700× fewer than SpRY | **Acharya 2024 itself** (not press release) |

## Native FnCas9 baseline

- **UniProt:** [A0Q5Y3](https://www.uniprot.org/uniprotkb/A0Q5Y3) — *F. tularensis* subsp. *novicida* U112; gene `cas9` / `FTN_0757`; **1,629 aa**; MW 190,461 Da.
- **PDB structures**:
  - [5B2O](https://www.rcsb.org/structure/5B2O) — WT + sgRNA + DNA, TGG PAM, 1.7 Å (Hirano 2016)
  - [5B2P](https://www.rcsb.org/structure/5B2P) — WT, TGA PAM, 1.7 Å
  - [5B2Q](https://www.rcsb.org/structure/5B2Q) — RHA variant, TGG PAM, 1.7 Å
- **AlphaFold model:** [AF-A0Q5Y3](https://alphafold.ebi.ac.uk/entry/A0Q5Y3)
- **Native PAM:** strict 5'-NGG-3'; R1556 and R1585 read the non-target dG2/dG3 via bidentate H-bonds.

## Why FnCas9 was worth engineering

- **Intrinsic specificity is exceptionally high** — single-mismatch binding is essentially abolished at the binding step (not just the cleavage step). Structurally distinct from SpCas9, which binds many off-targets and only filters via a conformational checkpoint. This is the basis of both the "ultra-precise" claim and FELUDA's mismatch discrimination.
- **Cellular activity is weak.** WT FnCas9 indel rates in mammalian cells were typically single-digit percent until enFnCas9 (and prior work tethering dSpCas9 as a "proxy" to open chromatin).

The enFnCas9 mutations were deliberately placed at the **PAM-readout / phosphate-lock interfaces** to preserve the REC-domain mismatch-sensing apparatus untouched.

## FELUDA (downstream application)

**FELUDA** = *FnCas9 Editor Linked Uniform Detection Assay*. Catalytically dead FnCas9 (dFnCas9) + FAM-labelled sgRNA + lateral-flow paper strip. Binds target nucleic acid only if perfectly complementary to the spacer. Used for:
- SNP discrimination (sickle-cell allele, etc.) — Azhar et al. 2021 *Biosens Bioelectron* (PMID 33866136)
- SARS-CoV-2 variant identification (N501Y, etc.) — Kumar et al. 2021 *eLife* 10:e67130 (PMID 34106048)
- Commercialised as TATA MD CHECK COVID-19 kit.

## Limitations standing in 2026 — design targets for our PLM redesign

1. **Size.** 1,629 aa exceeds single-AAV cargo (~4.7 kb coding limit). A compacted FnCas9-like scaffold is the biggest unmet need.
2. **PAM still NRG / NGR.** No PAM-less FnCas9 equivalent of SpRY exists.
3. **Chromatin accessibility** remains weaker than SpCas9 at some closed loci even for en31.
4. **No PDB structure of enFnCas9 itself** is available as of 2026-05; homology onto 5B2O / 5B2Q is the only structural reference.
5. **Non-standard sgRNA architecture** (longer than SpCas9 sgRNA) — engineering a compact guide is a parallel design target.
6. **HNH conformational checkpoint** is slower than SpCas9's, possibly limiting indel rates in some chromatin contexts.

## Other engineered FnCas9 / related orthologs

- **FnCas9-RHA** (Hirano 2016) — triple mutant E1369R / E1449H / **R1556A**; PAM 5'-YG-3'. Structural parent of enFnCas9.
- **FnCas9-AF2 / MUTE-Seq** (Ye et al., *Adv Materials* 2025, DOI [10.1002/adma.202505208](https://doi.org/10.1002/adma.202505208)) — advanced-fidelity FnCas9 for cfDNA mutation detection.
- **FrCas9** (Chen et al., *Nat Commun* 13, 2022, DOI [10.1038/s41467-022-29089-8](https://doi.org/10.1038/s41467-022-29089-8)) — *Faecalibaculum rodentium* ortholog; NNTA PAM; high-fidelity. Useful benchmark.

## Source accessions (download targets)

```
UniProt FASTA:   https://rest.uniprot.org/uniprotkb/A0Q5Y3.fasta
PDB 5B2O (WT):   https://files.rcsb.org/download/5B2O.pdb
PDB 5B2P (TGA):  https://files.rcsb.org/download/5B2P.pdb
PDB 5B2Q (RHA):  https://files.rcsb.org/download/5B2Q.pdb
AlphaFold model: https://alphafold.ebi.ac.uk/files/AF-A0Q5Y3-F1-model_v4.pdb
```

## Patents

- **US 11,970,699 B2** — "Kinetically enhanced engineered FnCas9 and its uses thereof." Inventors: Chakraborty, Maiti, Acharya, Nureki, Nishimasu, Hirano. Assignees: CSIR (India) + University of Tokyo. [Google Patents](https://patents.google.com/patent/US11970699B2/en).
- **WO 2023/275892 A1** — earlier WIPO filing covering en-variants.

## Related notes

- [[plm-nuclease-engineering]] — survey of PLM tools and prior PLM-designed nucleases
- [[verification-log]] — claim-by-claim verification record
- [[proteingym-substitutions]], [[proteingym-indels]] — PLM scoring benchmarks we'll lean on for fitness prediction
