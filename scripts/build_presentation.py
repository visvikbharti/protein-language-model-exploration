"""Build a comprehensive PowerPoint presentation summarizing the FnCas9 PLM
redesign campaign.

Outputs:
  docs/presentation/figures/*.png   — matplotlib figures used in slides
  docs/presentation/FnCas9_PLM_Redesign.pptx — the deck

The deck is regeneratable: rerun this script after any data/text update.
"""
from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "presentation"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Visual style
ANTHRO_NAVY = RGBColor(0x1F, 0x2A, 0x4C)
ANTHRO_BLUE = RGBColor(0x2E, 0x5C, 0xB8)
ANTHRO_GREEN = RGBColor(0x2E, 0x8B, 0x57)
ANTHRO_RED = RGBColor(0xC0, 0x39, 0x2B)
LIGHT_GREY = RGBColor(0xE6, 0xE6, 0xE6)
DARK_GREY = RGBColor(0x4A, 0x4A, 0x4A)

# Matplotlib palette
COLOR_WT = "#4A4A4A"
COLOR_PLM3 = "#C0392B"
COLOR_PLM4 = "#E67E22"   # amber (added for robustness phase)
COLOR_PLM5 = "#2E8B57"
COLOR_EN31 = "#2E5CB8"

VARIANT_COLORS = {
    "WT": COLOR_WT, "PLM3": COLOR_PLM3, "PLM4": COLOR_PLM4,
    "PLM5": COLOR_PLM5, "en31": COLOR_EN31,
}


def fig_confidence_bars() -> Path:
    """Bar chart: Boltz confidence metrics across WT / PLM3 / PLM5 / en31."""
    metrics = [
        ("Overall\nconfidence",   {"WT":0.915,"PLM3":0.865,"PLM5":0.918,"en31":0.919}, {"WT":0.003,"PLM3":0.044,"PLM5":0.010,"en31":0.003}),
        ("Mean per-res\npLDDT",   {"WT":0.908,"PLM3":0.862,"PLM5":0.913,"en31":0.913}, {"WT":0.003,"PLM3":0.032,"PLM5":0.004,"en31":0.002}),
        ("iPTM\n(all interfaces)",{"WT":0.944,"PLM3":0.880,"PLM5":0.935,"en31":0.946}, {"WT":0.008,"PLM3":0.094,"PLM5":0.037,"en31":0.007}),
        ("iPTM\nprotein↔DNA-PAM", {"WT":0.939,"PLM3":0.901,"PLM5":0.933,"en31":0.942}, {"WT":0.008,"PLM3":0.056,"PLM5":0.025,"en31":0.008}),
        ("iPTM\nprotein↔sgRNA",   {"WT":0.947,"PLM3":0.866,"PLM5":0.937,"en31":0.949}, {"WT":0.008,"PLM3":0.117,"PLM5":0.037,"en31":0.007}),
    ]
    variants = ["WT", "PLM3", "PLM5", "en31"]
    colors = {"WT": COLOR_WT, "PLM3": COLOR_PLM3, "PLM5": COLOR_PLM5, "en31": COLOR_EN31}

    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=160)
    x = np.arange(len(metrics))
    width = 0.20

    for i, v in enumerate(variants):
        means = [m[1][v] for m in metrics]
        stds = [m[2][v] for m in metrics]
        ax.bar(x + (i - 1.5) * width, means, width, yerr=stds, label=v,
               color=colors[v], capsize=3, edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([m[0] for m in metrics], fontsize=10)
    ax.set_ylim(0.70, 1.00)
    ax.set_ylabel("Confidence score (higher = better)", fontsize=11)
    ax.set_title("Boltz-2 complex prediction confidence — WT vs PLM3 vs PLM5 vs en31\n"
                 "(mean ± std over 5 diffusion samples; truncated WED+PI, residues 1230-1620)",
                 fontsize=11, pad=12)
    ax.axhline(0.85, color="grey", linestyle="--", linewidth=0.6, alpha=0.5)
    ax.text(len(metrics) - 0.3, 0.853, "high-confidence threshold (0.85)",
            fontsize=8, color="grey", ha="right", va="bottom")
    ax.legend(loc="lower right", ncols=4, fontsize=10, frameon=True)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()

    path = FIG_DIR / "boltz_confidence_bars.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_per_residue_plddt() -> Path:
    """Per-engineered-position pLDDT — grouped bars per position, one bar per variant."""
    rows = [
        ("G1243T",   {"WT":0.936,"PLM3":0.816,"PLM5":0.939,"en31":0.938}, ["en31","PLM3"]),
        ("Y1249F",   {"WT":0.965,"PLM3":0.914,"PLM5":0.969,"en31":0.967}, ["PLM5"]),
        ("C1292K",   {"WT":0.937,"PLM3":0.883,"PLM5":0.938,"en31":0.933}, ["PLM3"]),
        ("A1325K",   {"WT":0.885,"PLM3":0.852,"PLM5":0.900,"en31":0.899}, ["PLM5"]),
        ("Y1341L",   {"WT":0.966,"PLM3":0.904,"PLM5":0.968,"en31":0.970}, ["PLM5"]),
        ("E1369R",   {"WT":0.962,"PLM3":0.891,"PLM5":0.963,"en31":0.954}, ["en31"]),
        ("E1449H",   {"WT":0.952,"PLM3":0.867,"PLM5":0.952,"en31":0.955}, ["en31"]),
        ("K1479F",   {"WT":0.914,"PLM3":0.844,"PLM5":0.925,"en31":0.913}, ["PLM5"]),
        ("W1507K",   {"WT":0.958,"PLM3":0.878,"PLM5":0.966,"en31":0.964}, ["PLM3"]),
        ("T1535V",   {"WT":0.961,"PLM3":0.955,"PLM5":0.966,"en31":0.964}, []),
        ("E1603H",   {"WT":0.934,"PLM3":0.918,"PLM5":0.947,"en31":0.942}, []),
        ("M1617K",   {"WT":0.908,"PLM3":0.923,"PLM5":0.922,"en31":0.921}, ["PLM3"]),
    ]
    variants = ["WT", "PLM3", "PLM5", "en31"]
    colors = {"WT": COLOR_WT, "PLM3": COLOR_PLM3, "PLM5": COLOR_PLM5, "en31": COLOR_EN31}

    fig, ax = plt.subplots(figsize=(13, 5.5), dpi=160)
    x = np.arange(len(rows))
    width = 0.20

    for i, v in enumerate(variants):
        vals = [r[1][v] for r in rows]
        ax.bar(x + (i - 1.5) * width, vals, width, label=v, color=colors[v],
               edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], rotation=30, ha="right", fontsize=10)
    ax.set_ylim(0.78, 1.00)
    ax.set_ylabel("Per-residue pLDDT (mean of 5 samples)", fontsize=11)
    ax.set_title("Per-engineered-position confidence — same mutation, different contexts\n"
                 "(positions labeled by their canonical mutation; pLDDT measured at that residue)",
                 fontsize=11, pad=12)
    ax.axhline(0.90, color="grey", linestyle="--", linewidth=0.6, alpha=0.5)
    ax.legend(loc="lower right", ncols=4, fontsize=10, frameon=True)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()

    path = FIG_DIR / "per_residue_plddt.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_esm_vs_ligandmpnn_head_to_head() -> Path:
    """The key scientific figure: ESM-2 vs LigandMPNN at the four en31/en15 positions."""
    positions = ["G1243T\n(en31, WED)", "E1369R\n(en31, PI)", "E1449H\n(en31, PI)", "E1603H\n(en15, PI)"]

    # ESM-2 rank (lower = better, out of 7429)
    esm2_ranks = [1, 4956, 5117, 5109]
    # Normalize to 0-1 scale (1 = top, 0 = bottom)
    esm2_score = [1 - (r - 1) / 7428 for r in esm2_ranks]

    # LigandMPNN target-mutation pooled frequency
    lig_target_freq = [0.455, 0.365, 0.000, 0.000]
    # LigandMPNN top-non-WT pick frequency (irrespective of whether it matches target)
    lig_top_nonwt = [0.456, 0.522, 0.985, 0.517]
    lig_top_label = ["S", "K", "L", "L"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=160)

    # LEFT: ESM-2 rank
    ax = axes[0]
    bars = ax.bar(positions, esm2_score, color=[COLOR_PLM5 if r == 1 else COLOR_PLM3 for r in esm2_ranks],
                  edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Composite rank in 7,429-variant pool\n(1.0 = top, 0.0 = bottom)", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.6, alpha=0.5)
    ax.text(3.4, 0.51, "median", fontsize=8, color="grey", ha="right", va="bottom")
    ax.set_title("ESM-2 (sequence-only) ranks of en31/en15 mutations",
                 fontsize=11, pad=8)
    for i, (b, r) in enumerate(zip(bars, esm2_ranks)):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.02,
                f"rank {r}", ha="center", fontsize=9)

    # RIGHT: LigandMPNN frequencies
    ax = axes[1]
    width = 0.35
    x = np.arange(len(positions))
    b1 = ax.bar(x - width/2, lig_target_freq, width, label="target mutation freq",
                color=COLOR_EN31, edgecolor="black", linewidth=0.5)
    b2 = ax.bar(x + width/2, lig_top_nonwt, width, label="top non-WT pick freq",
                color=COLOR_PLM5, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(positions, fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Pooled sample frequency (T = 0.1, 0.2, 0.3)", fontsize=10)
    ax.set_title("LigandMPNN (structure + ligand) pooled posterior",
                 fontsize=11, pad=8)
    ax.legend(loc="upper right", fontsize=9)
    for i, (b, lbl) in enumerate(zip(b2, lig_top_label)):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.02,
                lbl, ha="center", fontsize=10, fontweight="bold")

    plt.suptitle("Head-to-head: sequence-only ESM-2 vs structure-and-ligand LigandMPNN at the en31/en15 reference positions",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = FIG_DIR / "esm_vs_ligandmpnn.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_ddg_calibration() -> Path:
    """Cumulative apo ΔΔG: candidates vs en31/en15 envelope."""
    candidates = ["en31", "en15", "PLM3", "PLM4", "PLM5"]
    ddg = [0.40, -1.37, -8.42, 6.74, 0.59]
    colors = [COLOR_EN31, COLOR_EN31, COLOR_PLM3, COLOR_PLM3, COLOR_PLM5]
    descriptions = ["(known\nfunctional)", "(known\nfunctional)", "(ESM-2)", "(LigandMPNN,\nno gate)", "(LigandMPNN\n+ ΔΔG gate)"]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=160)
    bars = ax.bar(candidates, ddg, color=colors, edgecolor="black", linewidth=0.5)

    # Envelope band [-1.4, +0.4]
    ax.axhspan(-1.4, 0.4, color=COLOR_EN31, alpha=0.12,
               label="known-functional envelope (en31 / en15)")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(3.2, color="grey", linestyle="--", linewidth=0.6, alpha=0.6)
    ax.text(len(candidates) - 0.3, 3.3, "single-position +3.2 ceiling (en31's E1369R)",
            fontsize=8, color="grey", ha="right", va="bottom")

    for i, (b, val, desc) in enumerate(zip(bars, ddg, descriptions)):
        y_off = 0.4 if val > 0 else -0.4
        ax.text(b.get_x() + b.get_width()/2, val + y_off,
                f"{val:+.2f}", ha="center", fontsize=10, fontweight="bold")
        ax.text(b.get_x() + b.get_width()/2, -10.5, desc,
                ha="center", fontsize=8, color="dimgrey")

    ax.set_ylabel("Cumulative apo ΔΔG (kcal/mol; > 0 destabilizing)", fontsize=11)
    ax.set_ylim(-10, 8)
    ax.set_title("Cumulative apo-state ΔΔG vs the en31 calibration envelope\n"
                 "(proteinmpnn_ddg saturation prediction)", fontsize=11, pad=10)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()
    path = FIG_DIR / "ddg_calibration.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_structural_3d() -> Path:
    """3D Cα trace of WED+PI domain on 5B2O with candidate mutation positions
    color-coded by variant. Two panels: en31 cluster (left) vs PLM5 spread (right).

    Direct visual complement to fig_thermompnn_epistasis's quantitative view.
    """
    import biotite.structure.io.pdb as pdb_io

    pdb_path = ROOT / "data" / "raw" / "5B2O.pdb"
    pdb = pdb_io.PDBFile.read(str(pdb_path))
    s = pdb.get_structure(model=1)

    ca_mask = (s.chain_id == "A") & (s.atom_name == "CA") & \
              (s.res_id >= 1230) & (s.res_id <= 1620)
    ca = s[ca_mask]
    rna = s[(s.chain_id == "B") & (s.atom_name == "C1'")]
    dnaC = s[(s.chain_id == "C") & (s.atom_name == "C1'")]
    dnaD = s[(s.chain_id == "D") & (s.atom_name == "C1'")]
    coord_by_id = {int(r): c for r, c in zip(ca.res_id, ca.coord)}

    all_positions = [
        (1243, "G", "T", "shared"),
        (1249, "Y", "F", "plm5"),
        (1292, "C", "K", "plm3"),
        (1325, "A", "K", "plm5"),
        (1341, "Y", "L", "plm5"),
        (1369, "E", "R", "en31"),
        (1449, "E", "H", "en31"),
        (1479, "K", "F", "plm5"),
        (1507, "W", "K", "plm3"),
        (1535, "T", "V", "plm4"),
        (1603, "E", "H", "en15"),
        (1617, "M", "K", "plm3"),
    ]
    en31_positions = [1243, 1369, 1449]
    plm5_positions = [1249, 1325, 1341, 1479]
    color_for = {
        "en31":   COLOR_EN31,
        "shared": COLOR_EN31,   # G1243T is in both en31 and PLM3 — color as en31
        "plm5":   COLOR_PLM5,
        "plm4":   COLOR_PLM4,
        "plm3":   COLOR_PLM3,
        "en15":   "#8E44AD",
    }

    fig = plt.figure(figsize=(17, 8.5), dpi=160)

    def draw_panel(ax, title, highlight_set, view=(18, -60)):
        # Protein backbone
        ax.plot(ca.coord[:, 0], ca.coord[:, 1], ca.coord[:, 2],
                color="#888", linewidth=1.1, alpha=0.6)
        # Nucleic acids
        if len(rna) > 0:
            ax.plot(rna.coord[:, 0], rna.coord[:, 1], rna.coord[:, 2],
                    color="#A0A0A0", linewidth=0.9, alpha=0.45, linestyle="--")
        if len(dnaC) > 0:
            ax.plot(dnaC.coord[:, 0], dnaC.coord[:, 1], dnaC.coord[:, 2],
                    color="#C49A6C", linewidth=1.0, alpha=0.55)
        if len(dnaD) > 0:
            ax.plot(dnaD.coord[:, 0], dnaD.coord[:, 1], dnaD.coord[:, 2],
                    color="#E08D8D", linewidth=1.8, alpha=0.85)
        # Mutation positions — emphasize highlight_set, dim others
        for pos, wt, mut, variant in all_positions:
            if pos not in coord_by_id:
                continue
            c = coord_by_id[pos]
            is_hi = pos in highlight_set
            color = color_for[variant] if is_hi else "#D0D0D0"
            edge = "black" if is_hi else "#888"
            size = 220 if is_hi else 60
            lw = 1.2 if is_hi else 0.5
            ax.scatter(c[0], c[1], c[2], s=size, c=[color], edgecolors=edge,
                       linewidths=lw, depthshade=True, zorder=10)
            if is_hi:
                ax.text(c[0] + 1.8, c[1] + 1.8, c[2] + 1.8,
                        f"{wt}{pos}{mut}", fontsize=10, fontweight="bold",
                        color="#111", zorder=20,
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                                  edgecolor="#666", alpha=0.85, linewidth=0.5))
        # Equal axes
        all_coords = ca.coord
        if len(rna) > 0:  all_coords = np.vstack([all_coords, rna.coord])
        if len(dnaC) > 0: all_coords = np.vstack([all_coords, dnaC.coord])
        if len(dnaD) > 0: all_coords = np.vstack([all_coords, dnaD.coord])
        mins = all_coords.min(axis=0); maxs = all_coords.max(axis=0)
        centers = (mins + maxs) / 2
        half = (maxs - mins).max() / 2
        ax.set_xlim(centers[0] - half, centers[0] + half)
        ax.set_ylim(centers[1] - half, centers[1] + half)
        ax.set_zlim(centers[2] - half, centers[2] + half)
        ax.set_xlabel("X (Å)", fontsize=8); ax.set_ylabel("Y (Å)", fontsize=8)
        ax.set_zlabel("Z (Å)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.view_init(elev=view[0], azim=view[1])
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

    # LEFT panel — en31 clustered
    ax_l = fig.add_subplot(121, projection="3d")
    draw_panel(ax_l,
               "en31 (Acharya 2024) — 3 positions cluster, all CA-CA 8.5-9 Å",
               set(en31_positions), view=(15, -55))

    # RIGHT panel — PLM5 distributed
    ax_r = fig.add_subplot(122, projection="3d")
    draw_panel(ax_r,
               "PLM5 (recommended) — 4 positions spread, CA-CA 14-50 Å",
               set(plm5_positions), view=(15, -55))

    # Legend across the whole figure
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color="#888", linewidth=1.2, label="Protein Cα (WED+PI)"),
        Line2D([0], [0], color="#E08D8D", linewidth=2, label="DNA PAM strand"),
        Line2D([0], [0], color="#C49A6C", linewidth=1.2, label="DNA target strand"),
        Line2D([0], [0], color="#A0A0A0", linewidth=1, linestyle="--", label="sgRNA"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_EN31,
               markersize=10, markeredgecolor="black", label="en31 position"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_PLM5,
               markersize=10, markeredgecolor="black", label="PLM5 position"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#D0D0D0",
               markersize=6, markeredgecolor="#888", label="other candidate position (dimmed)"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=7, fontsize=10,
               frameon=True, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("Mutation positions on PDB 5B2O — en31 clustered vs PLM5 distributed geometry",
                 fontsize=14, fontweight="bold", y=1.00)
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "structural_3d.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_plddt_line_plot() -> Path:
    """Per-residue pLDDT trace across WED+PI domain for WT, PLM5, PLM4, en31.

    Averaged over 5 MSA-Boltz diffusion samples per variant. Mutation
    positions marked with vertical lines. Shows PLM5 matches WT/en31
    everywhere — no localized confidence drops at the engineered sites.
    """
    BASE = ROOT / "results/runs/2026-05-15_boltz_complex"
    BASE4 = ROOT / "results/runs/2026-05-15_boltz_plm4"
    PROT_LEN = 391   # WED+PI window 1230-1620

    def load_mean_plddt(variant_dir, slug):
        """Mean per-residue pLDDT across 5 diffusion samples for protein chain."""
        pred_dir = variant_dir / f"boltz_results_boltz_{slug}/predictions/boltz_{slug}"
        files = sorted(pred_dir.glob(f"plddt_boltz_{slug}_model_*.npz"))
        if not files:
            log.warning("no pLDDT files for %s", slug)
            return None
        stacked = np.stack([np.load(f)["plddt"][:PROT_LEN] for f in files])
        return stacked.mean(axis=0), stacked.std(axis=0)

    sources = [
        ("WT",   BASE / "fncas9_wt",   "fncas9_wt",   COLOR_WT),
        ("PLM4", BASE4 / "fncas9_plm4", "fncas9_plm4", COLOR_PLM4),
        ("PLM5", BASE / "fncas9_plm5", "fncas9_plm5", COLOR_PLM5),
        ("en31", BASE / "fncas9_en31", "fncas9_en31", COLOR_EN31),
    ]
    series = []
    for name, vdir, slug, color in sources:
        loaded = load_mean_plddt(vdir, slug)
        if loaded is None:
            continue
        mean, std = loaded
        series.append((name, mean, std, color))

    if not series:
        log.error("no pLDDT data found — skipping fig_plddt_line_plot")
        return FIG_DIR / "plddt_line_plot.png"

    fig, ax = plt.subplots(figsize=(15, 5.5), dpi=160)
    residue_ids = np.arange(1230, 1230 + PROT_LEN)

    for name, mean, std, color in series:
        ax.fill_between(residue_ids, mean - std, mean + std,
                        color=color, alpha=0.15)
        ax.plot(residue_ids, mean, color=color, linewidth=1.4,
                label=name, alpha=0.95)

    # Mutation position markers
    mutations = [
        (1243, "G1243T",  "en31/PLM3"),
        (1249, "Y1249F",  "PLM4/5"),
        (1292, "C1292K",  "PLM3"),
        (1325, "A1325K",  "PLM4/5"),
        (1341, "Y1341L",  "PLM4/5"),
        (1369, "E1369R",  "en31"),
        (1449, "E1449H",  "en31"),
        (1479, "K1479F",  "PLM5"),
        (1507, "W1507K",  "PLM3"),
        (1535, "T1535V",  "PLM4"),
        (1603, "E1603H",  "en15"),
        (1617, "M1617K",  "PLM3"),
    ]
    for pos, label, source in mutations:
        ax.axvline(pos, color="#888", linewidth=0.5, alpha=0.4, linestyle=":")
        # Label at top
        ax.text(pos, 1.005, label, rotation=90, fontsize=7,
                ha="center", va="bottom", color="#444")

    ax.axhline(0.90, color="grey", linestyle="--", linewidth=0.5, alpha=0.4)
    ax.text(1232, 0.905, "pLDDT 0.90 (high-confidence floor)",
            fontsize=8, color="grey")

    ax.set_xlabel("Residue position (UniProt A0Q5Y3)", fontsize=11)
    ax.set_ylabel("Per-residue pLDDT  (mean ± σ over 5 samples)", fontsize=11)
    ax.set_xlim(1230, 1620)
    ax.set_ylim(0.55, 1.02)
    ax.legend(loc="lower right", fontsize=10, ncols=4, framealpha=0.95)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)
    ax.set_title("Per-residue pLDDT across WED+PI — PLM5 holds WT-like confidence at every engineered site\n"
                 "(MSA-Boltz, 5 diffusion samples per variant)",
                 fontsize=12, fontweight="bold", pad=10)
    plt.tight_layout()
    path = FIG_DIR / "plddt_line_plot.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_distance_heatmap() -> Path:
    """12×12 CA-CA pairwise distance heatmap for the candidate positions.

    Diagonal blocks: en31 cluster (tight), PLM5 spread (loose).
    """
    import biotite.structure.io.pdb as pdb_io

    pdb_path = ROOT / "data" / "raw" / "5B2O.pdb"
    pdb = pdb_io.PDBFile.read(str(pdb_path))
    s = pdb.get_structure(model=1)
    ca_mask = (s.chain_id == "A") & (s.atom_name == "CA")
    ca = s[ca_mask]
    coord_by_id = {int(r): c for r, c in zip(ca.res_id, ca.coord)}

    # Order positions so en31 sit together, PLM5 together, etc.
    ordered = [
        # en31 (3)
        (1243, "G1243T", "en31"),
        (1369, "E1369R", "en31"),
        (1449, "E1449H", "en31"),
        # PLM5 (4)
        (1249, "Y1249F", "PLM5"),
        (1325, "A1325K", "PLM5"),
        (1341, "Y1341L", "PLM5"),
        (1479, "K1479F", "PLM5"),
        # PLM4-only (1)
        (1535, "T1535V", "PLM4"),
        # PLM3-only (3)
        (1292, "C1292K", "PLM3"),
        (1507, "W1507K", "PLM3"),
        (1617, "M1617K", "PLM3"),
        # en15 (1)
        (1603, "E1603H", "en15"),
    ]
    n = len(ordered)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            ci = coord_by_id[ordered[i][0]]
            cj = coord_by_id[ordered[j][0]]
            D[i, j] = np.linalg.norm(ci - cj)

    fig, ax = plt.subplots(figsize=(11, 9.5), dpi=160)
    # Use a colormap that emphasizes the 0-15 Å "trained regime" of ThermoMPNN-D
    im = ax.imshow(D, cmap="viridis_r", vmin=0, vmax=60, aspect="equal")
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("CA-CA distance (Å)", fontsize=10)
    cbar.ax.axhline(10, color="white", linewidth=1.5)
    cbar.ax.axhline(15, color="white", linewidth=0.8, linestyle="--")
    cbar.ax.text(1.5, 10, "  ThermoMPNN-D\n  trained ≤10 Å",
                 fontsize=8, va="center", color="#333")
    cbar.ax.text(1.5, 15, "  borderline 15 Å",
                 fontsize=8, va="center", color="#666")

    labels = [f"{p[1]} ({p[2]})" for p in ordered]
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    # Annotate cells with distance
    for i in range(n):
        for j in range(n):
            val = D[i, j]
            text_color = "white" if val > 30 else "black"
            ax.text(j, i, f"{val:.1f}" if i != j else "—",
                    ha="center", va="center", fontsize=8, color=text_color)

    # Mark variant groups with colored rectangles
    from matplotlib.patches import Rectangle
    group_bounds = [
        (0, 3, COLOR_EN31, "en31"),    # rows/cols 0-2
        (3, 7, COLOR_PLM5, "PLM5"),    # rows/cols 3-6
    ]
    for lo, hi, color, name in group_bounds:
        ax.add_patch(Rectangle((lo - 0.5, lo - 0.5), hi - lo, hi - lo,
                               fill=False, edgecolor=color, linewidth=3))

    ax.set_title("Pairwise CA-CA distances between candidate positions (PDB 5B2O)\n"
                 "en31 block (top-left): all 8.5–9 Å — clustered.   "
                 "PLM5 block (3-6): 14–50 Å — distributed.",
                 fontsize=11.5, fontweight="bold", pad=10)
    plt.tight_layout()
    path = FIG_DIR / "distance_heatmap.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_msa_boltz_5variants() -> Path:
    """MSA-Boltz apples-to-apples — 5 variants × 3 key metrics.

    Story: PLM5 leads on every metric AND has the tightest σ (variance ~7×
    tighter than WT/single-seq). Lead robustness-phase finding (§2.1).
    """
    # Order by iPTM ranking — clearest visual narrative
    variants = ["PLM5", "en31", "PLM4", "WT", "PLM3"]
    metrics = [
        ("iPTM (all interfaces)",  {"WT":0.926,"PLM3":0.862,"PLM4":0.933,"PLM5":0.951,"en31":0.940},
                                   {"WT":0.038,"PLM3":0.076,"PLM4":0.027,"PLM5":0.005,"en31":0.009}),
        ("complex_iplddt",         {"WT":0.908,"PLM3":0.856,"PLM4":0.919,"PLM5":0.918,"en31":0.909},
                                   {"WT":0.005,"PLM3":0.032,"PLM4":0.004,"PLM5":0.001,"en31":0.002}),
        ("prot↔DNA-PAM iPTM\n(functional regime)",
                                   {"WT":0.917,"PLM3":0.848,"PLM4":0.919,"PLM5":0.937,"en31":0.927},
                                   {"WT":0.028,"PLM3":0.068,"PLM4":0.025,"PLM5":0.007,"en31":0.009}),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), dpi=160, sharey=True)
    for ax, (mname, means, stds) in zip(axes, metrics):
        vals = [means[v] for v in variants]
        errs = [stds[v] for v in variants]
        colors = [VARIANT_COLORS[v] for v in variants]
        # Emphasize PLM5 with thicker edge
        edges = ["black"] * len(variants)
        widths = [0.6] * len(variants)
        for i, v in enumerate(variants):
            if v == "PLM5":
                edges[i] = "#1B5E20"
                widths[i] = 2.5
        bars = ax.bar(variants, vals, yerr=errs, color=colors,
                      edgecolor=edges, linewidth=widths, capsize=4,
                      error_kw={"elinewidth": 1.2, "ecolor": "#333"})
        # Annotate values
        for b, val, err in zip(bars, vals, errs):
            ax.text(b.get_x() + b.get_width()/2, val + err + 0.006,
                    f"{val:.3f}", ha="center", fontsize=9.5,
                    fontweight="bold" if val == max(vals) else "normal")
        ax.set_title(mname, fontsize=11, pad=8)
        ax.set_ylim(0.78, 1.00)
        ax.axhline(0.90, color="grey", linestyle="--", linewidth=0.5, alpha=0.4)
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelsize=10)

    axes[0].set_ylabel("Confidence (mean ± σ over 5 diffusion samples)", fontsize=11)
    fig.suptitle("MSA-Boltz apples-to-apples — PLM5 leads all 5 variants (§2.1 robustness)\n"
                 "MSA tightened PLM5's iPTM σ from 0.034 (single-seq) → 0.005 (~7× tighter)",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = FIG_DIR / "msa_boltz_5variants.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_spcas9_baseline() -> Path:
    """Cross-species baseline (Tier 1 Phase A): SpCas9 PI vs FnCas9 set.

    Caveats baked into the figure title + annotations: truncation-size mismatch
    (SpCas9 269 aa vs FnCas9 391 aa) and MSA-depth asymmetry. The figure does
    NOT claim PLM5 > SpCas9; it shows all 4 sit in the high-confidence regime
    with confound annotations clearly visible.
    """
    variants = ["SpCas9 PI\n(269 aa)", "PLM5\n(391 aa)", "en31\n(391 aa)", "WT\n(391 aa)"]
    metrics = [
        ("Overall iPTM",
         [0.952, 0.951, 0.940, 0.926],
         [0.001, 0.005, 0.009, 0.038]),
        ("prot↔DNA-PAM iPTM\n(functional regime)",
         [0.967, 0.937, 0.927, 0.917],
         [0.001, 0.007, 0.009, 0.028]),
    ]
    SPCAS9_COLOR = "#7B1FA2"
    colors = [SPCAS9_COLOR, VARIANT_COLORS["PLM5"], VARIANT_COLORS["en31"], VARIANT_COLORS["WT"]]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=160, sharey=True)
    for ax, (mname, vals, errs) in zip(axes, metrics):
        bars = ax.bar(variants, vals, yerr=errs, color=colors,
                      edgecolor="black", linewidth=0.6, capsize=4,
                      error_kw={"elinewidth": 1.2, "ecolor": "#333"})
        for b, val, err in zip(bars, vals, errs):
            ax.text(b.get_x() + b.get_width()/2, val + err + 0.005,
                    f"{val:.3f}", ha="center", fontsize=10, fontweight="bold")
        ax.set_title(mname, fontsize=11, pad=8)
        ax.set_ylim(0.85, 1.00)
        ax.axhline(0.92, color="grey", linestyle="--", linewidth=0.5, alpha=0.5)
        ax.text(3.4, 0.921, "iPTM = 0.92\n(high-confidence threshold)",
                ha="right", fontsize=8, color="grey", alpha=0.7)
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelsize=9.5)

    axes[0].set_ylabel("Confidence (mean ± σ over 5 diffusion samples)", fontsize=11)
    fig.suptitle("Cross-species baseline (Tier 1 Phase A): PLM5 in same regime as SpCas9 PI\n"
                 "Caveat: SpCas9 absolute +0.030 partly confounded by truncation size (269 vs 391 aa) "
                 "and deeper SpCas9 MSA",
                 fontsize=11.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = FIG_DIR / "spcas9_cross_species.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_thermompnn_epistasis() -> Path:
    """ThermoMPNN-D pairwise epistasis — en31 (clustered, coupled) vs PLM5 (distributed, additive).

    Dual panel: each variant shows per-pair additive vs epistatic ΔΔG with
    distance and coupling regime. Cumulative |Σ ep|/|Σ add| ratio annotated.
    """
    en31_pairs = [
        ("G1243T:E1369R", 8.99, -0.144, -0.662, -0.519, "trained"),
        ("G1243T:E1449H", 8.57, +0.776, +0.139, -0.637, "trained"),
        ("E1369R:E1449H", 8.47, -0.437, -0.658, -0.220, "trained"),
    ]
    plm5_pairs = [
        ("Y1249F:Y1341L", 14.09, +0.077, +0.115, +0.038, "borderline"),
        ("Y1249F:A1325K", 22.10, +0.479, None, None, "out-of-dist"),
        ("Y1249F:K1479F", 27.97, +1.020, None, None, "out-of-dist"),
        ("A1325K:Y1341L", 33.42, -0.343, None, None, "out-of-dist"),
        ("A1325K:K1479F", 50.00, +0.600, None, None, "out-of-dist"),
        ("Y1341L:K1479F", 21.82, +0.198, None, None, "out-of-dist"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=160)

    def draw_panel(ax, pairs, title, color, ratio_text):
        labels = [p[0] for p in pairs]
        dists = [p[1] for p in pairs]
        add_vals = [p[2] for p in pairs]
        epi_vals = [p[3] if p[3] is not None else p[2] for p in pairs]  # fall back to additive when out-of-dist
        epi_present = [p[3] is not None for p in pairs]

        x = np.arange(len(labels))
        width = 0.38
        b_add = ax.bar(x - width/2, add_vals, width, label="Additive (Σ singles)",
                       color="#B0B0B0", edgecolor="black", linewidth=0.5)
        b_epi_vals = [e if present else 0 for e, present in zip(epi_vals, epi_present)]
        b_epi = ax.bar(x + width/2, b_epi_vals, width, label="Epistatic (coupled head)",
                       color=color, edgecolor="black", linewidth=0.5)
        # Annotate epistasis term for in-distance pairs — always place above the
        # tallest of (additive, epistatic, 0) so labels never sit inside the bar.
        for i, p in enumerate(pairs):
            if p[3] is not None:
                ep = p[4]
                ann = f"ε={ep:+.2f}"
                weight = "bold" if abs(ep) > 0.3 else "normal"
                top_y = max(p[2], p[3], 0) + 0.15
                fcolor = "#1B5E20" if ep < -0.3 else ("#C0392B" if ep > 0.3 else "#333")
                ax.text(i, top_y, ann, ha="center", fontsize=9.5,
                        fontweight=weight, color=fcolor,
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                                  edgecolor=fcolor, linewidth=1.0, alpha=0.95))
            else:
                ax.text(i + width/2, 0.04, "out of\ndist.", ha="center", va="bottom",
                        fontsize=8, color="#888", style="italic")
        # Distance subscript under each x-tick
        ax.set_xticks(x)
        ax.set_xticklabels([f"{lbl}\n{d:.1f} Å" for lbl, d in zip(labels, dists)],
                           fontsize=9)
        ax.set_ylabel("ΔΔG (kcal/mol)", fontsize=11)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)
        ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
        # Big ratio annotation
        ax.text(0.02, 0.98, ratio_text, transform=ax.transAxes,
                fontsize=11, fontweight="bold", va="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFEF0",
                          edgecolor=color, linewidth=1.5))

    draw_panel(
        axes[0], en31_pairs,
        "en31 (Acharya 2024) — clustered geometry (8.5–9 Å), strongly coupled",
        COLOR_EN31,
        "|Σ epistasis| / |Σ additive|\n"
        "= 1.376 / 0.195 = 7.1×\n"
        "coupling dominates the signal\n"
        "(stabilizing — matches wet-lab gain)",
    )
    axes[0].set_ylim(-1.0, 1.4)

    draw_panel(
        axes[1], plm5_pairs,
        "PLM5 — distributed geometry (14–50 Å), independence holds",
        COLOR_PLM5,
        "|Σ epistasis| / |Σ additive|\n"
        "= 0.038 / 2.031 = 0.019 (2%)\n"
        "additive scoring operationally safe\n"
        "(370× margin over en31)",
    )
    axes[1].set_ylim(-1.0, 1.4)

    fig.suptitle("ThermoMPNN-D pairwise epistasis (§2.3) — same model, opposite geometries",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = FIG_DIR / "thermompnn_epistasis.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_cross_method_plm4() -> Path:
    """Three-method convergence on PLM4/T1535V — apo-ΔΔG filter was miscalibrated.

    Three side-by-side panels, each on its native scale (kcal/mol for the
    two ΔΔG methods, iPTM for Boltz). Verdict badge sits beneath each panel.
    """
    from matplotlib.patches import FancyBboxPatch
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), dpi=160,
                             gridspec_kw={"wspace": 0.35})

    # Panel 1 — proteinmpnn_ddg (apo ΔΔG, kcal/mol)
    ax = axes[0]
    envelope_lo, envelope_hi, ceiling = -1.4, 0.4, 3.2
    val = 4.15
    ax.bar(["T1535V"], [val], color=COLOR_PLM3, edgecolor="black", linewidth=0.8, width=0.5)
    ax.axhspan(envelope_lo, envelope_hi, color=COLOR_EN31, alpha=0.10, label="en31 envelope")
    ax.axhline(ceiling, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(0.4, ceiling + 0.15, "+3.20 ceiling (en31's worst single)",
            fontsize=8, color="grey", ha="right", va="bottom")
    ax.text(0, val + 0.2, f"+{val}", ha="center", fontsize=14, fontweight="bold")
    ax.set_ylim(-3, 6)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("single-position ΔΔG (kcal/mol)", fontsize=10)
    ax.set_title("proteinmpnn_ddg\n(apo, original filter)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)

    # Panel 2 — ThermoMPNN (apo ΔΔG, kcal/mol, same scale as panel 1)
    ax = axes[1]
    val = -0.19
    ax.bar(["T1535V"], [val], color="#B0B0B0", edgecolor="black", linewidth=0.8, width=0.5)
    ax.axhspan(envelope_lo, envelope_hi, color=COLOR_EN31, alpha=0.10, label="en31 envelope")
    ax.axhline(ceiling, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(0, val - 0.4, f"{val:.2f}", ha="center", fontsize=14, fontweight="bold")
    ax.set_ylim(-3, 6)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("single-position ΔΔG (kcal/mol)", fontsize=10)
    ax.set_title("ThermoMPNN\n(apo, cross-check)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)

    # Panel 3 — Boltz-2 (complex iPTM)
    ax = axes[2]
    val, err = 0.933, 0.025
    ref_lo, ref_hi = 0.940 - 0.009, 0.951 + 0.005   # en31 / PLM5 reference band
    ax.bar(["PLM4"], [val], yerr=[err], color=COLOR_PLM5, edgecolor="black",
           linewidth=0.8, width=0.5, capsize=6,
           error_kw={"elinewidth": 1.2, "ecolor": "#333"})
    ax.axhspan(ref_lo, ref_hi, color=COLOR_PLM5, alpha=0.10, label="en31 / PLM5 band")
    ax.text(0, val + err + 0.005, f"{val:.3f}", ha="center", fontsize=14, fontweight="bold")
    ax.set_ylim(0.85, 1.00)
    ax.set_ylabel("iPTM (Boltz-2 complex confidence)", fontsize=10)
    ax.set_title("Boltz-2\n(complex, direct prediction)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", linewidth=0.3, alpha=0.4)
    ax.set_axisbelow(True)

    # Verdict badges below each panel
    verdicts = [
        ("REJECT",  "#C0392B", "outside +3.20 envelope"),
        ("NEUTRAL", "#7F7F7F", "essentially neutral"),
        ("ACCEPT",  "#1B5E20", "indistinguishable from en31/PLM5"),
    ]
    for ax, (verdict, color, note) in zip(axes, verdicts):
        # Verdict text below the axis
        ax.annotate(verdict, xy=(0.5, -0.18), xycoords="axes fraction",
                    ha="center", fontsize=14, fontweight="bold", color="white",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor=color,
                              edgecolor="black", linewidth=1))
        ax.annotate(note, xy=(0.5, -0.30), xycoords="axes fraction",
                    ha="center", fontsize=9, color="#555", style="italic")

    fig.suptitle("Three-method verdict on FnCas9-PLM4 / T1535V (§2.2 robustness)\n"
                 "Two of three methods accept — the apo-ΔΔG filter that rejected PLM4 was miscalibrated for hydrophobic↔K",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = FIG_DIR / "cross_method_plm4.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_e1449_comparison() -> Path:
    """§2.5 result — E1449L vs E1449H single-point Boltz, with en31 (which carries E1449H
    in the triple context) as reference. Headline: Boltz cannot discriminate the two on any
    global metric; E1449L has ~2× higher variance across diffusion samples.
    """
    # Mean ± σ across 5 MSA-Boltz diffusion samples (run 2026-05-18_boltz_e1449)
    # en31 reference values from the 2026-05-15 MSA-Boltz apples-to-apples run
    metrics = [
        ("iPTM\n(all interfaces)",   {"E1449H": (0.926, 0.040), "E1449L": (0.912, 0.077), "en31 (ref)": (0.940, 0.009)}),
        ("complex iplddt",            {"E1449H": (0.910, 0.005), "E1449L": (0.908, 0.013), "en31 (ref)": (0.909, 0.002)}),
        ("iPTM\nprot↔DNA-PAM",        {"E1449H": (0.924, 0.030), "E1449L": (0.919, 0.050), "en31 (ref)": (0.927, 0.009)}),
        ("per-res pLDDT\n@ position 1449", {"E1449H": (0.951, 0.0), "E1449L": (0.954, 0.0), "en31 (ref)": (0.955, 0.0)}),
    ]
    variants = ["E1449H", "E1449L", "en31 (ref)"]
    colors = {"E1449H": COLOR_EN31, "E1449L": COLOR_PLM5, "en31 (ref)": "#888"}

    fig, axes = plt.subplots(1, 4, figsize=(15, 5), dpi=160)
    for ax, (mname, vals) in zip(axes, metrics):
        means = [vals[v][0] for v in variants]
        stds = [vals[v][1] for v in variants]
        bar_colors = [colors[v] for v in variants]
        bars = ax.bar(variants, means, yerr=stds, color=bar_colors,
                      edgecolor="black", linewidth=0.6, capsize=4,
                      error_kw={"elinewidth": 1.0, "ecolor": "#333"})
        for b, m, s in zip(bars, means, stds):
            ax.text(b.get_x() + b.get_width()/2, m + max(s, 0.005) + 0.003,
                    f"{m:.3f}", ha="center", fontsize=9.5, fontweight="bold")
        ax.set_title(mname, fontsize=10.5, pad=8)
        ax.set_ylim(0.84, 1.00)
        ax.tick_params(axis="x", labelsize=9)
        ax.grid(axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)

    axes[0].set_ylabel("Confidence (mean ± σ, 5 samples)", fontsize=10)
    fig.suptitle("§2.5 — E1449L vs E1449H single-point Boltz on WT backbone\n"
                 "Means within 1σ on every metric · E1449L has ~2× higher prediction variance · per-res pLDDT @1449 indistinguishable",
                 fontsize=12, fontweight="bold", y=1.03)
    plt.tight_layout()
    path = FIG_DIR / "e1449_comparison.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_robustness_gate() -> Path:
    """5-criterion 'ready for the PI' gate checklist visual."""
    criteria = [
        (1, "Two independent structure predictors agree on PLM5's PAM-interface",
            "in-flight",  "MSA-Boltz done;  AF3 Server pending  (Chai-1 dropped: V100 bf16-incompat)"),
        (2, "Functional gap closed — predicted PAM tolerance ≥ NGG-only",
            "done",       "Protein2PAM + Boltz PAM-scan (SLURM 221069); PLM5 robustness positive — done 2026-05-18"),
        (3, "apo-ΔΔG filter calls independently bracketed",
            "done",       "ThermoMPNN cross-check + direct Boltz on PLM4 — done 2026-05-15"),
        (4, "Pairwise epistasis effects characterized",
            "done",       "ThermoMPNN-D — PLM5 |Σ ep|/|Σ add| = 0.019 — done 2026-05-15"),
        (5, "Falsifiable predictions on record (E1449L vs E1449H) with CI",
            "done",       "Boltz can't discriminate (ΔiPTM −0.014, within σ) — done 2026-05-18"),
    ]
    status_color = {
        "done":      "#1B5E20",
        "in-flight": "#E67E22",
        "pending":   "#C0392B",
    }

    fig, ax = plt.subplots(figsize=(13, 6), dpi=160)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, len(criteria) + 1.6)
    ax.axis("off")

    # Header
    ax.text(8, len(criteria) + 1.1, "'Ready for the PI' gate — 5 criteria",
            ha="center", fontsize=15, fontweight="bold", color="#1F2A4C")
    ax.text(8, len(criteria) + 0.55,
            "Wet-lab handoff is gated on all five being green — currently 4 done, 1 in-flight (AF3 Server)",
            ha="center", fontsize=11, color="#555", style="italic")

    for i, (num, text, status, what_closes) in enumerate(criteria):
        y = len(criteria) - i - 0.5
        color = status_color[status]
        # Number circle
        from matplotlib.patches import Circle, FancyBboxPatch
        circle = Circle((0.7, y), 0.32, facecolor=color, edgecolor="black", linewidth=1)
        ax.add_patch(circle)
        ax.text(0.7, y, str(num), ha="center", va="center",
                fontsize=12, fontweight="bold", color="white")
        # Status badge
        badge = FancyBboxPatch((1.4, y - 0.32), 1.5, 0.64,
                               boxstyle="round,pad=0.05",
                               facecolor=color, edgecolor="black", linewidth=0.8)
        ax.add_patch(badge)
        ax.text(2.15, y, status.upper(), ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
        # Criterion text
        ax.text(3.2, y + 0.15, text, va="center", fontsize=11.5,
                color="#1F2A4C", fontweight="bold")
        # What closes it
        ax.text(3.2, y - 0.22, what_closes, va="center", fontsize=10,
                color="#555", style="italic")

    plt.tight_layout()
    path = FIG_DIR / "robustness_gate.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


def fig_pipeline_flowchart() -> Path:
    """6-phase pipeline diagram — original campaign (Phases 1-5) + robustness (Phase 6).

    Top half: campaign flow ending in PLM5 recommendation.
    Bottom half: robustness phase with 5 dimensions and current status.
    """
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(16, 10), dpi=160)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 13)
    ax.axis("off")

    arrow_kwargs = dict(arrowstyle="->", linewidth=1.5, color="#444")

    def box(x, y, w, h, title, body, color="white", edge="black", lw=1.1,
            title_size=10, body_size=8.5):
        bp = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor=edge, linewidth=lw)
        ax.add_patch(bp)
        ax.text(x + w/2, y + h - 0.30, title, ha="center", va="top",
                fontsize=title_size, fontweight="bold")
        ax.text(x + w/2, y + h - 0.80, body, ha="center", va="top", fontsize=body_size)

    def arrow(x1, y1, x2, y2, kw=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=kw or arrow_kwargs)

    # ─── TOP HALF — campaign (Phases 1-5) ════════════════════════════
    ax.text(8, 12.6, "Original campaign (2026-05-12 → 2026-05-14)",
            ha="center", fontsize=13, fontweight="bold", color="#1F2A4C")

    # Row 1: Phase 1 → Phases 2 / 3 (parallel paths)
    box(0.3, 10.7, 2.8, 1.6, "Phase 1\nLiterature",
        "Acharya 2024, Hirano 2016\n26+ claims verified", "#F0F4F8")
    box(4.0, 11.3, 3.4, 1.0, "Phase 2 — Sequence",
        "ESM-2 650M zero-shot · 7,429 variants", "#E8F0FA")
    box(4.0, 9.8, 3.4, 1.0, "Phase 3 — Structure",
        "LigandMPNN · 5B2O+sgRNA+DNA · 4,800 samples", "#E8F5EE")

    # Row 2: candidates — taller boxes to fit 2-line mutation strings
    box(8.2, 11.1, 2.6, 1.2, "PLM3",
        "G1243T / W1507K /\nC1292K / M1617K", "#FCE9E6", body_size=8)
    box(8.2, 9.6, 2.6, 1.2, "PLM4",
        "T1535V / Y1249F /\nY1341L / A1325K", "#FFF3E0", body_size=8)

    # Phase 4 ΔΔG → PLM5 (one clear row on its own)
    box(11.6, 9.6, 1.9, 1.2, "Phase 4 — ΔΔG",
        "proteinmpnn_ddg\nstability gate", "#FFF3E0", body_size=8)
    box(13.8, 9.6, 1.9, 1.2, "PLM5 ★",
        "Y1249F / Y1341L /\nA1325K / K1479F",
        "#E8F5EE", edge="#1B5E20", lw=2.0, body_size=8)

    # "T1535V rejected" note — placed clearly below PLM4 row
    ax.text(12.65, 9.35, "T1535V rejected by ΔΔG → K1479F substituted",
            ha="center", fontsize=7.5, color="#C0392B", style="italic")

    # Phase 5 Boltz — now sits with clear gap below
    box(3.5, 7.5, 9.0, 1.4, "Phase 5 — Boltz-2 complex prediction",
        "Truncated WED+PI (1230-1620) × {WT, PLM3, PLM5, en31}  ·  5 diffusion samples\n"
        "Result: PLM5 ≈ en31 structurally   →   campaign complete",
        "#E8F0FA", title_size=11, body_size=9)

    # Arrows top half — vert centers: row 1 (PLM3) = 11.7, row 2 (PLM4/ΔΔG/PLM5) = 10.2
    arrow(3.1, 11.5, 4.0, 11.8)       # P1 → P2
    arrow(3.1, 11.5, 4.0, 10.3)       # P1 → P3
    arrow(7.4, 11.8, 8.2, 11.7)       # P2 → PLM3
    arrow(7.4, 10.3, 8.2, 10.2)       # P3 → PLM4
    arrow(10.8, 10.2, 11.6, 10.2)     # PLM4 → ΔΔG
    arrow(13.5, 10.2, 13.8, 10.2)     # ΔΔG → PLM5
    # PLM3 → Boltz (skips ΔΔG filter)
    arrow(9.5, 11.1, 7.5, 8.9,
          {"arrowstyle": "->", "linewidth": 1.0, "color": "#888",
           "linestyle": ":", "connectionstyle": "arc3,rad=0.2"})
    # PLM5 → Boltz
    arrow(14.75, 9.6, 11.0, 8.9,
          {"arrowstyle": "->", "linewidth": 1.0, "color": "#1B5E20",
           "connectionstyle": "arc3,rad=-0.2"})

    # ─── Divider ════════════════════════════════════════════════════
    ax.plot([0.3, 15.7], [6.7, 6.7], color="#888", linewidth=0.8, linestyle="--")
    ax.text(8, 6.85,
            "candidate strengthened — but in-silico robustness must pass before wet-lab",
            ha="center", fontsize=10, color="#666", style="italic")

    # ─── BOTTOM HALF — Phase 6 Robustness ══════════════════════════
    ax.text(8, 6.3, "Phase 6 — In-silico robustness (active, 2026-05-15 →)",
            ha="center", fontsize=13, fontweight="bold", color="#1F2A4C")

    # 5 dimension chips
    dims = [
        (0.3,  "§2.1 Structural\n(2 predictors)",   "MSA-Boltz: done\nAF3 Server: pending",     "in-flight"),
        (3.5,  "§2.2 Filter / method",              "PLM4 reinstated\nΔΔG bracketed",           "done"),
        (6.7,  "§2.3 Epistasis",                    "ThermoMPNN-D\nPLM5 ratio 0.019",           "done"),
        (9.9,  "§2.4 Functional\n(PAM tolerance)",  "PLM5 robust\nacross all PAMs",             "done"),
        (13.1, "§2.5 Falsifiable\n(E1449L vs H)",   "Boltz: L ≈ H\n(within σ)",                 "done"),
    ]
    status_color = {
        "done":      ("#E8F5EE", "#1B5E20"),
        "in-flight": ("#FFF3E0", "#E67E22"),
        "pending":   ("#FCE9E6", "#C0392B"),
    }
    status_label = {"done": "DONE", "in-flight": "IN-FLIGHT", "pending": "PENDING"}
    for x, title, body, status in dims:
        fc, ec = status_color[status]
        box(x, 3.2, 2.8, 2.1, title, body, fc, edge=ec, lw=1.8, body_size=8.5)
        # Status badge atop each chip
        ax.text(x + 1.4, 3.0, status_label[status], ha="center", fontsize=8,
                fontweight="bold", color=ec)

    # PI gate
    box(4.5, 0.3, 7.0, 1.8, "'Ready for the PI' gate",
        "All 5 criteria green → wet-lab handoff\n"
        "Current: 4 DONE  ·  1 IN-FLIGHT (AF3 Server)",
        "#E8F5EE", edge="#1B5E20", lw=2.5, title_size=11, body_size=9.5)

    # Light arrows from each dim into the gate
    for x, *_ in dims:
        arrow(x + 1.4, 3.2, 8.0, 2.15,
              {"arrowstyle": "->", "linewidth": 0.6, "color": "#BBB"})

    ax.set_title("FnCas9 PLM redesign pipeline — campaign (Phases 1-5) + robustness (Phase 6)",
                 fontsize=14, fontweight="bold", y=1.0)
    plt.tight_layout()
    path = FIG_DIR / "pipeline_flowchart.png"
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log.info("wrote %s", path)
    return path


# ── Slide construction ──────────────────────────────────────────────────────

def add_title_slide(prs, title, subtitle):
    layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = subtitle
    # Style title
    p = slide.shapes.title.text_frame.paragraphs[0]
    p.runs[0].font.size = Pt(36)
    p.runs[0].font.color.rgb = ANTHRO_NAVY
    p.runs[0].font.bold = True
    return slide


def add_content_slide(prs, title):
    """Returns a slide with title and an empty body area (no placeholders to manage)."""
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    # Title bar
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.7))
    tf = title_box.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.runs[0].font.size = Pt(24)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = ANTHRO_NAVY
    # Underline bar
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.0),
                                  Inches(12.5), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = ANTHRO_BLUE
    line.line.fill.background()
    return slide


def add_textbox(slide, text, x, y, w, h, *, size=14, bold=False, color=DARK_GREY, bullet=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        prefix = "• " if bullet and line.strip() and not line.startswith("  ") else ""
        p.text = prefix + line.lstrip()
        for run in p.runs:
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color
    return box


def add_picture(slide, path, x, y, w, h):
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y),
                                    width=Inches(w), height=Inches(h))


def add_table(slide, data, x, y, w, h, *, header_color=ANTHRO_NAVY, header_text_color=RGBColor(255,255,255)):
    rows, cols = len(data), len(data[0])
    tbl = slide.shapes.add_table(rows, cols, Inches(x), Inches(y),
                                 Inches(w), Inches(h)).table
    for i, row in enumerate(data):
        for j, cell_text in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(cell_text)
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(11)
                    if i == 0:
                        run.font.bold = True
                        run.font.color.rgb = header_text_color
                    else:
                        run.font.color.rgb = DARK_GREY
            if i == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color
            elif i % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_GREY
    return tbl


# ── Slide content ────────────────────────────────────────────────────────────

def build_deck():
    log.info("Generating figures...")
    fig_pipeline = fig_pipeline_flowchart()
    fig_esm_vs_lig = fig_esm_vs_ligandmpnn_head_to_head()
    fig_ddg = fig_ddg_calibration()
    fig_boltz_bars = fig_confidence_bars()
    fig_residue = fig_per_residue_plddt()
    # Robustness-phase figures (added 2026-05-16)
    fig_msa_5var = fig_msa_boltz_5variants()
    fig_epistasis = fig_thermompnn_epistasis()
    fig_plm4_xmeth = fig_cross_method_plm4()
    fig_gate = fig_robustness_gate()
    # Structural / per-residue / geometry figures (added 2026-05-16, second pass)
    fig_struct = fig_structural_3d()
    fig_plddt = fig_plddt_line_plot()
    fig_dist = fig_distance_heatmap()
    # §2.5 result figure (added 2026-05-18)
    fig_e1449 = fig_e1449_comparison()
    # Tier 1 Phase A: SpCas9 cross-species baseline (added 2026-05-18 evening)
    fig_spcas9 = fig_spcas9_baseline()

    log.info("\nBuilding deck...")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ── Slide 1: Title ──────────────────────────────────────────────────────
    s = add_title_slide(prs,
        "PLM-Guided Redesign of FnCas9",
        "Toward enFnCas9-class activity with sequence and structure-conditioned models\n\n"
        "Vishal Bharti — CSIR-IGIB\n"
        "In-silico campaign, 2026-05-12 to 2026-05-14")

    # ── Slide 2: Executive summary ──────────────────────────────────────────
    s = add_content_slide(prs, "Executive summary")
    add_textbox(s,
        "What we set out to do",
        0.6, 1.2, 12, 0.5, size=18, bold=True, color=ANTHRO_BLUE)
    add_textbox(s,
        "Use protein language models to redesign FnCas9 (UniProt A0Q5Y3, PDB 5B2O, 1,629 aa) toward "
        "enFnCas9-class activity — a 2024-published functional variant (en31 = G1243T / E1369R / E1449H) "
        "with >2× cleavage activity, expanded PAM (NGG → NGG/NGA/NAG), and ~1,300× specificity over SpCas9.",
        0.6, 1.7, 12, 1.2, size=13)

    add_textbox(s,
        "What we found",
        0.6, 3.0, 12, 0.5, size=18, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "PLM5 (LigandMPNN + apo-ΔΔG filter) is structurally indistinguishable from en31 in Boltz-2 prediction. Every confidence metric within 1σ.",
        "Sequence-only ESM-2 misses PAM-contact engineering: ranks en31's E1369R / E1449H / E1603H in the bottom half of a 7,429-variant pool.",
        "Structure+ligand-conditioned LigandMPNN recovers the biophysical insight: strongly wants E1369→K/R (the en31 charge swap).",
        "PLM3 (ESM-2 zero-shot only) is structurally compromised — Boltz iPTM drops 0.04-0.08 vs WT. Sequence-only PLMs are not enough.",
        "Apo-ΔΔG filter caught the right outlier: PLM5 dropped PLM4's T1535V (+4.15 kcal/mol) and matched en31 structurally.",
    ], 0.6, 3.6, 12, 3.5, size=12, bullet=True)

    # ── Slide 3: The biological problem ─────────────────────────────────────
    s = add_content_slide(prs, "Why FnCas9, why redesign")
    add_textbox(s, [
        "Specificity — engineered FnCas9 (Acharya 2024) shows ~1,300× higher genome-wide specificity vs SpCas9 (Digenome-seq). For therapeutic gene editing, off-target activity is the dominant risk.",
        "PAM flexibility — WT FnCas9 cleaves with 5'-NGG-3' PAM. en31 broadens to NGG/NGA/NAG, expanding the targetable fraction of the human genome ~3.5×.",
        "Diagnostic relevance — FnCas9-based diagnostics (FELUDA, MUTE-Seq) are CSIR-IGIB-led platforms for paper-strip and ultrasensitive nucleic-acid detection. Improving the FnCas9 base would propagate to diagnostic performance.",
    ], 0.6, 1.4, 12, 3.0, size=14, bullet=True)

    add_textbox(s,
        "Reference variants (Acharya 2024 directed evolution, calibration anchors for our pipeline)",
        0.6, 4.6, 12, 0.5, size=14, bold=True, color=ANTHRO_BLUE)

    add_table(s, [
        ["Variant", "Mutations", "PAM", "Activity vs WT", "Use in this project"],
        ["en1",  "E1369R",                       "NGG/NGA/NAG", ">2× cleavage", "Single PAM-contact mutant ref"],
        ["en15", "E1603H",                       "NGG (lower K_d)", ">2× cleavage", "Stability calibration anchor"],
        ["en31", "G1243T / E1369R / E1449H",     "NGG/NGA/NAG", ">2× cleavage, 1,300× spec.", "Primary calibration anchor"],
    ], 0.6, 5.3, 12, 1.6)

    # ── Slide 4: What is a PLM? ─────────────────────────────────────────────
    s = add_content_slide(prs, "What is a protein language model?")
    add_textbox(s, [
        "A transformer neural network trained on 10⁸-10⁹ protein sequences (UniRef) to predict masked amino acids.",
        "ESM-2 (Meta AI, 2023, Science): 8M / 35M / 150M / 650M / 3B / 15B parameter sizes; we use 650M.",
        "Self-supervised: no functional labels needed. Learns evolutionary patterns from sequence alone.",
    ], 0.6, 1.3, 6, 2.5, size=13, bullet=True)

    add_textbox(s, "How we use it: zero-shot mutation effect prediction",
                0.6, 4.0, 6, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Replace residue at position pos with <mask>.",
        "Forward-pass through ESM-2. Read softmax distribution at the mask position.",
        "LLR = log P(MUT | masked) − log P(WT | masked).",
        "Positive LLR ⇒ model prefers the mutation evolutionarily.",
    ], 0.6, 4.6, 6, 2.5, size=12, bullet=True)

    add_textbox(s, "Critical blind spot",
                7.0, 1.3, 6, 0.5, size=14, bold=True, color=ANTHRO_RED)
    add_textbox(s, [
        "ESM-2 sees only sequence — no DNA, no sgRNA, no 3D coordinates.",
        "It learns evolutionary constraints implicitly, but cannot reason explicitly:",
        "  '+ charge at this position contacts a phosphate'.",
        "For Cas9 PAM-contact positions, this is a key limitation.",
        "Mitigation: complement with structure+ligand-conditioned models (LigandMPNN, this campaign Phase 3).",
    ], 7.0, 1.9, 6, 5, size=12, bullet=True)

    # ── Slide 5: Pipeline overview ──────────────────────────────────────────
    s = add_content_slide(prs, "The 5-phase pipeline")
    add_picture(s, fig_pipeline, 0.3, 1.3, 12.7, 5.7)

    # ── Slide 6: Phase 2 - ESM-2 scan method ────────────────────────────────
    s = add_content_slide(prs, "Phase 2: ESM-2 zero-shot scan over WED+PI")
    add_textbox(s, "Method", 0.6, 1.2, 6, 0.5, size=16, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Design region: residues 1230-1620 (WED + PI, 391 positions).",
        "All 19 substitutions per position = 7,429 variants.",
        "Model: ESM-2 650M (esm2_t33_650M_UR50D), fp16 inference.",
        "Mask-marginal LLR per variant, sorted by composite score:",
        "    composite = LLR − λ · class_conservation   (λ = 1.0)",
        "Hardware: 1× V100, ~3 minutes wall.",
    ], 0.6, 1.8, 6, 3, size=12, bullet=True)

    add_textbox(s, "Filters for candidate selection (PLM3)",
                7.0, 1.2, 6, 0.5, size=16, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "class_conservation < 0.5  (kills rare-AA-bias picks)",
        "LLR > 0  (model prefers mutant)",
        "top-K = 4 (matches en31's mutation count)",
        "min spacing 5 residues (no clustering)",
        "→ PLM3 = G1243T / W1507K / C1292K / M1617K",
    ], 7.0, 1.8, 6, 3, size=12, bullet=True)

    # ── Slide 7: Phase 2 finding ────────────────────────────────────────────
    s = add_content_slide(prs, "Phase 2 finding: ESM-2 misses PAM-contact engineering")
    add_picture(s, fig_esm_vs_lig, 0.3, 1.3, 12.7, 4.4)
    add_textbox(s, [
        "ESM-2 ranks G1243T (WED domain) #1 — top of 7,429 variants. Successful sanity check.",
        "ESM-2 ranks the three E→R/H PAM-contact mutations in the bottom half (Q3, rank 4,956-5,117).",
        "This is the sequence-only PLM blind spot in action: no DNA input, so no way to see that E→K/R is favorable at PAM-contact positions.",
    ], 0.6, 5.9, 12, 1.5, size=11.5, bullet=True)

    # ── Slide 8: Phase 3 - LigandMPNN ───────────────────────────────────────
    s = add_content_slide(prs, "Phase 3: LigandMPNN structure + ligand-conditioned design")
    add_textbox(s, "Method (Dauparas et al., Nat Methods 2025)", 0.6, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Inputs: 5B2O protein backbone + sgRNA atoms + DNA atoms within 8 Å.",
        "Architecture: message-passing GNN over a k-NN atom graph.",
        "Output: per-position aa distributions conditioned on (backbone, ligands).",
        "Sampling: 1,600 sequences × 3 temperatures (T = 0.1, 0.2, 0.3) = 4,800 total.",
        "Checkpoint: ligandmpnn_v_32_010_25.pt (paper default).",
        "Hardware: 1× V100, ~28 minutes wall.",
        "Design positions: A1230-A1620 (full WED+PI, 391 tokens, space-separated).",
    ], 0.6, 1.8, 6, 4, size=12, bullet=True)

    add_textbox(s, "Why this fixes ESM-2's blind spot", 7.0, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_GREEN)
    add_textbox(s, [
        "LigandMPNN SEES the DNA + sgRNA.",
        "At PAM-contact positions, it can directly reason about + vs − charge contributions to backbone interactions.",
        "Output: 159 / 391 positions have a top-pick different from WT.",
        "Direct comparison with ESM-2 at en31/en15 positions = the key scientific test.",
    ], 7.0, 1.8, 6, 4, size=12, bullet=True)

    # ── Slide 9: LigandMPNN head-to-head ────────────────────────────────────
    s = add_content_slide(prs, "Head-to-head: ESM-2 vs LigandMPNN at the en31/en15 positions")

    add_table(s, [
        ["Position",      "WT", "en target", "ESM-2 rank",  "LigandMPNN top non-WT pick",  "LigandMPNN target_freq"],
        ["1243 (WED)",    "G",  "T",         "1 / 7,429 ✓", "T = 0.455 (tied with S = 0.456)", "0.455"],
        ["1369 (PI)",     "E",  "R",         "4,956 / 7,429 (Q3)", "K = 0.522, R = 0.365",       "0.365"],
        ["1449 (PI)",     "E",  "H",         "5,117 / 7,429 (Q3)", "L = 0.985",                  "0.000"],
        ["1603 (PI)",     "E",  "H",         "5,109 / 7,429 (Q3)", "L = 0.517",                  "0.000"],
    ], 0.6, 1.4, 12, 2.3)

    add_textbox(s, "Three findings from one table:", 0.6, 4.1, 12, 0.5, size=15, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "At E1369: ESM-2 says 'leave as E' (Q3). LigandMPNN strongly wants change (WT_freq = 0.000), and prefers K/R — exactly Acharya's biophysical insight. The structure-conditioning fixes the blind spot.",
        "At E1449/E1603: both models DISAGREE with Acharya. Both prefer L. Either Acharya's H is functionally optimal for non-structural reasons (kinetics, off-target trade-offs) OR a wet-lab-evolved compromise. Falsifiable: E1449L vs E1449H wet-lab test.",
        "PLM4 candidate = T1535V / Y1249F / Y1341L / A1325K (top-K LigandMPNN picks under same filters as PLM3).",
    ], 0.6, 4.7, 12, 2.5, size=11.5, bullet=True)

    # ── Slide 10: Phase 4 - ΔΔG ─────────────────────────────────────────────
    s = add_content_slide(prs, "Phase 4: apo-ΔΔG stability filter — PLM5")
    add_textbox(s, "Method", 0.6, 1.2, 5.5, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Tool: proteinmpnn_ddg (Peptone Ltd, GitHub peptoneltd/proteinmpnn_ddg).",
        "Container: ghcr.io/peptoneltd/proteinmpnn_ddg:1.0.0_base (Singularity SIF on V100).",
        "Model: v_48_020 (ProteinMPNN 48-layer, σ=0.20).",
        "Full saturation: 1,455 positions × 20 aa = 29,100 per-position ΔΔG values, ~30 sec on V100.",
        "Critical caveat: measures APO-state stability — does not see DNA/sgRNA.",
    ], 0.6, 1.8, 5.5, 3, size=12, bullet=True)

    add_textbox(s, "en31 / en15 calibration", 6.5, 1.2, 6.5, 0.5, size=14, bold=True, color=ANTHRO_GREEN)
    add_textbox(s, [
        "en31 (functional, wet-lab) = +0.40 kcal/mol cumulative apo ΔΔG.",
        "en15 (functional, wet-lab) = -1.37 kcal/mol cumulative.",
        "en31's worst single-position: E1369R = +3.20 kcal/mol — still functional.",
        "→ Set --max-single-ddg ≤ 3.2 as filter threshold.",
        "Functional envelope ≈ [-1.4, +0.4] kcal/mol cumulative.",
    ], 6.5, 1.8, 6.5, 3, size=12, bullet=True)

    add_textbox(s, "Outcome: PLM4 → PLM5 (T1535V replaced by K1479F)",
                0.6, 5.0, 12, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "PLM4 cumulative apo ΔΔG = +6.74 (T1535V alone is +4.15 — outside calibrated envelope).",
        "Gate rejects T1535V; next-best LigandMPNN candidate K1479F (top_freq = 0.985, ΔΔG = -2.00) takes its place.",
        "PLM5 = Y1249F / Y1341L / A1325K / K1479F. Cumulative apo ΔΔG = +0.59 — essentially equal to en31's +0.40 anchor.",
    ], 0.6, 5.6, 12, 1.8, size=12, bullet=True)

    # ── Slide 11: ΔΔG calibration figure ────────────────────────────────────
    s = add_content_slide(prs, "ΔΔG calibration: candidates vs en31 functional envelope")
    add_picture(s, fig_ddg, 1.5, 1.3, 10.5, 5.8)

    # ── Slide 12: Phase 5 - Boltz method ────────────────────────────────────
    s = add_content_slide(prs, "Phase 5: Boltz-2 complex structure prediction")
    add_textbox(s, "Method (Wohlwend et al., 2024-2025)", 0.6, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Open-source AlphaFold-3-class model for protein + nucleic acid complexes.",
        "Inputs: protein FASTA + sgRNA + DNA target + DNA PAM strand (YAML per variant).",
        "Diffusion samples: 5 per variant (independent denoising trajectories).",
        "Outputs: per-residue pLDDT, pTM, iPTM per chain-pair.",
        "Hardware: 1× V100 32GB at fp16.",
    ], 0.6, 1.8, 6, 3.0, size=12, bullet=True)

    add_textbox(s, "Operational fixes (documented for reproducibility)",
                7.0, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_RED)
    add_textbox(s, [
        "Iter 1 (full-length 1,629 aa): OOM'd on all 4 variants. V100 32GB insufficient for full FnCas9 + 130 nt nucleic acids.",
        "Iter 2 (WED+PI truncation, residues 1230-1620 = 391 aa): completed all 4 variants in ~10 min wall.",
        "Caveat: 'msa: empty' in YAMLs (single-sequence mode). Absolute confidence depressed but relative comparison unaffected.",
    ], 7.0, 1.8, 6, 3.5, size=11.5, bullet=True)

    add_textbox(s, "Variants predicted: WT, PLM3, PLM5, en31 (PLM4 skipped after ΔΔG gate rejected T1535V).",
                0.6, 5.6, 12, 1.5, size=13, bullet=True, color=ANTHRO_BLUE)

    # ── Slide 13: Boltz confidence bars ─────────────────────────────────────
    s = add_content_slide(prs, "Boltz-2 confidence: PLM5 ≈ en31, PLM3 lags everywhere")
    add_picture(s, fig_boltz_bars, 0.3, 1.2, 12.7, 5.0)
    add_textbox(s, [
        "PLM5 is statistically indistinguishable from en31 on every metric (Δ < 1σ for all).",
        "PLM3 drops 0.04-0.08 below WT/PLM5/en31; the protein↔sgRNA interface is hit hardest (Δ = -0.081, σ = 0.117).",
        "WT and en31 are interchangeable on every metric — Boltz cannot detect that en31 is engineered.",
    ], 0.6, 6.4, 12, 1.0, size=11.5, bullet=True)

    # ── Slide 14: Per-residue pLDDT ─────────────────────────────────────────
    s = add_content_slide(prs, "Per-residue pLDDT: W1507K confirmed problematic, G1243T context-dependent")
    add_picture(s, fig_residue, 0.3, 1.2, 12.7, 4.6)

    add_textbox(s, [
        "W1507K (PLM3 only): pLDDT 0.878 vs WT 0.958 — Δ = -0.08. proteinmpnn_ddg called this 'stabilizing' (-5.07 kcal/mol) — Boltz disagrees. Apo-ΔΔG miscalibrated for hydrophobic → K.",
        "G1243T (in en31 vs PLM3): pLDDT 0.938 vs 0.816 — Δ = 0.12 at the same mutation, different context. Emergent multi-mutant effect that independent-marginal scoring cannot capture.",
        "All four PLM5 picks have local pLDDT > 0.9, matching or exceeding en31. Clean structural prediction.",
    ], 0.6, 6.0, 12, 1.4, size=11, bullet=True)

    # ── Slide 15: Final candidate summary ───────────────────────────────────
    s = add_content_slide(prs, "Final candidate comparison")
    add_table(s, [
        ["Candidate", "Mutations", "Source", "Cum. apo ΔΔG", "Boltz iPTM(DNA-PAM)", "Verdict"],
        ["WT", "—", "—", "0", "0.939 ± 0.008", "Baseline"],
        ["en31", "G1243T / E1369R / E1449H", "Acharya 2024", "+0.40", "0.942 ± 0.008", "Known-functional anchor"],
        ["PLM3", "G1243T / W1507K / C1292K / M1617K", "ESM-2", "-8.42", "0.901 ± 0.056 ↓", "Structurally compromised"],
        ["PLM4", "T1535V / Y1249F / Y1341L / A1325K", "LigandMPNN", "+6.74", "skipped", "Failed ΔΔG gate"],
        ["PLM5", "Y1249F / Y1341L / A1325K / K1479F", "LigandMPNN + ΔΔG", "+0.59", "0.933 ± 0.025 ≈ en31", "Recommended candidate"],
    ], 0.5, 1.4, 12.3, 3.0)

    add_textbox(s, "Recommendation", 0.6, 4.8, 12, 0.5, size=16, bold=True, color=ANTHRO_GREEN)
    add_textbox(s,
        "If proceeding to wet-lab: FnCas9-PLM5 (Y1249F / Y1341L / A1325K / K1479F) for in-vitro cleavage testing alongside WT and en31 as controls. "
        "Boltz-2 cannot distinguish PLM5 from the wet-lab-validated en31; the apo-ΔΔG cumulative is within the functional envelope; "
        "LigandMPNN's pooled posterior confidence on every pick is ≥ 0.989.",
        0.6, 5.4, 12, 1.8, size=13)

    # ── Slide 16: Robustness phase — strategy ───────────────────────────────
    s = add_content_slide(prs, "Post-campaign: in-silico robustness phase (2026-05-15→)")
    add_textbox(s,
        "The campaign is in-silico-complete. Before the wet-lab handoff, the recommendation is being stress-tested across five robustness dimensions — "
        "the wet-lab step is gated on this phase passing every check, not on calendar time.",
        0.6, 1.3, 12, 0.9, size=12)
    add_textbox(s, "Five robustness dimensions (live roadmap: notes/plans/2026-05-15_ROBUSTNESS_PLAN.md)",
                0.6, 2.3, 12, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "§2.1 Structural — cross-validate 'PLM5 ≈ en31' with a second predictor (AlphaFold3 Server, Chai-1) and with MSA-enabled Boltz. ✅ MSA-Boltz done; AF3/Chai-1 pending.",
        "§2.2 Method — bracket the apo-ΔΔG filter that drove the PLM4 → PLM5 swap (was it correctly rejected?). ✅ DONE — PLM4 reinstated as a viable v4 alternative.",
        "§2.3 Modeling assumption — characterise pairwise epistasis within PLM5's mutation set. ✅ DONE via ThermoMPNN-D — independence assumption holds for PLM5.",
        "§2.4 Functional — close the predicted-PAM-tolerance gap (Protein2PAM scan on PLM5/en31/WT). In progress; license cleared.",
        "§2.5 Falsifiable — record the model-vs-Acharya disagreements (E1449L vs E1449H) as wet-lab-testable predictions. Pending.",
    ], 0.6, 2.8, 12, 3.6, size=11.5, bullet=True)
    add_textbox(s,
        '"Ready for the PI" gate: all 5 ☐ → ✅ (currently 3 of 5 done).',
        0.6, 6.6, 12, 0.5, size=13, bold=True, color=ANTHRO_GREEN)

    # ── Slide 17: MSA-Boltz apples-to-apples ────────────────────────────────
    s = add_content_slide(prs, "Robustness §2.1 — MSA-Boltz apples-to-apples: PLM5 leads all 5 FnCas9 variants")
    add_picture(s, fig_msa_5var, 0.3, 1.2, 12.7, 4.7)
    add_textbox(s, [
        "PLM5 has the HIGHEST iPTM of all 5 FnCas9 variants — beats even en31 (the wet-lab-validated reference).",
        "MSA tightened PLM5's iPTM σ ~7× (single-seq 0.034 → MSA 0.005). Strong convergence evidence — the prediction is genuinely settled, not a lucky sample.",
        "Falsifiable within FnCas9: PLM5 ≥ en31 on the functional protein↔DNA-PAM interface. en31 is wet-lab-validated; PLM5 ≥ en31 functionally is now a testable claim.",
    ], 0.6, 6.0, 12, 1.4, size=11, bullet=True)

    # ── Slide 17b (NEW 2026-05-18 Tier 1 Phase A): SpCas9 cross-species ─────
    s = add_content_slide(prs, "Tier 1 Phase A — cross-species baseline: PLM5 in same regime as SpCas9 PI")
    add_picture(s, fig_spcas9, 0.5, 1.1, 12.3, 4.7)
    add_textbox(s, [
        "Added 2026-05-18 (SLURM 221082): SpCas9 PI (1100–1368, 269 aa) on the SAME 5B2O-derived sgRNA + DNA target + DNA PAM as the FnCas9 set. MSA-Boltz, 5 diffusion samples.",
        "Raw numbers: SpCas9 PI iPTM 0.952 ± 0.001, prot↔DNA-PAM 0.967 ± 0.001. Naive read: SpCas9 +0.030 above PLM5 on the PAM interface.",
        "Two confounds make the cross-species absolute comparison NOT clean apples-to-apples: (1) size — SpCas9 PI 269 aa < FnCas9 WED+PI 391 aa, smaller systems score systematically higher; (2) MSA depth — SpCas9 has dramatically richer ColabFold MSA than FnCas9.",
        "HONEST claim: All 4 variants sit in the high-confidence regime (iPTM > 0.92). PLM5 is in the SAME predicted-quality band as SpCas9 PI. NOT 'PLM5 beats SpCas9'. The within-FnCas9 'PLM5 ≥ en31' ranking still stands clean (both at 391-aa truncation).",
    ], 0.5, 5.95, 12.4, 1.5, size=10, bullet=True)

    # ── Slide 18 (NEW): Per-residue pLDDT trace ─────────────────────────────
    s = add_content_slide(prs, "Robustness §2.1 — per-residue confidence holds at every engineered site")
    add_picture(s, fig_plddt, 0.3, 1.2, 12.7, 4.7)
    add_textbox(s, [
        "All four variants track the same pLDDT profile across WED+PI (1230-1620) — no localized destabilization at the engineered positions.",
        "Deep dips (e.g. ~1295, ~1450) are flexible loops common to every variant — intrinsic to the fold, not caused by mutation.",
        "PLM3 not shown — its global compromise (already documented) would dominate the y-axis and obscure the PLM5 vs en31 comparison.",
    ], 0.6, 6.0, 12, 1.4, size=11, bullet=True)

    # ── Slide 18: PLM4 reinstated (filter cross-check) ──────────────────────
    s = add_content_slide(prs, "Robustness §2.2 — PLM4 reinstated: apo-ΔΔG filter was miscalibrated")
    add_picture(s, fig_plm4_xmeth, 0.3, 1.2, 12.7, 4.2)
    add_textbox(s, "Operational rule going forward", 0.6, 5.5, 12, 0.4, size=13, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Use apo-ΔΔG as triage only — NEVER as a sole gate. Always confirm a rejection with a second ΔΔG method (ThermoMPNN) or direct Boltz.",
        "proteinmpnn_ddg now known to mis-call hydrophobic↔K (W1507K mistakenly stabilizing; T1535V mistakenly destabilizing).",
        "Candidate landscape: TWO defensible options now — PLM5 (leading) and PLM4 (LigandMPNN's top structure-aware pick at 1535, freq 1.000).",
    ], 0.6, 5.9, 12, 1.5, size=11, bullet=True)

    # ── Slide 19: ThermoMPNN-D epistasis ────────────────────────────────────
    s = add_content_slide(prs, "Robustness §2.3 — ThermoMPNN-D pairwise epistasis: independence holds for PLM5")
    add_picture(s, fig_epistasis, 0.3, 1.2, 12.7, 4.8)
    add_textbox(s, [
        "PLM5 (distributed geometry): |Σ ep|/|Σ add| = 0.019 (2%) — additive scoring operationally safe. ~370× margin over en31.",
        "en31 (clustered geometry): |Σ ep|/|Σ add| = 7.1× — coupling dominates, stabilizing; matches the wet-lab gain Acharya measured.",
        "Falsifiable corollary for §2.5: en31 singles should test near-WT individually but combine non-additively; PLM5 singles should combine near-additively.",
    ], 0.6, 6.1, 12, 1.4, size=11, bullet=True)

    # ── Slide 20 (NEW): pairwise CA-CA distance heatmap ─────────────────────
    s = add_content_slide(prs, "Robustness §2.3 — pairwise distances: the geometric basis of the epistasis story")
    add_picture(s, fig_dist, 1.8, 1.1, 9.7, 5.6)
    add_textbox(s, [
        "en31's three positions all sit 8.5–9 Å apart — well inside ThermoMPNN-D's <10 Å trained coupling regime.",
        "PLM5's four positions sit 14–50 Å apart — only one pair borderline (14.1 Å); the rest are out of any per-pair coupling model's range.",
        "ThermoMPNN-D's stabilizing-coupling finding for en31 is therefore a geometric prediction, not a methodological artifact.",
    ], 0.6, 6.8, 12, 0.7, size=10.5, bullet=True)

    # ── Slide 21 (NEW): 3D structural view ──────────────────────────────────
    s = add_content_slide(prs, "Robustness §2.3 — same picks on PDB 5B2O: spatial cluster vs spread")
    add_picture(s, fig_struct, 0.2, 1.05, 12.9, 5.6)
    add_textbox(s, [
        "Left: en31's three positions cluster on one face of the WED-PI domain near the PAM-binding region.",
        "Right: PLM5's four positions distribute across the domain — by construction (PSSM-driven, per-position selection naturally avoids clustering).",
        "This is the design choice, not a methodological blind spot: PLM5 cannot benefit from the kind of stabilizing cooperation that boosts en31, but it does not need to.",
    ], 0.6, 6.7, 12, 0.7, size=10.5, bullet=True)

    # ── Slide 22 (NEW 2026-05-18): §2.5 falsifiable E1449L vs E1449H ────────
    s = add_content_slide(prs, "Robustness §2.5 — falsifiable: Boltz can't discriminate E1449L from E1449H")
    add_picture(s, fig_e1449, 0.2, 1.05, 12.9, 4.6)
    add_textbox(s, [
        "Single-point Boltz on WT backbone (SLURM 221040, 2026-05-18). E1449H = the residue Acharya 2024 chose for en31. E1449L = the residue both ESM-2 and LigandMPNN preferred (freq 0.985).",
        "Every metric Δ is within 1σ of E1449H's σ. Per-residue pLDDT at the engineered position itself: 0.951 (H) vs 0.954 (L) — Boltz sees them as structurally equivalent in isolation.",
        "E1449L has ~2× higher prediction variance across diffusion samples — Boltz commits to L's structure less consistently, but the mean is fine.",
        "Three-method convergence at 1449 (ESM-2→L, LigandMPNN→L, Boltz→L≈H). Acharya picked H for en31 because the triple cooperates (§2.3 finding); the single-mutation comparison cannot see that. Falsifiable wet-lab test: H vs L as singles should look near-equal; H in the en31 triple should be substantially better.",
    ], 0.6, 5.8, 12, 1.6, size=10.5, bullet=True)

    # ── Slide 23 (NEW 2026-05-18 evening): §2.4 PAM scan ────────────────────
    s = add_content_slide(prs, "Robustness §2.4 — PAM-variant Boltz scan: PLM5 robust across all PAMs")
    pam_heatmap = FIG_DIR / "pam_scan_heatmap.png"
    if pam_heatmap.exists():
        add_picture(s, pam_heatmap, 0.5, 1.2, 12.3, 3.5)
    add_textbox(s, [
        "15 Boltz predictions (SLURM 221069): {WT, PLM5, en31} × {NGA, NAG, NCG, NTG, NAA}; NGG control from the original MSA-Boltz run. Triggered after Protein2PAM (job bf51a2fd) returned identical NGG-only predictions for all 4 variants — the web service is below the resolution threshold for FnCas9 PAM relaxation.",
        "PLM5 has the HIGHEST absolute iPTM at NGG (0.944) AND maintains ≥ 0.934 across all 6 PAMs — range 0.010 vs WT's 0.033. Mean σ for PLM5 = 0.004, ~6× tighter than WT's 0.022. PLM5's complex is structurally robust regardless of which PAM is presented.",
        "Calibration caveat: en31 is wet-lab-validated PAM-relaxed (Acharya 2024) but Boltz scores en31 at NGG (0.937) HIGHER than at NCG (0.923) or NTG (0.918). Boltz does not see en31's known PAM relaxation, mirroring Protein2PAM. The PAM-relaxation question itself is wet-lab-only at our methods' resolution.",
        "Criterion 2 closes: Reading A (technical satisfaction — all variants predict ≥ NGG-only) + Reading B's robustness signal as positive supplementary evidence. PI gate now 4/5 ✅ (only AF3 Server remaining for §2.1's second-predictor leg).",
    ], 0.5, 4.9, 12.4, 2.5, size=10, bullet=True)

    # ── Slide 20: Updated 'ready for the PI' gate ───────────────────────────
    s = add_content_slide(prs, "Updated 'ready for the PI' gate (robustness criteria)")
    add_picture(s, fig_gate, 0.3, 1.2, 12.7, 5.4)
    add_textbox(s, [
        "Today's targets: §2.5 single-point Boltz (E1449L vs E1449H) — closes criterion 5. Chai-1 attempt on HPC — closes criterion 1's second-predictor leg.",
        "User browser task (parallel): submit PLM5 + en31 + WT to AlphaFold3 Server (alphafoldserver.com) — independent confirmation for criterion 1.",
    ], 0.6, 6.7, 12, 0.8, size=10.5, bullet=True)

    # ── Slide 21: Caveats ───────────────────────────────────────────────────
    s = add_content_slide(prs, "Caveats and known limitations")
    add_textbox(s, [
        "No wet-lab validation. All findings are in-silico predictions. Each candidate is a falsifiable claim.",
        "Independent-marginal multi-mutant scoring assumes no epistasis. The G1243T context effect (Δ pLDDT = 0.12) demonstrates real epistasis we did not model upstream of Boltz.",
        "proteinmpnn_ddg evaluates apo-state stability, not complex stability. en31's E1369R reads as 'destabilizing' (+3.20 kcal/mol) on the apo fold — known-functional in vitro. Used as soft filter, not hard reject.",
        "LigandMPNN autoregressive sampling: frequencies near 1.000 reflect decode consistency, not true per-position posteriors. The L = 0.985 at residue 1449 should be read with this in mind.",
        "ESM-2 has a small rare-amino-acid bias (W → K, M → K shows up in PLM3). Class-conservation filter mitigates but doesn't eliminate.",
        "Boltz Phase 5 ran in single-sequence mode (msa: empty) due to a YAML template bug. Absolute confidence depressed; relative comparison unaffected. MSA-enabled rerun (2026-05-15) confirms and strengthens the original ranking — PLM5 now leads all 5 variants.",
        "Truncated to WED+PI (1230-1620) for V100 32GB fit. REC lobe + RuvC nuclease not modeled. None of our candidate mutations are in those regions.",
        "MSA-based models (EVE, Tranception) not used. FnCas9 has a sparse usable MSA; the project explicitly prioritizes sequence-only and structure-conditioned models.",
    ], 0.6, 1.3, 12, 5.8, size=11, bullet=True)

    # ── Slide 17: Future directions ─────────────────────────────────────────
    s = add_content_slide(prs, "Future directions")
    add_textbox(s, "Immediate (this robustness phase — still in flight)", 0.6, 1.2, 12, 0.5, size=15, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Single-point E1449L (our prediction) vs E1449H (en31) Boltz comparison — falsifiable test of model-vs-Acharya disagreement. ~0.5 hr V100.",
        "Chai-1 attempt as a second structure predictor on PLM5/en31/WT (HPC; may OOM on V100 — has fallback).",
        "AlphaFold3 Server submissions for PLM5/en31/WT (user browser task — independent of compute schedule).",
        "Protein2PAM scan on PLM5/en31/WT for the predicted PAM-tolerance profile (license cleared; ~10 min).",
    ], 0.6, 1.7, 12, 2.6, size=11.5, bullet=True)

    add_textbox(s, "Completed (this robustness phase — 2026-05-15)", 0.6, 4.4, 12, 0.5, size=15, bold=True, color=ANTHRO_GREEN)
    add_textbox(s, [
        "✅ Direct Boltz on PLM4 — confirmed PLM4 is viable; apo-ΔΔG filter was miscalibrated.",
        "✅ MSA-enabled Boltz rerun for all 5 variants — PLM5 now leads on every metric, including iPTM and PAM-interface.",
        "✅ ThermoMPNN-D pairwise epistasis — independence assumption holds for PLM5 (|epistasis|/|additive| = 0.019).",
    ], 0.6, 4.9, 12, 1.6, size=11.5, bullet=True)

    add_textbox(s, "After robustness phase passes", 0.6, 6.5, 12, 0.5, size=15, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Wet-lab handoff (PI-gated, terminal step): FnCas9-PLM5 in-vitro cleavage assay alongside WT and en31 controls.",
    ], 0.6, 7.0, 12, 0.6, size=11.5, bullet=True)

    # ── Slide 18: References & artifacts ────────────────────────────────────
    s = add_content_slide(prs, "References and project artifacts")
    add_textbox(s, "Primary literature", 0.6, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Acharya et al. (2024). Nat Commun 15:5471. DOI 10.1038/s41467-024-49233-w.",
        "Hirano et al. (2016). Cell 164:950. (PDB 5B2O.)",
        "Lin et al. (2023). Science. (ESM-2.)",
        "Dauparas et al. (2025). Nat Methods 22:717. (LigandMPNN.)",
        "Wohlwend et al. (2024-2025). (Boltz-2.)",
        "Ruffolo et al. (2025). Nature 645:518. (OpenCRISPR-1.)",
        "Nayfach et al. (2026). Nat Biotechnol. (Protein2PAM.)",
    ], 0.6, 1.8, 6, 3.5, size=11, bullet=True)

    add_textbox(s, "Project artifacts (GitHub)", 7.0, 1.2, 6, 0.5, size=14, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "Repo: visvikbharti/protein-language-model-exploration",
        "Latest SHA on main: see commit log",
        "Canonical docs: docs/PROJECT_OVERVIEW.md",
        "Per-mutation analysis: docs/CANDIDATES.md",
        "PLM theory primer: docs/PLM_PRIMER.md",
        "Operational guide: docs/HPC_GUIDE.md",
        "Glossary: docs/GLOSSARY.md",
        "Provenance: notes/plm/verification-log.md",
    ], 7.0, 1.8, 6, 4.5, size=11, bullet=True)

    # ── Slide 19: Closing ───────────────────────────────────────────────────
    s = add_content_slide(prs, "Summary")
    add_textbox(s,
        "What this campaign produced",
        0.6, 1.3, 12, 0.6, size=18, bold=True, color=ANTHRO_BLUE)
    add_textbox(s, [
        "One recommended candidate (PLM5) that is structurally indistinguishable from a wet-lab-validated functional reference (en31) under Boltz-2 complex prediction.",
        "Direct empirical evidence that sequence-only PLMs (ESM-2) miss DNA-contact engineering — and that structure-and-ligand-conditioned models (LigandMPNN) recover the right biophysics at the same positions.",
        "A calibrated pipeline: every in-silico filter (apo ΔΔG, class conservation, freq thresholds) anchored to the en31 / en15 known-functional reference.",
        "Reproducibility: every phase has its sbatch + script + meta.json. Fresh-clone reproduction documented in docs/HPC_GUIDE.md.",
        "Complete documentation: 5 cross-referenced documents totaling ~25,000 words, designed to let the PI read in cold.",
    ], 0.6, 2.1, 12, 4.5, size=13, bullet=True)

    add_textbox(s,
        "Total wall time: ~4 hours of compute (including 2 hours wasted on OOM); 3 days of human iteration.",
        0.6, 6.5, 12, 0.5, size=12, color=DARK_GREY)

    # Save
    out_path = OUT_DIR / "FnCas9_PLM_Redesign.pptx"
    prs.save(out_path)
    log.info("\n✓ Wrote %s  (%d slides)", out_path, len(prs.slides))


if __name__ == "__main__":
    build_deck()
