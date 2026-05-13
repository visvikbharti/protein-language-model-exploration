"""Structure-based analysis of FnCas9 mutation sites using PDB 5B2O.

For each mutation site in FnCas9-PLM1 and reference engineered variants (en31,
en15, en1), characterise the structural context using PDB 5B2O:
  - Domain assignment (WED / PI / REC / HNH / RuvC) by published boundaries
  - Secondary structure (helix / sheet / loop) — assigned by phi/psi via biotite
  - Solvent-accessible surface area (Shrake-Rupley via biotite.structure.sasa)
  - Number of protein neighbors within 6 Å (heavy atoms)
  - Distance to nearest DNA atom (target strand and non-target strand)
  - Distance to nearest sgRNA atom

Output: results/runs/<date>_structure/mutation_site_table.tsv
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

import biotite.structure as struc
import biotite.structure.io.pdb as pdb

# Published FnCas9 domain boundaries (Hirano et al. Cell 2016, Acharya 2024).
# 1-indexed inclusive ranges in the UniProt A0Q5Y3 numbering.
FNCAS9_DOMAINS: list[tuple[str, int, int]] = [
    ("RuvC-I",   1,   75),
    ("Bridge",   76,  189),
    ("REC1",     190, 469),
    ("REC2",     470, 729),
    ("REC3",     730, 879),  # approximate
    ("HNH",      880, 1029),
    ("RuvC-II",  1030, 1156),
    ("RuvC-III", 1157, 1232),
    ("WED",      1233, 1349),
    ("PI",       1350, 1629),
]

EN1_MUTATIONS = ["E1369R"]
EN15_MUTATIONS = ["E1603H"]
EN31_MUTATIONS = ["G1243T", "E1369R", "E1449H"]


def domain_for(pos: int) -> str:
    for name, lo, hi in FNCAS9_DOMAINS:
        if lo <= pos <= hi:
            return name
    return "?"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdb", default="data/raw/5B2O.pdb")
    parser.add_argument(
        "--plm1-meta",
        required=True,
        help="Path to FnCas9-PLM1.meta.json from build_candidate.py",
    )
    parser.add_argument(
        "--output-dir",
        default=f"results/runs/{datetime.now(timezone.utc):%Y-%m-%d}_structure",
    )
    args = parser.parse_args()

    plm1_meta = json.loads(Path(args.plm1_meta).read_text())
    plm1_muts = plm1_meta["mutations"].split("/")
    log.info("FnCas9-PLM1 mutations: %s", plm1_muts)

    all_sites = sorted(set(
        int(m[1:-1]) for m in (plm1_muts + EN31_MUTATIONS + EN15_MUTATIONS + EN1_MUTATIONS)
    ))
    log.info("Analyzing %d unique mutation sites: %s", len(all_sites), all_sites)

    # Load PDB
    pdb_file = pdb.PDBFile.read(args.pdb)
    structure = pdb_file.get_structure(model=1)
    log.info("Loaded %s — %d atoms across %d chains", args.pdb, structure.array_length(),
             len(set(structure.chain_id)))

    # Identify chains
    chain_ids = sorted(set(structure.chain_id))
    log.info("Chains in 5B2O: %s", chain_ids)

    # Protein chain — find the longest amino-acid chain
    protein = structure[struc.filter_amino_acids(structure)]
    chain_residue_counts = {
        c: len(set(protein[protein.chain_id == c].res_id))
        for c in sorted(set(protein.chain_id))
    }
    log.info("Protein residues per chain: %s", chain_residue_counts)
    protein_chain = max(chain_residue_counts, key=lambda c: chain_residue_counts[c])
    log.info("Using protein chain: %s", protein_chain)
    protein = protein[protein.chain_id == protein_chain]

    # DNA / sgRNA chains (anything that's not amino-acid)
    nonprotein = structure[~struc.filter_amino_acids(structure)]
    nonprotein = nonprotein[~struc.filter_solvent(nonprotein)]
    log.info("Non-protein chains: %s", sorted(set(nonprotein.chain_id)))

    # We classify nucleic acid chains by residue name heuristically
    nuc_res = set(nonprotein.res_name)
    log.info("Non-protein residue names: %s", sorted(nuc_res))
    dna_resnames = {"DA", "DC", "DG", "DT", "DI", "DU"}
    rna_resnames = {"A", "C", "G", "U", "I"}
    dna = nonprotein[np.isin(nonprotein.res_name, list(dna_resnames))]
    rna = nonprotein[np.isin(nonprotein.res_name, list(rna_resnames))]
    log.info("DNA atoms: %d, RNA atoms: %d", dna.array_length(), rna.array_length())

    # Compute SASA for the protein chain
    log.info("Computing SASA (Shrake-Rupley)...")
    sasa = struc.sasa(protein, probe_radius=1.4, point_number=200)
    # sasa is per-atom; reduce to per-residue by summing
    residue_starts = struc.get_residue_starts(protein)
    res_sasa: dict[int, float] = {}
    for rs, re in zip(residue_starts, list(residue_starts[1:]) + [protein.array_length()]):
        res_id = int(protein.res_id[rs])
        res_sasa[res_id] = float(np.nan_to_num(sasa[rs:re]).sum())

    # Build per-residue context for each mutation site
    rows: list[dict] = []
    for site in all_sites:
        site_atoms = protein[protein.res_id == site]
        if site_atoms.array_length() == 0:
            log.warning("Residue %d not present in PDB 5B2O", site)
            rows.append({
                "pos": site,
                "domain": domain_for(site),
                "in_pdb": False,
            })
            continue

        site_res_name = site_atoms.res_name[0]

        # Center of mass (or CA position) of this residue
        ca = site_atoms[site_atoms.atom_name == "CA"]
        if ca.array_length() == 0:
            log.warning("Residue %d has no CA atom", site)
            continue
        ca_xyz = ca.coord[0]

        # Neighbors within 6 Å (heavy atoms in other residues, same chain)
        other = protein[(protein.res_id != site)]
        if other.array_length():
            d = np.linalg.norm(other.coord - ca_xyz, axis=1)
            n_neighbors_6A = int((d < 6.0).sum())
            # Per residue count
            close_atoms = other[d < 6.0]
            n_res_within_6A = len(set(close_atoms.res_id))
        else:
            n_neighbors_6A = 0
            n_res_within_6A = 0

        # Distance to nearest DNA atom
        if dna.array_length():
            d_dna = float(np.linalg.norm(dna.coord - ca_xyz, axis=1).min())
        else:
            d_dna = float("inf")
        # Distance to nearest RNA atom
        if rna.array_length():
            d_rna = float(np.linalg.norm(rna.coord - ca_xyz, axis=1).min())
        else:
            d_rna = float("inf")

        row = {
            "pos": site,
            "wt_resname": site_res_name,
            "domain": domain_for(site),
            "ca_in_pdb": True,
            "sasa_A2": round(res_sasa.get(site, float("nan")), 1),
            "n_heavy_neighbors_6A": n_neighbors_6A,
            "n_residues_6A_of_CA": n_res_within_6A,
            "nearest_DNA_A": round(d_dna, 2),
            "nearest_RNA_A": round(d_rna, 2),
            "is_en31_site": site in [int(m[1:-1]) for m in EN31_MUTATIONS],
            "is_en15_site": site in [int(m[1:-1]) for m in EN15_MUTATIONS],
            "is_plm1_site": site in [int(m[1:-1]) for m in plm1_muts],
        }
        rows.append(row)
        log.info(
            "  pos %4d  %s  domain=%-9s  SASA=%6.1f Å²  neighbors=%3d  d_DNA=%5.2f Å  d_RNA=%5.2f Å",
            site, site_res_name, row["domain"], row["sasa_A2"],
            row["n_residues_6A_of_CA"], row["nearest_DNA_A"], row["nearest_RNA_A"],
        )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tsv = out_dir / "mutation_site_table.tsv"
    with tsv.open("w") as f:
        cols = ["pos", "wt_resname", "domain", "sasa_A2", "n_heavy_neighbors_6A",
                "n_residues_6A_of_CA", "nearest_DNA_A", "nearest_RNA_A",
                "is_en31_site", "is_en15_site", "is_plm1_site"]
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    log.info("Wrote %s", tsv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
