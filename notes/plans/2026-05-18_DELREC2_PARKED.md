# In-silico ΔREC-II FnCas9 panel — PARKED for now

**Authored:** 2026-05-18
**Status:** PARKED. Not started. To be re-evaluated after PLM5 wet-lab data lands.
**Predecessors:** [`2026-05-15_ROBUSTNESS_PLAN.md`](2026-05-15_ROBUSTNESS_PLAN.md), [`2026-05-16_TIER1_MD_PROXY_PLAN.md`](2026-05-16_TIER1_MD_PROXY_PLAN.md)

---

## Why this doc exists

User raised in conversation (2026-05-18): "can we also do these [Boltz cross-species comparisons] for REC-II-deleted versions of en1, and compare with WT en1, SpCas9, other enFnCas9 variants, WT FnCas9, PLM5, and ΔREC-II of PLM5?" Decision made same day to **park** the idea so the current PLM5 wet-lab handoff is not diluted, but to document it here so it is not lost.

## Why this is non-trivially worth doing later

**Lab context (key update 2026-05-18):** CSIR-IGIB lab is actively running ΔREC-II wet-lab work for FnCas9 variants in parallel with this PLM campaign. That means:
- There is potentially real wet-lab calibration data forthcoming for ΔREC-II FnCas9 variants — making in-silico ΔREC-II predictions directly testable rather than blind extrapolation.
- The in-silico campaign could prioritize *which* ΔREC-II variants the wet-lab arm tests next, providing a concrete cross-program contribution.
- This is fundamentally different from the "ΔREC-II as exploratory expansion" framing I initially used (and partially walked back here).

**Scientific value once wet-lab calibration is available:**
- AAV cargo limits make smaller Cas9 variants therapeutically attractive (precedent: mini-SpCas9 work, Trevino & Zhang 2021).
- FnCas9 already smaller than SpCas9 (1629 vs 1368 aa — wait, FnCas9 is LARGER). For AAV-relevance, ΔREC-II FnCas9 would matter only if FnCas9 has activity/specificity advantages that justify carrying it despite its size.
- A panel comparing {WT, en1, en31, PLM5} × {full-length, ΔREC-II} on Boltz interface metrics would tell us whether REC-II is computationally dispensable for predicted PAM-interface confidence — a falsifiable starting point.

## What an executed version would look like (sketch only)

**Variants:** 8–10. Full panel: WT FnCas9, en1 (need exact mutations from Acharya 2024), en31 (G1243T/E1369R/E1449H), PLM5 (Y1249F/Y1341L/A1325K/K1479F), plus ΔREC-II versions of each. Optional: SpCas9 full + SpCas9 ΔREC-II for cross-species robustness check.

**Splice points:** TBD — needs literature search + alignment with the lab's wet-lab REC-II deletion construct. Per Hirano 2016, FnCas9 REC2 ≈ residues 370–580 (approximate; needs verification with PDB 5B2O domain annotation). The exact splice points + any linker chosen by the wet-lab program should be matched in silico so the comparison is meaningful.

**Compute:** ~10 min Boltz per variant on V100, ~1-2 HPC hours total. Cheap.

**Outputs:** Extension of the MSA-Boltz comparison table; same per-residue pLDDT readout; PAM-scan style robustness check on the ΔREC-II variants.

**Calibration anchor:** the lab's wet-lab ΔREC-II data, when available. Without it, the in-silico results are uncalibrated extrapolation (same caveat as SpCas9 cross-species).

## Open decisions before starting

| Decision | Owner | Default |
|---|---|---|
| Splice points / linker for ΔREC-II | wet-lab program | match lab construct |
| en1 exact mutation set | literature (Acharya 2024) | verify from supplementary |
| Include SpCas9 ΔREC-II in panel? | user | NO unless cross-species claim needed |
| Run before or after PLM5 wet-lab? | user | AFTER — to use PLM5 wet-lab as the cross-validation |

## Why NOT now (current decision)

1. PI gate for PLM5 wet-lab handoff is 4/5 → 5/5 pending AF3 (today). Adding 8+ new ΔREC-II candidates before wet-lab on PLM5 would push the next PI conversation away from "test PLM5 in vitro" toward "we have 12 candidates, which?".
2. Without the lab's ΔREC-II wet-lab calibration data, our in-silico predictions for ΔREC-II would have no anchor — same situation as SpCas9 cross-species in §3.5.1, but worse (no published reference at all for FnCas9 truncations).
3. Cost is low (~2 HPC hours) but the doc/PPT/PI-brief update overhead is high — keep narrow focus on PLM5 wet-lab triggering.

## Re-evaluation trigger

Pick this back up when **either** of:
- PLM5 has wet-lab cleavage data (positive or negative result both inform next priorities).
- Lab's ΔREC-II program produces its first wet-lab data point on any FnCas9 variant — use that as calibration anchor.

Whichever comes first → reopen this doc, fill in splice points + en1 mutation set, run the Boltz panel.
