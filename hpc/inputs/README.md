# HPC input templates

YAML configs that the SLURM jobs read. Place hand-edited variants here before running each job.

## `boltz_fncas9_plm2.yaml` (to be written)

Template for predicting the FnCas9-PLM2 + sgRNA + dsDNA complex with Boltz-2.

```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: |
        MNFKILPIAIDLGV...   # full FnCas9-PLM2 sequence (1629 aa)
      msa: empty            # rely on MSA server, or "empty" for single-sequence mode
  - rna:
      id: B
      sequence: |
        GAUUCUAAU...        # FnCas9 sgRNA, ~80 nt, repeat + spacer + tracrRNA
  - dna:
      id: C
      sequence: |
        ATGCTAA...          # target dsDNA, protospacer + PAM (NGG)
  - dna:
      id: D
      sequence: |
        ...                 # complementary strand
properties: []
```

The exact FnCas9 sgRNA scaffold sequence is in the Hirano 2016 paper supplementary materials. We can also use PDB 5B2O's sgRNA + DNA sequences directly (they are in the PDB header).

## `boltz_fncas9_plm2_PI_domain.yaml`

Same as above but truncated to the WED-PI region (residues 1230-1620 of FnCas9, ~391 aa). Use as a fallback if V100 OOMs on the full complex.

## `ligandmpnn_design_residues.txt`

Plain-text list of residues to design (mask) for LigandMPNN. Currently hardcoded in the SLURM script as `A1230-A1620`. Update here if you want a different design region.
