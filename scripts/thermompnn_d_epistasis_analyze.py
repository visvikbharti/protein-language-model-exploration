"""Quantify pairwise epistasis from ThermoMPNN-D additive vs epistatic CSVs.

For the FnCas9 robustness phase (§2.3 of `notes/plans/2026-05-15_ROBUSTNESS_PLAN.md`),
evaluates whether the campaign's multi-mutant scoring's *independence assumption*
holds within the PLM5 and en31 mutation sets.

Epistasis term per pair = epistatic_ddG - additive_ddG, where:
  - additive_ddG comes from ThermoMPNN-D `--mode additive` (sum of singles, no coupling)
  - epistatic_ddG comes from ThermoMPNN-D `--mode epistatic` (uses the coupled head)
  - |epistasis| ≈ 0 → independent-marginal scoring is safe for that pair
  - |epistasis| > 0.3 kcal/mol → meaningful coupling, independence assumption breaks

Pairs are searched as the ThermoMPNN-D Mutation string format:
    <wt_aa><chain><position><mut_aa>:<wt_aa><chain><position><mut_aa>
e.g. "GA1243T:EA1369R" = G1243T paired with E1369R (chain A in both, lower pos first).

Pairs at CA-CA > ~10 Å are outside ThermoMPNN-D's trained coupling regime
(the model was trained on Megascale double-mutants where measured pairs are
mostly in physical contact). Their epistasis predictions degrade to ≈additive
(epistasis term ≈ 0). Non-zero epistasis at >10 Å is unlikely to be real signal
— treat it as the model defaulting to no-coupling for out-of-distribution pairs.

Inputs:
  --additive   ThermoMPNN-D `--mode additive` CSV
  --epistatic  ThermoMPNN-D `--mode epistatic` CSV
               (cols in both: index, ddG (kcal/mol), Mutation, CA-CA Distance)

Outputs (stdout):
  - Per-pair table across all 9 candidate pairs (3 en31 + 6 PLM5).
  - Cumulative within each variant.
  - Interpretation notes for missing/far pairs.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# Candidate pairs in ThermoMPNN-D Mutation string format (lower pos first).
# Mutations chosen to match the engineered variants:
#   en31  : G1243T / E1369R / E1449H            (3 pairs = C(3,2))
#   PLM5  : Y1249F / A1325K / Y1341L / K1479F   (6 pairs = C(4,2))
PAIRS: list[tuple[str, str, str]] = [
    ("en31", "GA1243T:EA1369R", "G1243T : E1369R"),
    ("en31", "GA1243T:EA1449H", "G1243T : E1449H"),
    ("en31", "EA1369R:EA1449H", "E1369R : E1449H"),
    ("PLM5", "YA1249F:AA1325K", "Y1249F : A1325K"),
    ("PLM5", "YA1249F:YA1341L", "Y1249F : Y1341L"),
    ("PLM5", "YA1249F:KA1479F", "Y1249F : K1479F"),
    ("PLM5", "AA1325K:YA1341L", "A1325K : Y1341L"),
    ("PLM5", "AA1325K:KA1479F", "A1325K : K1479F"),
    ("PLM5", "YA1341L:KA1479F", "Y1341L : K1479F"),
]

EPISTASIS_THRESHOLD = 0.3  # |epistasis| kcal/mol above this is flagged as "coupled"

# CA-CA distance below which ThermoMPNN-D's coupled head is in trained distribution.
TRAINED_DISTANCE_CUTOFF = 10.0


def lookup(csv_path: Path, pair_str: str) -> tuple[float, float] | None:
    """grep-based lookup — avoids loading multi-GB CSVs into pandas.

    Returns (ddG, CA_CA_distance) for the given pair string, or None if absent.
    The pair_str is searched as `,<pair_str>,` to anchor it inside the Mutation
    column (preceded and followed by commas in the CSV row).
    """
    result = subprocess.run(
        ["grep", "-F", f",{pair_str},", str(csv_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        # 0 = match, 1 = no match, anything else = error
        sys.stderr.write(f"grep error on {csv_path}: {result.stderr}\n")
        return None
    if not result.stdout.strip():
        return None
    # CSV columns: index, ddG (kcal/mol), Mutation, CA-CA Distance
    line = result.stdout.strip().split("\n")[0]
    fields = line.split(",")
    return float(fields[1]), float(fields[3])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--additive", type=Path, required=True,
                   help="Path to ThermoMPNN-D --mode additive output CSV.")
    p.add_argument("--epistatic", type=Path, required=True,
                   help="Path to ThermoMPNN-D --mode epistatic output CSV.")
    args = p.parse_args()

    print(f"[input] additive  : {args.additive}", file=sys.stderr)
    print(f"[input] epistatic : {args.epistatic}", file=sys.stderr)
    print(file=sys.stderr)

    print()
    print("=" * 96)
    print("Per-pair epistasis (epistatic - additive)")
    print("=" * 96)
    header = (f"{'variant':<6} {'pair':<22} {'CA-CA':>6} "
              f"{'additive':>10} {'epistatic':>10} {'epistasis':>10} {'regime':<14} {'flag':<14}")
    print(header)
    print("-" * 96)

    by_variant: dict[str, dict] = {}

    for variant, pair_str, desc in PAIRS:
        a = lookup(args.additive, pair_str)
        e = lookup(args.epistatic, pair_str)
        info = by_variant.setdefault(variant, {"sum_a": 0.0, "sum_e": 0.0, "n": 0, "missing": []})

        if a is None and e is None:
            print(f"{variant:<6} {desc:<22} {'—':>6} {'(absent from both CSVs — likely > --distance)':>62}")
            info["missing"].append(desc)
            continue
        if a is None:
            print(f"{variant:<6} {desc:<22} {e[1]:>6.2f} {'—':>10} {e[0]:>+10.3f} {'(no add)':>10}")
            continue
        if e is None:
            print(f"{variant:<6} {desc:<22} {a[1]:>6.2f} {a[0]:>+10.3f} {'—':>10} {'(no epi)':>10}")
            continue

        a_v, a_d = a
        e_v, _ = e
        eps = e_v - a_v
        regime = "TRAINED" if a_d <= TRAINED_DISTANCE_CUTOFF else "out-of-dist"
        flag = "**COUPLED**" if abs(eps) > EPISTASIS_THRESHOLD else "additive-OK"
        print(f"{variant:<6} {desc:<22} {a_d:>6.2f} "
              f"{a_v:>+10.3f} {e_v:>+10.3f} {eps:>+10.3f} {regime:<14} {flag:<14}")

        info["sum_a"] += a_v
        info["sum_e"] += e_v
        info["n"] += 1

    print()
    print("=" * 96)
    print("Cumulative within each variant (sum across pairs present in both CSVs)")
    print("=" * 96)
    print(f"{'variant':<6} {'n_pairs':>8} {'Σ additive':>12} {'Σ epistatic':>12} {'Σ epistasis':>12}")
    print("-" * 96)
    for variant, info in by_variant.items():
        if info["n"] == 0:
            continue
        delta = info["sum_e"] - info["sum_a"]
        print(f"{variant:<6} {info['n']:>8} "
              f"{info['sum_a']:>+12.3f} {info['sum_e']:>+12.3f} {delta:>+12.3f}")

    print()
    print("Notes:")
    print(f"  - |epistasis| > {EPISTASIS_THRESHOLD} kcal/mol is flagged as **COUPLED** "
          "(the independence assumption may not hold for that pair).")
    print(f"  - CA-CA > {TRAINED_DISTANCE_CUTOFF} Å is outside ThermoMPNN-D's trained coupling regime; "
          "epistasis predictions there degrade to ≈0 by construction, not measurement.")
    print("  - 'Σ epistasis' = total non-additive correction to the cumulative ΔΔG for that variant.")
    print("    If it's small relative to the cumulative additive total, the independence assumption "
          "the original campaign's scoring used is operationally safe for that variant.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
