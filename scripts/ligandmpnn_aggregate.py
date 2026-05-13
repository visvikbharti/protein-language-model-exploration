"""Aggregate per-position aa frequencies from LigandMPNN sampled sequences.

LigandMPNN writes sequences whose length equals the number of resolved
residues in chain A (not UniProt length). We map sample-string indices
back to UniProt positions via the PDB ATOM records.

Output: TSV with one row per UniProt residue in the design region,
giving the WT amino acid and the per-temperature + pooled frequency of
each amino acid across all samples.
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

AAS = "ACDEFGHIKLMNPQRSTVWY"


def parse_fasta(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    header: str | None = None
    seq_parts: list[str] = []
    with path.open() as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if header is not None:
                    out.append((header, "".join(seq_parts)))
                header = line[1:]
                seq_parts = []
            else:
                seq_parts.append(line)
        if header is not None:
            out.append((header, "".join(seq_parts)))
    return out


def extract_resolved_positions(pdb_path: Path) -> list[int]:
    """Ordered list of UniProt positions for chain A CA atoms."""
    positions: list[int] = []
    seen: set[int] = set()
    with pdb_path.open() as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            if line[21] != "A":
                continue
            if line[12:16].strip() != "CA":
                continue
            resseq = int(line[22:26])
            if resseq in seen:
                continue
            seen.add(resseq)
            positions.append(resseq)
    return positions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True,
                        help="LigandMPNN run dir containing T<temp>/seqs/5B2O.fa")
    parser.add_argument("--pdb", default="data/raw/5B2O.pdb")
    parser.add_argument("--design-region", default="1230-1620")
    parser.add_argument("--temperatures", nargs="+", default=["0.1", "0.2", "0.3"])
    parser.add_argument("--output",
                        help="Output TSV (default: <run-dir>/aggregate.tsv)")
    args = parser.parse_args()

    region_lo, region_hi = (int(x) for x in args.design_region.split("-"))
    run_dir = Path(args.run_dir)
    out_path = Path(args.output) if args.output else run_dir / "aggregate.tsv"

    resolved_positions = extract_resolved_positions(Path(args.pdb))
    log.info("Chain A: %d resolved positions (range %d-%d)",
             len(resolved_positions), resolved_positions[0], resolved_positions[-1])
    pos_to_idx = {pos: i for i, pos in enumerate(resolved_positions)}

    by_temp: dict[str, dict[int, Counter]] = {}
    wt_by_pos: dict[int, str] = {}
    n_samples_per_temp: dict[str, int] = {}

    for temp in args.temperatures:
        fa = run_dir / f"T{temp}" / "seqs" / "5B2O.fa"
        if not fa.exists():
            log.error("Missing %s", fa)
            return 1
        records = parse_fasta(fa)
        if len(records) < 2:
            log.error("Only %d records in %s — no samples?", len(records), fa)
            return 1
        reference = records[0][1]
        samples = [seq for _, seq in records[1:]]
        n_samples_per_temp[temp] = len(samples)
        log.info("T=%s: %d samples (reference len=%d)",
                 temp, len(samples), len(reference))

        # Anchor WT from the reference at each design position
        for uniprot_pos in range(region_lo, region_hi + 1):
            if uniprot_pos not in pos_to_idx:
                continue
            wt_aa = reference[pos_to_idx[uniprot_pos]]
            if uniprot_pos in wt_by_pos:
                if wt_by_pos[uniprot_pos] != wt_aa:
                    log.error("WT mismatch at %d: %s vs %s",
                              uniprot_pos, wt_by_pos[uniprot_pos], wt_aa)
                    return 1
            else:
                wt_by_pos[uniprot_pos] = wt_aa

        counts: dict[int, Counter] = {
            pos: Counter() for pos in range(region_lo, region_hi + 1)
            if pos in pos_to_idx
        }
        for seq in samples:
            if len(seq) != len(reference):
                log.error("Length mismatch in sample: %d vs reference %d",
                          len(seq), len(reference))
                return 1
            for uniprot_pos in counts:
                counts[uniprot_pos][seq[pos_to_idx[uniprot_pos]]] += 1
        by_temp[temp] = counts

    # Pool across temperatures
    first_temp = args.temperatures[0]
    pooled: dict[int, Counter] = {pos: Counter() for pos in by_temp[first_temp]}
    for counts in by_temp.values():
        for pos, ctr in counts.items():
            pooled[pos].update(ctr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        header = ["pos", "wt", "wt_freq_pooled"]
        for temp in args.temperatures:
            header += [f"wt_freq_T{temp}", f"top_aa_T{temp}", f"top_freq_T{temp}"]
        header += ["top_aa_pooled", "top_freq_pooled"]
        for aa in AAS:
            header.append(f"freq_pooled_{aa}")
        f.write("\t".join(header) + "\n")

        for pos in sorted(pooled.keys()):
            wt = wt_by_pos.get(pos, "?")
            pool_total = sum(pooled[pos].values())
            row = [str(pos), wt, f"{pooled[pos][wt] / pool_total:.4f}"]
            for temp in args.temperatures:
                ct = by_temp[temp][pos]
                tot = sum(ct.values())
                row.append(f"{ct[wt] / tot:.4f}")
                top_aa, top_n = ct.most_common(1)[0]
                row.append(top_aa)
                row.append(f"{top_n / tot:.4f}")
            top_pool_aa, top_pool_n = pooled[pos].most_common(1)[0]
            row.append(top_pool_aa)
            row.append(f"{top_pool_n / pool_total:.4f}")
            for aa in AAS:
                row.append(f"{pooled[pos][aa] / pool_total:.4f}")
            f.write("\t".join(row) + "\n")
    log.info("Wrote %s", out_path)

    log.info("\n=== LigandMPNN posterior at en31/en15 reference positions ===")
    log.info("%-22s  %-12s  %-12s  %-22s", "Mutation", "WT freq", "target freq", "top non-WT")
    for pos, target_aa, name in [
        (1243, "T", "en31 G1243T  (WED)"),
        (1369, "R", "en1/en31 E1369R (PI)"),
        (1449, "H", "en31 E1449H  (PI)"),
        (1603, "H", "en15 E1603H  (PI)"),
    ]:
        if pos not in pooled:
            log.info("  %-22s  not in design region", name)
            continue
        wt = wt_by_pos[pos]
        tot = sum(pooled[pos].values())
        wt_freq = pooled[pos][wt] / tot
        target_freq = pooled[pos][target_aa] / tot
        # Top non-WT amino acid + its frequency
        non_wt = [(aa, n) for aa, n in pooled[pos].most_common() if aa != wt]
        top_nonwt = f"{non_wt[0][0]}={non_wt[0][1] / tot:.3f}" if non_wt else "—"
        log.info("  %-22s  %s=%.3f      %s=%.3f      %s",
                 name, wt, wt_freq, target_aa, target_freq, top_nonwt)

    log.info("\nPositions where LigandMPNN top-pick differs from WT (sorted by |1 - wt_freq_pooled|):")
    divergent = []
    for pos, ctr in pooled.items():
        wt = wt_by_pos.get(pos)
        if wt is None:
            continue
        tot = sum(ctr.values())
        wt_freq = ctr[wt] / tot
        top_aa, top_n = ctr.most_common(1)[0]
        top_freq = top_n / tot
        if top_aa != wt:
            divergent.append((pos, wt, top_aa, wt_freq, top_freq))
    divergent.sort(key=lambda x: -x[4])
    log.info("  Total positions where top-pick != WT: %d / %d",
             len(divergent), len(pooled))
    for pos, wt, top, wt_f, top_f in divergent[:15]:
        log.info("  pos %4d  WT=%s  top=%s  WT_freq=%.3f  top_freq=%.3f",
                 pos, wt, top, wt_f, top_f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
