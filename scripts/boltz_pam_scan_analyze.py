"""Analyze the Boltz-2 PAM-variant scan results (§2.4 Reading B).

Reads the 15 non-NGG outputs from results/runs/<date>_boltz_pam_scan/
and the 3 NGG control outputs from results/runs/2026-05-15_boltz_complex/.
Produces:

  1. A 3-variant × 6-PAM table of iPTM (prot↔DNA-PAM) values.
  2. Per-variant "PAM tolerance" metrics:
       Δ_iPTM(PAM) = iPTM(variant, PAM) - iPTM(variant, NGG)
       Tolerance score = mean(Δ_iPTM over non-NGG PAMs)
       Negative Δ = PAM is worse than NGG; small |Δ| = tolerated.
  3. A heatmap figure for the deck (3 variants × 6 PAMs).
  4. The core comparison: does PLM5 tolerate non-NGG PAMs better than WT does?
     If mean Δ_iPTM(PLM5, non-NGG) > mean Δ_iPTM(WT, non-NGG), criterion 2 ✅.
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

PAMS = ["NGG", "NGA", "NAG", "NCG", "NTG", "NAA"]
VARIANTS = ["wt", "plm5", "en31"]
NICE = {"wt": "WT", "plm5": "PLM5", "en31": "en31"}

CHAIN_PROT = "0"
CHAIN_RNA = "1"
CHAIN_DNA_TARGET = "2"
CHAIN_DNA_PAM = "3"


def mean_std(xs):
    if not xs:
        return (0.0, 0.0)
    if len(xs) == 1:
        return (xs[0], 0.0)
    return (statistics.mean(xs), statistics.stdev(xs))


def load_confidence_jsons(variant_dir: Path):
    pred_dirs = list(variant_dir.glob("boltz_results_*/predictions/boltz_*/"))
    if not pred_dirs:
        return []
    return [json.loads(p.read_text())
            for p in sorted(pred_dirs[0].glob("confidence_*.json"))]


def variant_summary(samples):
    out = {}
    for key in ("iptm", "ptm", "complex_iplddt"):
        vals = [s[key] for s in samples if key in s]
        if vals:
            out[key] = mean_std(vals)
    for label, c1, c2 in [
        ("prot_dna_target", CHAIN_PROT, CHAIN_DNA_TARGET),
        ("prot_dna_pam",    CHAIN_PROT, CHAIN_DNA_PAM),
        ("prot_rna",        CHAIN_PROT, CHAIN_RNA),
    ]:
        vals = [s.get("pair_chains_iptm", {}).get(c1, {}).get(c2) for s in samples]
        vals = [v for v in vals if v is not None]
        if vals:
            out[label] = mean_std(vals)
    return out


def collect(scan_dir: Path, ngg_dir: Path):
    """Build a {variant: {PAM: metrics_dict}} table."""
    data = {}
    for v in VARIANTS:
        data[v] = {}
        # NGG control from the apples-to-apples MSA-Boltz run
        ngg_path = ngg_dir / f"fncas9_{v}"
        if ngg_path.exists():
            samples = load_confidence_jsons(ngg_path)
            if samples:
                data[v]["NGG"] = variant_summary(samples)
                log.info("  %s NGG: %d samples", v, len(samples))
            else:
                log.warning("  %s NGG: no confidence JSONs found", v)
        else:
            log.warning("  %s NGG dir missing: %s", v, ngg_path)
        # Non-NGG PAMs from the scan
        for pam in PAMS:
            if pam == "NGG":
                continue
            p = scan_dir / f"fncas9_{v}_pam_{pam}"
            if p.exists():
                samples = load_confidence_jsons(p)
                if samples:
                    data[v][pam] = variant_summary(samples)
                    log.info("  %s %s: %d samples", v, pam, len(samples))
    return data


def print_table(data, metric="prot_dna_pam"):
    log.info("\n=== iPTM(protein↔DNA-PAM) table (mean ± σ over 5 diffusion samples) ===\n")
    header = f"{'Variant':<8}"
    for p in PAMS:
        header += f"  {p:<14}"
    log.info(header)
    log.info("-" * len(header))
    for v in VARIANTS:
        row = f"{NICE[v]:<8}"
        for p in PAMS:
            val = data[v].get(p, {}).get(metric)
            if val is None:
                row += f"  {'n/a':<14}"
            else:
                m, s = val
                row += f"  {m:.3f}±{s:.3f} "
        log.info(row)


def tolerance_metrics(data, metric="prot_dna_pam"):
    log.info("\n=== PAM tolerance metrics (Δ_iPTM relative to NGG) ===\n")
    log.info("Δ_iPTM(PAM) = mean iPTM(variant, PAM) - mean iPTM(variant, NGG)")
    log.info("Negative Δ = PAM is worse than NGG for this variant.")
    log.info("A candidate that tolerates non-NGG PAMs has Δ closer to 0 (less drop).")
    log.info("")
    header = f"{'Variant':<8}  {'NGG (anchor)':<14}"
    for p in PAMS[1:]:
        header += f"  Δ_{p:<6}"
    header += f"  {'mean Δ (5 non-NGG)':<20}"
    log.info(header)
    log.info("-" * len(header))
    results = {}
    for v in VARIANTS:
        ngg = data[v].get("NGG", {}).get(metric)
        if ngg is None:
            continue
        ngg_m = ngg[0]
        row = f"{NICE[v]:<8}  {ngg_m:.3f}         "
        deltas = []
        for p in PAMS[1:]:
            val = data[v].get(p, {}).get(metric)
            if val is None:
                row += f"  {'n/a':<8}"
                continue
            d = val[0] - ngg_m
            row += f"  {d:+.3f} "
            deltas.append(d)
        if deltas:
            mean_d = statistics.mean(deltas)
            row += f"  {mean_d:+.3f}"
            results[v] = (ngg_m, mean_d, deltas)
        log.info(row)
    return results


def closure_verdict(results):
    log.info("\n=== Criterion 2 closure check ===\n")
    if "wt" not in results or "plm5" not in results:
        log.warning("Missing WT or PLM5 — cannot evaluate criterion.")
        return
    wt_mean_d = results["wt"][1]
    plm5_mean_d = results["plm5"][1]
    en31_mean_d = results.get("en31", (None, None, None))[1]

    log.info(f"WT  mean Δ_iPTM (5 non-NGG PAMs): {wt_mean_d:+.4f}")
    log.info(f"PLM5 mean Δ_iPTM (5 non-NGG PAMs): {plm5_mean_d:+.4f}")
    if en31_mean_d is not None:
        log.info(f"en31 mean Δ_iPTM (5 non-NGG PAMs): {en31_mean_d:+.4f}")
    log.info("")
    log.info("Headline question: does PLM5 tolerate non-NGG PAMs better than WT?")
    if plm5_mean_d > wt_mean_d:
        log.info(f"  YES — PLM5 Δ ({plm5_mean_d:+.4f}) > WT Δ ({wt_mean_d:+.4f}).")
        log.info(f"  Margin: {plm5_mean_d - wt_mean_d:+.4f} iPTM units.")
        log.info("  This is positive structural evidence of PAM relaxation.")
        log.info("  → criterion 2 = ✅ subject to interpretation of the margin.")
    elif abs(plm5_mean_d - wt_mean_d) < 0.005:
        log.info(f"  EFFECTIVELY EQUAL — PLM5 Δ ({plm5_mean_d:+.4f}) ≈ WT Δ ({wt_mean_d:+.4f}).")
        log.info("  No structural-prediction signal of PAM relaxation.")
        log.info("  → criterion 2 = ✅ only under Reading A (Protein2PAM caveat).")
    else:
        log.info(f"  NO — PLM5 Δ ({plm5_mean_d:+.4f}) < WT Δ ({wt_mean_d:+.4f}).")
        log.info(f"  Margin: {plm5_mean_d - wt_mean_d:+.4f} iPTM units.")
        log.info("  PLM5 tolerates non-NGG PAMs LESS well than WT in Boltz.")
        log.info("  → criterion 2 NOT met by this test. Flag for review.")

    if en31_mean_d is not None:
        log.info("")
        log.info(f"Calibration check (en31 is wet-lab-validated PAM-relaxed):")
        if en31_mean_d > wt_mean_d:
            log.info(f"  en31 Δ ({en31_mean_d:+.4f}) > WT Δ ({wt_mean_d:+.4f}) — "
                     "Boltz sees en31's PAM relaxation. Method is calibrated.")
        else:
            log.info(f"  en31 Δ ({en31_mean_d:+.4f}) ≤ WT Δ ({wt_mean_d:+.4f}) — "
                     "Boltz does NOT see en31's known PAM relaxation. "
                     "Method-resolution limit (similar to Protein2PAM); the test is uninformative.")


def make_heatmap(data, metric, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return
    M = np.full((len(VARIANTS), len(PAMS)), np.nan)
    for i, v in enumerate(VARIANTS):
        for j, p in enumerate(PAMS):
            val = data[v].get(p, {}).get(metric)
            if val is not None:
                M[i, j] = val[0]
    fig, ax = plt.subplots(figsize=(10, 4), dpi=160)
    im = ax.imshow(M, cmap="viridis", vmin=0.80, vmax=0.96, aspect="auto")
    ax.set_xticks(range(len(PAMS)))
    ax.set_xticklabels(PAMS)
    ax.set_yticks(range(len(VARIANTS)))
    ax.set_yticklabels([NICE[v] for v in VARIANTS])
    for i in range(len(VARIANTS)):
        for j in range(len(PAMS)):
            val = M[i, j]
            if not np.isnan(val):
                color = "white" if val < 0.88 else "black"
                ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                        fontsize=10, color=color, fontweight="bold")
    plt.colorbar(im, ax=ax, label=f"iPTM ({metric})")
    ax.set_title("Boltz-2 PAM-variant scan — protein↔DNA-PAM iPTM\n"
                 "(higher = better PAM-interface confidence; NGG is the canonical PAM)",
                 fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-dir", required=True,
                        help="Top-level dir of the PAM scan, e.g. "
                             "results/runs/2026-05-18_boltz_pam_scan")
    parser.add_argument("--ngg-dir",
                        default="results/runs/2026-05-15_boltz_complex",
                        help="Dir containing the NGG control runs (the original MSA-Boltz set)")
    parser.add_argument("--metric", default="prot_dna_pam",
                        help="Which metric to compare: prot_dna_pam (default), iptm, complex_iplddt")
    parser.add_argument("--out-figure",
                        default="docs/presentation/figures/pam_scan_heatmap.png")
    args = parser.parse_args()

    scan_dir = Path(args.scan_dir)
    ngg_dir = Path(args.ngg_dir)
    if not scan_dir.exists():
        log.error("Scan dir missing: %s", scan_dir)
        return 1

    log.info("Collecting scan results from %s", scan_dir)
    log.info("Collecting NGG control runs from %s", ngg_dir)
    data = collect(scan_dir, ngg_dir)

    print_table(data, metric=args.metric)
    results = tolerance_metrics(data, metric=args.metric)
    closure_verdict(results)
    make_heatmap(data, args.metric, Path(args.out_figure))
    return 0


if __name__ == "__main__":
    sys.exit(main())
