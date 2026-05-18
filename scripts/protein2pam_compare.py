"""Compare Protein2PAM PWM predictions across WT / PLM4 / PLM5 / en31.

Expected layout (after the user downloads Protein2PAM results into
`data/browser_submissions/protein2pam_output/`):

    protein2pam_output/
        WT.tsv         # PWM as a tab-separated table (rows = positions, cols = ACGT)
        PLM4.tsv
        PLM5.tsv
        en31.tsv

Optional logo PNGs are also expected per variant (e.g. WT_logo.png) — not parsed
here, just referenced.

Outputs:
  - Console: side-by-side PWM comparison + PAM-tolerance metrics
  - PNG: `docs/presentation/figures/protein2pam_comparison.png` — 4-panel sequence logos
  - PWM-derived metrics:
      * H(pos): per-position Shannon entropy in bits (higher = more tolerant)
      * Σ H(NGG positions): cumulative entropy at the canonical NGG positions
      * P(non-NGG): predicted probability mass NOT on NGG
      * Off-NGG support: max prob on NGA / NAG / NCG / NTG / NAA / NAC etc.

Success criterion (closes §6.2 / criterion 2 of the PI gate):
  PLM5 shows broader PAM tolerance (higher Σ H, lower P(NGG-only)) than WT,
  comparable to or exceeding en31.
"""
from __future__ import annotations

import argparse
import csv
import logging
import math
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# Variant order — keep en31 as reference comparator
VARIANT_ORDER = ["WT", "PLM4", "PLM5", "en31"]


def load_pwm(tsv_path: Path) -> list[dict[str, float]]:
    """Load a PWM from TSV.

    Robust to common Protein2PAM export formats:
        position  A  C  G  T          (4-col + position; header)
        A  C  G  T                    (4-col, no position)
        Comma- or tab-separated

    Returns: list of dicts, one per position, with keys A/C/G/T.
    """
    text = tsv_path.read_text().strip()
    if not text:
        return []
    # Auto-detect delimiter
    delim = "\t" if "\t" in text.splitlines()[0] else ","
    rows = list(csv.reader(text.splitlines(), delimiter=delim))
    if not rows:
        return []
    # Find header columns
    header = [c.strip().upper() for c in rows[0]]
    if {"A", "C", "G", "T"}.issubset(set(header)):
        col_a = header.index("A")
        col_c = header.index("C")
        col_g = header.index("G")
        col_t = header.index("T")
        body = rows[1:]
    else:
        # Assume no header, columns are A C G T (with optional leading position col)
        if len(rows[0]) == 5:
            col_a, col_c, col_g, col_t = 1, 2, 3, 4
        else:
            col_a, col_c, col_g, col_t = 0, 1, 2, 3
        body = rows
    pwm = []
    for r in body:
        if len(r) <= max(col_a, col_c, col_g, col_t):
            continue
        try:
            pwm.append({"A": float(r[col_a]), "C": float(r[col_c]),
                        "G": float(r[col_g]), "T": float(r[col_t])})
        except ValueError:
            continue
    # Normalize each row to sum to 1 (PWMs sometimes come as counts or probabilities)
    out = []
    for p in pwm:
        s = sum(p.values())
        if s > 0:
            out.append({k: v / s for k, v in p.items()})
        else:
            out.append(p)
    return out


def entropy_bits(probs: dict[str, float]) -> float:
    """Shannon entropy in bits (max 2 for 4 bases)."""
    h = 0.0
    for p in probs.values():
        if p > 0:
            h -= p * math.log2(p)
    return h


def pam_tolerance_metrics(pwm: list[dict[str, float]]) -> dict[str, float]:
    """Compute summary metrics for a PWM.

    Assumes positions 0..N-1; for typical Cas9 PAM (3 nt = NGG), the canonical
    positions are 1 and 2 (G, G — index 0 is N which is unconstrained).
    """
    if len(pwm) < 3:
        return {}
    metrics: dict[str, float] = {}
    entropies = [entropy_bits(p) for p in pwm]
    metrics["sum_entropy"] = sum(entropies)
    metrics["mean_entropy"] = statistics_mean(entropies)
    # Canonical NGG positions: P(G) at positions 1 and 2 (0-indexed)
    if len(pwm) >= 3:
        metrics["P_pos1_G"] = pwm[1].get("G", 0.0)
        metrics["P_pos2_G"] = pwm[2].get("G", 0.0)
        metrics["P_NGG"] = pwm[1].get("G", 0.0) * pwm[2].get("G", 0.0)
        # Non-NGG support = 1 - P(G at pos1) * P(G at pos2)
        metrics["P_non_NGG"] = 1.0 - metrics["P_NGG"]
    return metrics


def statistics_mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def print_comparison_table(pwms: dict[str, list[dict[str, float]]]) -> None:
    log.info("\n=== Protein2PAM PWM comparison ===\n")
    for v in VARIANT_ORDER:
        if v not in pwms:
            continue
        pwm = pwms[v]
        log.info(f"[{v}]  ({len(pwm)} positions)")
        log.info(f"  {'pos':<5} {'A':>8} {'C':>8} {'G':>8} {'T':>8}   {'H (bits)':>10}")
        for i, p in enumerate(pwm):
            log.info(f"  {i:<5} {p.get('A', 0):.4f}   {p.get('C', 0):.4f}   "
                     f"{p.get('G', 0):.4f}   {p.get('T', 0):.4f}     "
                     f"{entropy_bits(p):.3f}")
        log.info("")


def print_metrics_table(pwms: dict[str, list[dict[str, float]]]) -> None:
    log.info("\n=== PAM-tolerance summary ===\n")
    metrics_per_v = {v: pam_tolerance_metrics(pwms[v]) for v in pwms}
    if not metrics_per_v:
        return
    header = f"{'Metric':<22}"
    for v in VARIANT_ORDER:
        if v in metrics_per_v:
            header += f"  {v:<10}"
    log.info(header)
    log.info("-" * len(header))
    metric_names = ["sum_entropy", "mean_entropy", "P_pos1_G", "P_pos2_G",
                    "P_NGG", "P_non_NGG"]
    interp = {
        "sum_entropy": "(higher = more tolerant overall)",
        "mean_entropy": "(higher = more tolerant per position)",
        "P_pos1_G": "(NGG canonical position 1)",
        "P_pos2_G": "(NGG canonical position 2)",
        "P_NGG": "(prob of canonical NGG)",
        "P_non_NGG": "(broader = more tolerant)",
    }
    for k in metric_names:
        row = f"{k:<22}"
        for v in VARIANT_ORDER:
            if v in metrics_per_v and k in metrics_per_v[v]:
                row += f"  {metrics_per_v[v][k]:<10.4f}"
        row += f"  {interp[k]}"
        log.info(row)


def make_logo_figure(pwms: dict[str, list[dict[str, float]]], out_path: Path) -> None:
    """4-panel sequence logos — best-effort with matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        log.warning("matplotlib not available — skipping logo figure")
        return

    variants = [v for v in VARIANT_ORDER if v in pwms]
    if not variants:
        return
    n_pos = max(len(pwms[v]) for v in variants)
    base_colors = {"A": "#2E8B57", "C": "#2E5CB8", "G": "#E67E22", "T": "#C0392B"}

    fig, axes = plt.subplots(len(variants), 1, figsize=(max(8, n_pos * 0.6), 2.4 * len(variants)),
                             dpi=160, sharex=True)
    if len(variants) == 1:
        axes = [axes]
    for ax, v in zip(axes, variants):
        pwm = pwms[v]
        for i, p in enumerate(pwm):
            # Bit-height logo: each base's height = p * (2 - H)
            h_pos = entropy_bits(p)
            content = max(0.0, 2.0 - h_pos)
            sorted_bases = sorted(p.items(), key=lambda kv: -kv[1])
            y_cursor = 0.0
            for base, prob in sorted_bases:
                if prob <= 0:
                    continue
                h = prob * content
                ax.text(i, y_cursor + h / 2, base,
                        ha="center", va="center", fontsize=14 + min(8, int(h * 12)),
                        fontweight="bold", color=base_colors.get(base, "black"))
                y_cursor += h
        ax.set_xlim(-0.5, n_pos - 0.5)
        ax.set_ylim(0, 2.05)
        ax.set_ylabel(f"{v}\nbits", fontsize=10)
        ax.set_xticks(range(n_pos))
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)
    axes[-1].set_xlabel("PAM position (0-indexed)", fontsize=10)
    fig.suptitle("Protein2PAM predicted PAM specificity — taller letters = more constrained\n"
                 "Wider/shorter logos = more PAM tolerance (the engineered property of en31)",
                 fontsize=12, fontweight="bold", y=1.005)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir",
                        default="data/browser_submissions/protein2pam_output",
                        help="Dir containing <variant>.tsv PWM files")
    parser.add_argument("--out-figure",
                        default="docs/presentation/figures/protein2pam_comparison.png")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    if not in_dir.exists():
        log.error("No such dir: %s — paste/save your Protein2PAM PWM exports there first", in_dir)
        return 1

    pwms: dict[str, list[dict[str, float]]] = {}
    for v in VARIANT_ORDER:
        for ext in (".tsv", ".csv", ".txt"):
            p = in_dir / f"{v}{ext}"
            if p.exists():
                pwm = load_pwm(p)
                if pwm:
                    pwms[v] = pwm
                    log.info("loaded %s (%d positions)", p, len(pwm))
                    break
        if v not in pwms:
            log.warning("no PWM file found for %s in %s (expected %s.tsv/.csv/.txt)",
                        v, in_dir, v)

    if not pwms:
        log.error("No PWMs loaded. Save Protein2PAM exports first.")
        return 1

    print_comparison_table(pwms)
    print_metrics_table(pwms)
    make_logo_figure(pwms, Path(args.out_figure))

    log.info("\n=== Done. Use the metrics table + logo figure to draft the §2.4 section ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
