"""Generate Boltz-2 YAMLs for a PAM-variant scan: {WT, PLM5, en31} x {NGA, NAG, NCG, NTG, NAA}.

§2.4 fallback (Reading B in the 2026-05-18 PAM-tolerance plan): Protein2PAM cannot
resolve our variants, so we directly test PAM specificity by predicting the complex
with each candidate PAM swapped in. PLM5 is en31-class if it tolerates non-NGG PAMs
better than WT does.

PAM strand: chain D = 5'-TGGTATCGG-3' (9 nt). Positions 1-3 (TGG) are the PAM.
We keep position 1 as T (the "N" — unconstrained nucleotide) and vary positions
2 and 3 to scan {GA, AG, CG, TG, AA} alongside the original GG.

Target strand: chain C = 5'-CCGATACCACCCCAGCGCACCTAATTTCCC-3' (30 nt). The first
9 nt (CCGATACCA) is the duplex region anti-parallel to chain D. The PAM-strand
positions 1-3 base-pair with target-strand positions 7-9 (anti-parallel reverse
complement). So when we swap chain D positions 2,3 to PAM[1],PAM[2], we must
swap chain C positions 7,8 to complement(PAM[2]),complement(PAM[1]).

The NGG control (original 5B2O) is already in results/runs/2026-05-15_boltz_complex/
for WT, PLM5, en31 — we don't re-run it. We generate 5 new PAMs × 3 variants = 15
new YAMLs.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from prepare_boltz_yamls import extract_chain, write_yaml  # reuse existing helpers
from nuclease_design.io import load_fasta
from nuclease_design.variants import apply_mutant, parse_mutant


# Five non-NGG PAMs to scan. Plus NGG-by-NGG keep-as-original for sanity if desired.
# (We don't re-run NGG since we already have those results.)
PAM_VARIANTS = ["NGA", "NAG", "NCG", "NTG", "NAA"]

COMPLEMENT = str.maketrans("ACGT", "TGCA")


def make_pam_chain_d(original_d: str, pam: str) -> str:
    """Original chain D = 5'-TGGTATCGG-3'. Replace positions 2,3 with pam[1:3].

    Position 1 (T) stays as the "N" representative — Cas PAMs are defined
    such that position 1 is unconstrained.
    """
    assert len(original_d) == 9 and original_d.startswith("TGG"), \
        f"unexpected chain D: {original_d}"
    assert len(pam) == 3 and pam[0] == "N", f"PAM must be N-prefixed 3mer, got: {pam}"
    new_pos23 = pam[1] + pam[2]
    return original_d[0] + new_pos23 + original_d[3:]  # T + <new> + TATCGG


def make_paired_chain_c(original_c: str, pam: str) -> str:
    """Original chain C first 9 nt = CCGATACCA. The PAM-paired positions on chain
    C are positions 7, 8, 9 (1-indexed). Position 9 pairs with chain D position 1
    (unchanged), position 8 pairs with chain D position 2, position 7 pairs with
    chain D position 3.

    Update positions 7, 8 to the anti-parallel complement of pam[2], pam[1].
    """
    assert len(original_c) == 30 and original_c.startswith("CCGATACCA"), \
        f"unexpected chain C: {original_c}"
    assert len(pam) == 3 and pam[0] == "N", f"PAM must be N-prefixed 3mer, got: {pam}"
    new_c7 = pam[2].translate(COMPLEMENT)  # paired with chain D pos 3 = pam[2]
    new_c8 = pam[1].translate(COMPLEMENT)  # paired with chain D pos 2 = pam[1]
    # position 9 pairs with chain D pos 1 (T → A), unchanged
    new_c_first9 = original_c[:6] + new_c7 + new_c8 + original_c[8]
    return new_c_first9 + original_c[9:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdb", default="data/raw/5B2O.pdb")
    parser.add_argument("--wt-fasta", default="data/raw/A0Q5Y3_fncas9.fasta")
    parser.add_argument("--output-dir", default="hpc/inputs")
    parser.add_argument("--truncate", default="1230-1620",
                        help="Same truncation as the campaign Boltz runs.")
    args = parser.parse_args()

    pdb_path = Path(args.pdb)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Extracting nucleic-acid chains from %s ...", pdb_path)
    sgRNA = extract_chain(pdb_path, "B", "rna")
    dna_C = extract_chain(pdb_path, "C", "dna")  # target strand
    dna_D = extract_chain(pdb_path, "D", "dna")  # PAM strand
    log.info("  sgRNA (chain B, %d nt): %s", len(sgRNA), sgRNA)
    log.info("  DNA   (chain C, %d nt): %s", len(dna_C), dna_C)
    log.info("  DNA   (chain D, %d nt): %s", len(dna_D), dna_D)

    wt = load_fasta(Path(args.wt_fasta))[0].sequence
    log.info("FnCas9 WT: %d aa", len(wt))

    protein_variants = {
        "fncas9_wt":   wt,
        "fncas9_plm5": apply_mutant(wt, parse_mutant("Y1249F/Y1341L/A1325K/K1479F")),
        "fncas9_en31": apply_mutant(wt, parse_mutant("G1243T/E1369R/E1449H")),
    }

    if args.truncate:
        lo, hi = (int(x) for x in args.truncate.split("-"))
        protein_variants = {k: v[lo - 1:hi] for k, v in protein_variants.items()}
        log.info("Truncated protein chains to residues %d-%d (length %d)",
                 lo, hi, hi - lo + 1)

    n_yamls = 0
    for prot_slug, prot_seq in protein_variants.items():
        for pam in PAM_VARIANTS:
            new_dna_D = make_pam_chain_d(dna_D, pam)
            new_dna_C = make_paired_chain_c(dna_C, pam)
            slug = f"{prot_slug}_pam_{pam}"
            yaml_path = out_dir / f"boltz_{slug}.yaml"
            write_yaml(yaml_path, f"FnCas9-{prot_slug.replace('fncas9_', '').upper()} PAM={pam}",
                       prot_seq, sgRNA, new_dna_C, new_dna_D, use_msa_server=True)
            n_yamls += 1
            log.info("  PAM=%s: chain D = %s, chain C[:9] = %s",
                     pam, new_dna_D, new_dna_C[:9])

    log.info("\nDone. Wrote %d YAMLs (3 variants × %d non-NGG PAMs).",
             n_yamls, len(PAM_VARIANTS))
    log.info("NGG control runs are already in results/runs/2026-05-15_boltz_complex/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
