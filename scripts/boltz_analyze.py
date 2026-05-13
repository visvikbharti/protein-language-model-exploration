"""Compare Boltz-2 complex predictions across WT / PLM3 / PLM5 / en31.

Reads the per-sample confidence JSONs (5 diffusion samples per variant) and
emits two outputs:

1. A summary table with mean ± std across the 5 samples for the key metrics
   (confidence_score, complex_plddt, iptm, chains_ptm, protein-DNA iptm).
2. Optionally a per-residue pLDDT trace at the engineered positions.

Designed for the truncated WED+PI run (residues 1230-1620 → indices 1-391
in the prediction). Engineered positions are auto-renumbered.
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# Chain index in Boltz's pair_chains_iptm: based on the YAML order
# 0 = protein A, 1 = RNA B, 2 = DNA C (target strand), 3 = DNA D (PAM strand)
CHAIN_PROT = "0"
CHAIN_RNA = "1"
CHAIN_DNA_TARGET = "2"
CHAIN_DNA_PAM = "3"

# Engineered positions (UniProt numbering). Indexed in the truncated chain as (pos - lo + 1).
ENGINEERED_POSITIONS = {
    "G1243T (en31, PLM3)":  1243,
    "Y1249F (PLM4/5)":      1249,
    "C1292K (PLM3)":        1292,
    "A1325K (PLM4/5)":      1325,
    "Y1341L (PLM4/5)":      1341,
    "E1369R (en1/en31)":    1369,
    "E1449H (en31)":        1449,
    "K1479F (PLM5)":        1479,
    "W1507K (PLM3)":        1507,
    "T1535V (PLM4 only)":   1535,
    "E1603H (en15)":        1603,
    "M1617K (PLM3)":        1617,
}


def load_confidence_jsons(variant_dir: Path) -> list[dict]:
    """Load all 5 confidence_*.json files for a variant."""
    pred_dirs = list((variant_dir).glob("boltz_results_*/predictions/boltz_*/"))
    if len(pred_dirs) != 1:
        log.warning("%s: expected 1 predictions/ dir, found %d", variant_dir, len(pred_dirs))
        if not pred_dirs:
            return []
    pred_dir = pred_dirs[0]
    jsons = sorted(pred_dir.glob("confidence_*.json"))
    return [json.loads(p.read_text()) for p in jsons]


def load_plddt_npz(variant_dir: Path) -> list:
    """Load per-residue pLDDT arrays from .npz files."""
    import numpy as np
    pred_dirs = list((variant_dir).glob("boltz_results_*/predictions/boltz_*/"))
    if not pred_dirs:
        return []
    pred_dir = pred_dirs[0]
    npzs = sorted(pred_dir.glob("plddt_*.npz"))
    out = []
    for p in npzs:
        d = np.load(p)
        # Boltz stores per-residue pLDDT under either "plddt" or first array
        if "plddt" in d.files:
            out.append(d["plddt"])
        else:
            out.append(d[d.files[0]])
    return out


def mean_std(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return (0.0, 0.0)
    if len(xs) == 1:
        return (xs[0], 0.0)
    return (statistics.mean(xs), statistics.stdev(xs))


def summarize_variant(name: str, samples: list[dict]) -> dict:
    """Average the 5-sample metrics for one variant."""
    if not samples:
        return {}
    out: dict[str, tuple[float, float]] = {}
    for key in ("confidence_score", "complex_plddt", "iptm", "ptm", "complex_iplddt"):
        out[key] = mean_std([s[key] for s in samples if key in s])
    # Chain-pair iPTM for the protein-DNA interfaces
    for label, c1, c2 in [
        ("prot_dna_target", CHAIN_PROT, CHAIN_DNA_TARGET),
        ("prot_dna_pam",    CHAIN_PROT, CHAIN_DNA_PAM),
        ("prot_rna",        CHAIN_PROT, CHAIN_RNA),
    ]:
        vals = []
        for s in samples:
            pair = s.get("pair_chains_iptm", {})
            if c1 in pair and c2 in pair[c1]:
                vals.append(pair[c1][c2])
        out[label] = mean_std(vals)
    # Per-chain pTM (protein chain confidence)
    chain_ptms = [s.get("chains_ptm", {}).get(CHAIN_PROT) for s in samples]
    chain_ptms = [v for v in chain_ptms if v is not None]
    out["protein_ptm"] = mean_std(chain_ptms)
    return out


def print_summary_table(summaries: dict[str, dict]) -> None:
    log.info("\n=== Boltz-2 complex confidence summary (mean ± std over 5 diffusion samples) ===\n")
    metrics = [
        ("confidence_score", "Overall confidence"),
        ("complex_plddt",    "Mean per-res pLDDT"),
        ("complex_iplddt",   "Interface pLDDT"),
        ("ptm",              "pTM (whole complex)"),
        ("iptm",              "iPTM (all interfaces)"),
        ("protein_ptm",      "pTM (protein chain)"),
        ("prot_dna_target",  "iPTM protein↔DNA-target"),
        ("prot_dna_pam",     "iPTM protein↔DNA-PAM"),
        ("prot_rna",         "iPTM protein↔sgRNA"),
    ]
    # Header
    header = f"{'Metric':<28}"
    for name in summaries:
        header += f"  {name:<14}"
    log.info(header)
    log.info("-" * len(header))
    for key, label in metrics:
        row = f"{label:<28}"
        for name in summaries:
            m, s = summaries[name].get(key, (0.0, 0.0))
            if m == 0.0 and s == 0.0:
                row += f"  {'n/a':<14}"
            else:
                row += f"  {m:.3f}±{s:.3f}  "
        log.info(row)


def per_residue_table(variants: dict[str, list], lo: int, hi: int) -> None:
    """Print per-engineered-position pLDDT across variants."""
    try:
        import numpy as np
    except ImportError:
        log.warning("numpy not available — skipping per-residue analysis")
        return

    log.info("\n=== Per-residue pLDDT at engineered positions (mean over 5 samples) ===\n")
    log.info("Truncated chain: UniProt residues %d-%d → indices 0-%d", lo, hi, hi - lo)

    header = f"{'Position':<28}"
    for name in variants:
        header += f"  {name:<10}"
    log.info(header)
    log.info("-" * len(header))

    for label, uniprot_pos in ENGINEERED_POSITIONS.items():
        if not (lo <= uniprot_pos <= hi):
            continue
        idx = uniprot_pos - lo
        row = f"{label:<28}"
        for name, arrays in variants.items():
            if not arrays:
                row += f"  {'n/a':<10}"
                continue
            vals = [a[idx] for a in arrays if idx < len(a)]
            if vals:
                m = float(np.mean(vals))
                row += f"  {m:.3f}    "
            else:
                row += f"  {'n/a':<10}"
        log.info(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="results/runs/2026-05-13_boltz_complex",
                        help="Top-level Boltz output dir containing fncas9_<variant>/ subdirs")
    parser.add_argument("--truncate-lo", type=int, default=1230,
                        help="Start of UniProt range used in the YAML")
    parser.add_argument("--truncate-hi", type=int, default=1620,
                        help="End of UniProt range used in the YAML")
    parser.add_argument("--no-per-residue", action="store_true",
                        help="Skip per-residue pLDDT analysis")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        log.error("No such dir: %s", run_dir)
        return 1

    variants = ["fncas9_wt", "fncas9_plm3", "fncas9_plm5", "fncas9_en31"]
    nice_names = {
        "fncas9_wt":   "WT",
        "fncas9_plm3": "PLM3",
        "fncas9_plm5": "PLM5",
        "fncas9_en31": "en31",
    }

    summaries: dict[str, dict] = {}
    plddt_arrays: dict[str, list] = {}
    for v in variants:
        vdir = run_dir / v
        if not vdir.exists():
            log.warning("Missing %s — skipping", vdir)
            continue
        samples = load_confidence_jsons(vdir)
        log.info("%s: %d confidence JSONs found", v, len(samples))
        summaries[nice_names[v]] = summarize_variant(v, samples)
        if not args.no_per_residue:
            plddt_arrays[nice_names[v]] = load_plddt_npz(vdir)

    print_summary_table(summaries)
    if not args.no_per_residue:
        per_residue_table(plddt_arrays, args.truncate_lo, args.truncate_hi)

    log.info("\n=== Interpretation hints ===")
    log.info("- iPTM > 0.85 = high-confidence interface; 0.6-0.85 = medium; <0.6 = low.")
    log.info("- complex_plddt > 0.85 = well-folded; 0.7-0.85 = medium; <0.7 = poor.")
    log.info("- Compare each candidate's iPTM(protein↔DNA-target) and (protein↔DNA-PAM)")
    log.info("  against WT and en31. A candidate that drops more than ~0.05 below WT/en31")
    log.info("  at the PAM-strand interface is breaking the PAM contact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
