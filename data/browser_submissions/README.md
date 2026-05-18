# Browser-task submissions — §2.4 Protein2PAM + §2.1 AF3 Server

**Purpose:** Close the last two open robustness criteria via free web services.
**Created:** 2026-05-18

Do these in two browser tabs while the HPC Chai-1 work runs in parallel. Both are zero-compute on your side.

---

## §2.4 — Protein2PAM scan (closes criterion 2)

**Service:** https://protein2pam.profluent.bio/
**License:** Polyform-NC — academic in-silico use cleared (Round 1 verification).
**Paper:** Nayfach et al. 2026, *Nat Biotechnol* — DOI 10.1038/s41587-025-02995-0.

### Inputs

File: `data/browser_submissions/protein2pam_4variants.fasta` (4 sequences in one FASTA — WT, PLM4, PLM5, en31).

If the web service prefers one-sequence-at-a-time submission, use:
- `af3server_WT_protein.fasta`
- `af3server_PLM4_protein.fasta`
- `af3server_PLM5_protein.fasta`
- `af3server_en31_protein.fasta`

(They're the same protein sequences; the AF3-named files are just per-variant copies.)

### Submission steps

1. Open https://protein2pam.profluent.bio/
2. For each variant: paste the FASTA → run.
3. Save the output PAM PWM / motif logo per variant (download as PNG or copy the PWM matrix).

### Success criterion

PLM5 shows a predicted PAM profile **at least as relaxed as en31** (which itself broadens NGG → NGG/NGA/NAG per Acharya 2024). WT should look NGG-restrictive. If PLM5 looks NGG-restrictive, that's a flag for §2.4 — it would mean structural en31-likeness in Boltz doesn't translate to predicted functional PAM relaxation.

### Where to record

Save PWM/logo images to `data/browser_submissions/protein2pam_output/<variant>.png` and the PWM table to `<variant>.tsv`. I'll then write up a comparison in `notes/plm/verification-log.md` and flip §6 criterion 2.

---

## §2.1 — AlphaFold3 Server submission (closes criterion 1's second-predictor leg)

**Service:** https://alphafoldserver.com
**License:** Free academic use; 30 jobs/day; 5,000-token-per-job limit.
**Paper:** Abramson et al. 2024, *Nature* — AlphaFold3.

### Inputs (per variant — submit 3 jobs)

For each of {WT, PLM5, en31}, create a job with **4 entities**:

| Entity | Type | Sequence source |
|---|---|---|
| 1 | Protein | `af3server_WT_protein.fasta` (or PLM5 / en31) — 1629 aa |
| 2 | RNA     | sgRNA below (93 nt) |
| 3 | DNA     | DNA target strand below (30 nt) |
| 4 | DNA     | DNA PAM strand below (9 nt) |

**Token budget:** 1629 + 93 + 30 + 9 = 1,761 tokens. Well under the 5,000 limit. (Full-length FnCas9 OOM'd on V100 Boltz; AF3 Server has substantially more compute headroom.)

### Sequences (copy-paste-ready)

**sgRNA (chain B, 93 nt RNA):**
```
GGGAAAUUAGGUGCGCUGGGGGUUUCAGUUGCGCCGAAAGGCGCUCUGUAAUCAUUAAAAGUAUUUUGAACGGACCUCUGUUUGACACGUCUG
```

**DNA target strand (chain C, 30 nt DNA):**
```
CCGATACCACCCCAGCGCACCTAATTTCCC
```

**DNA PAM strand (chain D, 9 nt DNA):**
```
TGGTATCGG
```

(All three nucleic-acid sequences are extracted from PDB 5B2O — same as our Boltz runs, for apples-to-apples comparison.)

### Submission steps (per variant)

1. Open https://alphafoldserver.com → "New job"
2. Add protein entity → paste the variant's 1629-aa sequence
3. Add RNA entity → paste sgRNA (93 nt)
4. Add DNA entity → paste DNA target (30 nt)
5. Add DNA entity → paste DNA PAM strand (9 nt)
6. Job name: `FnCas9_<variant>_full` (e.g. `FnCas9_PLM5_full`)
7. Submit. ~few-minute queue.

### Success criterion

AF3 confidence metrics for PLM5 ≥ en31 (or within ~1σ) — on iPTM (or AF3's analogous interface metric) and on per-residue pLDDT at the four PLM5 positions. **If AF3 agrees that PLM5 is en31-class, criterion 1 closes ✅** with two independent predictors (Boltz + AF3).

### Where to record

When jobs finish:
- Download the per-job ZIP from AF3 Server (contains JSON metrics + CIF structures).
- Save under `data/browser_submissions/af3_server_output/FnCas9_<variant>_full.zip`.
- I'll extract the metrics and write up the comparison in `notes/plm/verification-log.md`.

---

## Status tracking

| Task | Status |
|---|---|
| §2.4 Protein2PAM WT | ☐ submitted ☐ results saved |
| §2.4 Protein2PAM PLM4 | ☐ submitted ☐ results saved |
| §2.4 Protein2PAM PLM5 | ☐ submitted ☐ results saved |
| §2.4 Protein2PAM en31 | ☐ submitted ☐ results saved |
| §2.1 AF3 Server WT | ☐ submitted ☐ done ☐ downloaded |
| §2.1 AF3 Server PLM5 | ☐ submitted ☐ done ☐ downloaded |
| §2.1 AF3 Server en31 | ☐ submitted ☐ done ☐ downloaded |

Update the boxes as you go (or just tell me "Protein2PAM done", "AF3 PLM5 done" etc. and I'll handle the recording).
