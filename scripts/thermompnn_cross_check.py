"""Cross-check ThermoMPNN ΔΔG predictions against proteinmpnn_ddg's calls.

For the FnCas9 candidate positions, compares the two apo-ΔΔG methods side by
side and flags disagreements — particularly direction disagreements and the
substitutions that plm-scout identified as likely failure-mode boundaries:
  K→hydrophobic (e.g. K1479F): proteinmpnn_ddg failure-mode direction
  hydrophobic→K (e.g. W1507K): the previously-identified miscalibration

Inputs:
  --proteinmpnn-ddg  ddg.csv from hpc/slurm/03_proteinmpnn_ddg.sbatch
                     (peptoneltd LONG format: pre, post, pos, ...,
                      logit_difference_ddg)
  --thermompnn       ThermoMPNN_inference_<pdbid>.csv from
                     external/ThermoMPNN/analysis/custom_inference.py
                     (cols: Model, Dataset, ddG_pred, position, wildtype,
                      mutation, pdb, chain)

Outputs (stdout):
  - Per-mutation cross-check table for the candidate set.
  - Cumulative ΔΔG per variant under each method.
  - Direction-agreement flag, plus failure-mode notes.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


VARIANTS: dict[str, list[str]] = {
    "FnCas9-PLM5": ["Y1249F", "Y1341L", "A1325K", "K1479F"],
    "FnCas9-PLM4": ["T1535V", "Y1249F", "Y1341L", "A1325K"],
    "FnCas9-en31": ["G1243T", "E1369R", "E1449H"],
    "FnCas9-en15": ["E1603H"],
    "FnCas9-PLM3": ["G1243T", "W1507K", "C1292K", "M1617K"],
}

FLAGS: dict[str, str] = {
    "K1479F": "K->hydrophobic. proteinmpnn_ddg failure-mode direction; ThermoMPNN may correct.",
    "W1507K": "hyd->K. proteinmpnn_ddg called STABILIZING (-5.07); Boltz refuted (pLDDT 0.878 vs WT 0.958). Does ThermoMPNN agree with Boltz?",
    "T1535V": "PLM4's filter-rejecting call (proteinmpnn_ddg = +4.15). Sanity check.",
    "G1243T": "Recovered by both ESM-2 and LigandMPNN; en31's WED mutation.",
    "E1369R": "en31's PAM-contact charge swap; proteinmpnn_ddg ceiling = +3.20.",
}

# en31-calibrated stability envelope (project_context.md item 4 / verification log).
ENVELOPE_CUM = (-1.4, 0.4)
ENVELOPE_SINGLE_CEILING = 3.20


def parse_mut(mut: str) -> tuple[str, int, str]:
    return mut[0], int(mut[1:-1]), mut[-1]


def load_proteinmpnn_ddg(csv_path: Path) -> dict[tuple[int, str], float]:
    out: dict[tuple[int, str], float] = {}
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            pos = int(row["pos"])
            target = row["post"].strip()
            if row["pre"].strip() == target:
                continue
            out[(pos, target)] = float(row["logit_difference_ddg"])
    return out


def load_thermompnn(csv_path: Path) -> dict[tuple[int, str], tuple[float, str]]:
    """Returns (uniprot_pos, mut_aa) -> (ddg_kcal_per_mol, wildtype_aa).

    ThermoMPNN's custom_inference.py writes 0-indexed PDB residue numbers
    (position 0 = first resolved residue = the N-terminal Met for FnCas9).
    For FnCas9, PDB numbering = UniProt numbering, so position_uniprot = pos + 1.
    """
    out: dict[tuple[int, str], tuple[float, str]] = {}
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            pos = int(row["position"]) + 1
            mut = row["mutation"].strip()
            wt = row["wildtype"].strip()
            if mut == wt:
                continue
            out[(pos, mut)] = (float(row["ddG_pred"]), wt)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proteinmpnn-ddg", type=Path, required=True)
    parser.add_argument("--thermompnn", type=Path, required=True)
    args = parser.parse_args()

    pddg = load_proteinmpnn_ddg(args.proteinmpnn_ddg)
    tmpnn = load_thermompnn(args.thermompnn)

    print(f"Loaded proteinmpnn_ddg: {len(pddg):,} (pos,mut) entries from {args.proteinmpnn_ddg}")
    print(f"Loaded ThermoMPNN:      {len(tmpnn):,} (pos,mut) entries from {args.thermompnn}")
    print()

    header = (f"{'variant':<14} {'mutation':<8} {'pmpnn_ddg':>10} "
              f"{'thermompnn':>11} {'delta':>8} {'sign?':>6}  flag")
    print(header)
    print("-" * 65)

    cum_pddg: dict[str, float] = defaultdict(float)
    cum_tmpnn: dict[str, float] = defaultdict(float)
    direction_disagreements: list[str] = []

    invariant_errors: list[str] = []
    for variant, muts in VARIANTS.items():
        for mut in muts:
            expected_wt, pos, mut_aa = parse_mut(mut)
            p = pddg.get((pos, mut_aa))
            tm_entry = tmpnn.get((pos, mut_aa))
            flag = FLAGS.get(mut, "")
            if tm_entry is not None:
                t, tm_wt = tm_entry
                if tm_wt != expected_wt:
                    invariant_errors.append(
                        f"{mut}: ThermoMPNN reports wt={tm_wt!r} at pos {pos}, but mutation expects wt={expected_wt!r}"
                    )
            else:
                t, tm_wt = None, None
            if p is None or t is None:
                p_s = f"{p:>10.2f}" if p is not None else f"{'MISSING':>10}"
                t_s = f"{t:>11.2f}" if t is not None else f"{'MISSING':>11}"
                d_s = "       -"
                agree_s = f"{'-':>6}"
            else:
                d = t - p
                same_sign = (p > 0) == (t > 0)
                if not same_sign:
                    direction_disagreements.append(f"{variant} {mut}: pmpnn={p:+.2f} vs thermompnn={t:+.2f}")
                cum_pddg[variant] += p
                cum_tmpnn[variant] += t
                p_s, t_s, d_s = f"{p:>10.2f}", f"{t:>11.2f}", f"{d:>+8.2f}"
                agree_s = f"{'YES' if same_sign else '*NO*':>6}"
            print(f"{variant:<14} {mut:<8} {p_s} {t_s} {d_s} {agree_s}  {flag}")
        print()

    if invariant_errors:
        print("=== INVARIANT ERRORS (wildtype mismatch — position offset is wrong!) ===")
        for e in invariant_errors:
            print(f"  - {e}")
        print()

    print("=== Cumulative ΔΔG per variant (sum across the variant's mutations) ===")
    print(f"{'variant':<14} {'pmpnn_ddg':>10} {'thermompnn':>11} {'delta':>8}  in-envelope (pmpnn / thermompnn)")
    for variant in VARIANTS:
        cp = cum_pddg[variant]
        ct = cum_tmpnn[variant]
        d = ct - cp
        in_p = ENVELOPE_CUM[0] <= cp <= ENVELOPE_CUM[1]
        in_t = ENVELOPE_CUM[0] <= ct <= ENVELOPE_CUM[1]
        env_s = f"{'YES' if in_p else 'NO':>4} / {'YES' if in_t else 'NO':<4}"
        print(f"{variant:<14} {cp:>10.2f} {ct:>11.2f} {d:>+8.2f}  {env_s}")

    print()
    print(f"Reference: en31-calibrated cumulative envelope {ENVELOPE_CUM}; "
          f"single-position ceiling +{ENVELOPE_SINGLE_CEILING:.2f}.")
    if direction_disagreements:
        print()
        print("=== Direction disagreements (sign flips — strongest robustness signal) ===")
        for d in direction_disagreements:
            print(f"  - {d}")
    else:
        print()
        print("No direction disagreements among the candidate set. Methods broadly agree.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
