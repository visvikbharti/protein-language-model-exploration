"""Analyze AlphaFold3 Server output zips for the FnCas9 PLM-redesign campaign.

Expected layout (per variant) after the user downloads + unpacks the AF3 Server
job ZIPs into `data/browser_submissions/af3_server_output/`:

    af3_server_output/
        FnCas9_WT_full/
            summary_confidences.json        # top-level metrics
            fold_*_summary_confidences.json # per-ranked-model summaries (if present)
            fold_*_full_data.json           # per-residue confidence (if present)
            fold_*_model_0.cif              # structure ranked 0 (best)
            ...
        FnCas9_PLM5_full/
            (same layout)
        FnCas9_en31_full/
            (same layout)

If AF3 Server changes its output format, run this on a single variant to
inspect the actual files, then adjust the `summary_keys` and `per_chain_keys`
lists below.

Outputs:
  1. A summary table mirroring `boltz_analyze.py` (iPTM, pTM, per-chain pTM, etc.)
  2. A per-engineered-position pLDDT table (parsed from CIF B-factor column)
  3. Side-by-side comparison vs Boltz MSA results (for criterion-1 closure)
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

# Engineered positions (UniProt A0Q5Y3 numbering)
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

# Boltz MSA-Boltz reference values (mean ± σ over 5 samples) for cross-comparison
BOLTZ_REF = {
    "WT":   {"iptm": (0.926, 0.038), "complex_iplddt": (0.908, 0.005), "prot_dna_pam": (0.917, 0.028)},
    "PLM5": {"iptm": (0.951, 0.005), "complex_iplddt": (0.918, 0.001), "prot_dna_pam": (0.937, 0.007)},
    "PLM4": {"iptm": (0.933, 0.027), "complex_iplddt": (0.919, 0.004), "prot_dna_pam": (0.919, 0.025)},
    "en31": {"iptm": (0.940, 0.009), "complex_iplddt": (0.909, 0.002), "prot_dna_pam": (0.927, 0.009)},
    "PLM3": {"iptm": (0.862, 0.076), "complex_iplddt": (0.856, 0.032), "prot_dna_pam": (0.848, 0.068)},
}


def load_summary_json(variant_dir: Path) -> list[dict]:
    """Load any summary_confidences*.json files (multiple if AF3 produced ranked models)."""
    paths = sorted(variant_dir.glob("*summary_confidences*.json"))
    if not paths:
        # Some AF3 dumps name it differently; try permissive
        paths = sorted(variant_dir.glob("*confidences*.json"))
    out = []
    for p in paths:
        try:
            out.append({"_path": str(p.name), **json.loads(p.read_text())})
        except json.JSONDecodeError as e:
            log.warning("  failed to parse %s: %s", p, e)
    return out


def extract_plddt_from_cif(cif_path: Path, protein_chain_id: str = "A") -> dict[int, float]:
    """Parse mmCIF B-factor column (used for per-residue pLDDT in AF3/Boltz outputs).

    Returns dict mapping {residue_seq_id (int) → mean B-factor (per-residue pLDDT)}.
    Only considers atoms on the protein chain.
    """
    plddts: dict[int, list[float]] = {}
    in_atom_block = False
    column_order: list[str] = []
    try:
        for line in cif_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("loop_"):
                column_order = []
                in_atom_block = False
                continue
            if line.startswith("_atom_site."):
                column_order.append(line.split(".", 1)[1])
                continue
            if column_order and not line.startswith("_") and not line.startswith("#"):
                in_atom_block = True
            if line.startswith("#") or line.startswith("loop_") or line.startswith("_"):
                in_atom_block = False
                continue
            if not in_atom_block or not line:
                continue
            fields = line.split()
            if len(fields) < len(column_order):
                continue
            row = dict(zip(column_order, fields))
            # AF3 / Boltz CIFs use auth_asym_id for chain and auth_seq_id for residue
            chain = row.get("auth_asym_id") or row.get("label_asym_id")
            if chain != protein_chain_id:
                continue
            try:
                seq_id = int(row.get("auth_seq_id") or row.get("label_seq_id"))
                b = float(row.get("B_iso_or_equiv", "nan"))
            except (TypeError, ValueError):
                continue
            plddts.setdefault(seq_id, []).append(b)
    except FileNotFoundError:
        log.warning("  CIF not found: %s", cif_path)
        return {}
    return {k: statistics.mean(v) for k, v in plddts.items() if v}


def mean_std(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return (0.0, 0.0)
    if len(xs) == 1:
        return (xs[0], 0.0)
    return (statistics.mean(xs), statistics.stdev(xs))


def summarize_variant(name: str, summaries: list[dict]) -> dict:
    """Aggregate metrics across N ranked models (or single summary)."""
    if not summaries:
        return {}
    out: dict[str, tuple[float, float]] = {}
    # AF3 Server's typical top-level keys (best-effort list; may need adjustment)
    for key in ("iptm", "ptm", "ranking_score", "ranking_confidence",
                "fraction_disordered", "has_clash", "complex_plddt",
                "complex_iplddt"):
        vals = [s[key] for s in summaries if key in s and isinstance(s[key], (int, float))]
        if vals:
            out[key] = mean_std(vals)
    # Per-chain metrics (if present)
    for key in ("chain_iptm", "chain_ptm", "chain_pair_iptm"):
        if not any(key in s for s in summaries):
            continue
        # These are typically arrays — collapse to scalars for the protein chain (index 0)
        protein_vals = []
        for s in summaries:
            v = s.get(key)
            if isinstance(v, list) and v:
                protein_vals.append(v[0] if isinstance(v[0], (int, float)) else None)
        protein_vals = [x for x in protein_vals if x is not None]
        if protein_vals:
            out[f"{key}_protein"] = mean_std(protein_vals)
    return out


def print_summary(summaries: dict[str, dict]) -> None:
    log.info("\n=== AF3 Server confidence summary ===\n")
    if not summaries:
        log.info("(no summaries loaded — check that AF3 Server output JSONs are in place)")
        return
    metrics = sorted({k for s in summaries.values() for k in s.keys()})
    header = f"{'Metric':<30}"
    for name in summaries:
        header += f"  {name:<14}"
    log.info(header)
    log.info("-" * len(header))
    for k in metrics:
        row = f"{k:<30}"
        for name in summaries:
            if k in summaries[name]:
                m, s = summaries[name][k]
                row += f"  {m:.3f}±{s:.3f}  "
            else:
                row += f"  {'n/a':<14}"
        log.info(row)


def print_cross_comparison(af3_summaries: dict[str, dict]) -> None:
    log.info("\n=== AF3 vs Boltz cross-comparison (criterion 1 check) ===\n")
    log.info("Hypothesis: AF3 agrees with Boltz that PLM5 ≈/≥ en31 on iPTM and prot↔DNA-PAM.")
    log.info(f"\n{'Variant':<10} {'AF3 iPTM':<22} {'Boltz iPTM':<22} {'AF3 ≈ Boltz?':<14}")
    log.info("-" * 70)
    for name, af3 in af3_summaries.items():
        # Map our variant labels to Boltz reference names
        short = name.replace("FnCas9_", "").replace("_full", "")
        boltz = BOLTZ_REF.get(short, {}).get("iptm")
        af3_iptm = af3.get("iptm", (0.0, 0.0))
        if boltz and af3_iptm[0] > 0:
            agree = "yes" if abs(af3_iptm[0] - boltz[0]) < 0.05 else "DIVERGE"
            log.info(f"{short:<10} {af3_iptm[0]:.3f} ± {af3_iptm[1]:.3f}     "
                     f"{boltz[0]:.3f} ± {boltz[1]:.3f}     {agree}")
        else:
            log.info(f"{short:<10} {'(not loaded)':<22} {boltz or '(no ref)':<22}")


def print_per_residue_table(variants: dict[str, dict[int, float]]) -> None:
    if not any(variants.values()):
        return
    log.info("\n=== Per-engineered-position pLDDT (from CIF B-factor) ===\n")
    header = f"{'Position':<28}"
    for name in variants:
        header += f"  {name:<12}"
    log.info(header)
    log.info("-" * len(header))
    for label, pos in ENGINEERED_POSITIONS.items():
        row = f"{label:<28}"
        for name, plddts in variants.items():
            val = plddts.get(pos)
            row += f"  {val:.3f}      " if val is not None else f"  {'n/a':<12}"
        log.info(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir",
                        default="data/browser_submissions/af3_server_output",
                        help="Top-level dir containing FnCas9_<variant>_full/ subdirs")
    parser.add_argument("--chain-id", default="A",
                        help="Protein chain ID in the CIF (AF3 typically uses 'A')")
    parser.add_argument("--no-per-residue", action="store_true")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    if not in_dir.exists():
        log.error("No such dir: %s — make sure you've downloaded + unpacked AF3 Server outputs", in_dir)
        return 1

    variant_dirs = sorted([p for p in in_dir.iterdir() if p.is_dir()])
    if not variant_dirs:
        log.error("No variant subdirs found under %s", in_dir)
        return 1

    log.info("Found variant dirs: %s", ", ".join(p.name for p in variant_dirs))

    summaries: dict[str, dict] = {}
    plddts_by_variant: dict[str, dict[int, float]] = {}
    for vdir in variant_dirs:
        log.info("\n[%s]", vdir.name)
        sums = load_summary_json(vdir)
        log.info("  %d summary JSON(s) loaded", len(sums))
        summaries[vdir.name] = summarize_variant(vdir.name, sums)

        if not args.no_per_residue:
            cifs = sorted(vdir.glob("*.cif"))
            if cifs:
                log.info("  parsing CIF: %s", cifs[0].name)
                plddts_by_variant[vdir.name] = extract_plddt_from_cif(cifs[0], args.chain_id)
            else:
                log.info("  no CIF found — skipping per-residue extraction")
                plddts_by_variant[vdir.name] = {}

    print_summary(summaries)
    print_cross_comparison(summaries)
    if not args.no_per_residue:
        print_per_residue_table(plddts_by_variant)

    log.info("\n=== Done. Use this output to draft a new section in notes/plm/verification-log.md. ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
