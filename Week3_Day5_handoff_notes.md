# Week 3 - Handoff Notes: Synthetic Control (Mohamed Aadhil M, Time-Series / Synthetic Control Analyst, branch feature/treatment-baseline)

## What was frozen (Day 1)
- Outcome: mean revenue per product-day per region, 7-day blocks anchored at 2026-07-01 (25 pre weeks 2026-01-07..06-30, 8 post weeks 07-01..08-25), indexed to each region's own pre-mean = 100.
- Treated: R01, R04 (and their average). Primary donor pool: R07, R08 (no spillover exposure). Alternate pool: all 6 controls (R02, R03, R05, R06 are spillover-exposed).
- MSPE = mean over weeks of (treated - synthetic)^2, in index points^2. Baselines: constant pre-mean, equal-weight donors.

## Results (primary pool = R07, R08; average of R01 and R04)
- Weights: R07:0.57, R08:0.43. Pre-treatment RMSPE 9.7 index points vs 7.1 for a constant baseline - **the synthetic control does not fit the pre-period better than a flat line** (skill -0.86).
- Post-period gap (effect estimate): 2.60 revenue per product-day (0.86% of the counterfactual). Across 16 specifications (donor pools, leave-one-donor-out, pre-windows) the estimate ranges from -3.9 to 9.4, spanning zero.
- In-space placebo: R01 ratio 0.92 (rank 4 of 7, p = 0.571); R04 ratio 1.14 (rank 3 of 7, p = 0.429). Neither is unusual relative to controls.
- In-time placebo (fake start dates inside the pre-period): all 12 checks passed (|gap| < 1 training RMSPE).
- Rolling validation: SC beat the constant baseline in 9 of 24 treated-unit x pool x fold tests (mean test MSPE SC 123.3 vs constant 95.4).

## Conclusion
Unit-level estimates point in opposite directions (R01 positive, R04 negative in every specification) and cancel in the average, which is what you expect from noise rather than a common pricing effect. R01 with the clean pool did beat the constant baseline in all 4 rolling folds (test MSPE 50.4 vs 78.3); R04 never did.

No credible synthetic-control evidence of a pricing effect either way. The effect estimate is small relative to noise, the fit is no better than a constant baseline, and placebo checks do not separate treated from control regions. Do **not** report a causal lift from this module; report it as inconclusive.

## Why the fit is poor
Daily revenue in R01/R04 is almost uncorrelated with every control region in the pre-period (|r| < 0.15), so no weighted average of controls tracks the treated series. Weekly smoothing helps but does not fix it.

## Spillover
The exposed controls (R02, R03, R05, R06) show post-period gaps within 0.15-0.35 of their pre-period RMSPE relative to the clean synthetic - no detectable spillover, but the test has little power given the noise.

## Region-level comparison with DML (Day 3)
SC and DML agree R04 is near zero/negative and insignificant. R01 DML is unstable with few controls (residual treatment variance < 0.01) and disagrees in sign with SC; treat R01 DML-vs-SC comparison as unresolved.

## Files and rerun
`python week3_day1_windows_baseline.py` -> `week3_day5_validation_handoff.py` in order (Day 3 needs ../week2_dml). Input: `data/analysis_dataset.csv` (provisional Week 1/2 panel - swap in the team's final panel, same columns). Tests: `python -m unittest test_week3_sc -v`.

## Limitations
Two treated regions, 25 pre weeks, 8 post weeks; no formal confidence interval for SC (placebo p-values have a floor of 1/7); convex weights without intercept cannot absorb level differences, handled by indexing; provisional data uses median imputation for missing marketing spend / competitor price.
