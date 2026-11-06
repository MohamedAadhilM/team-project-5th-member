# Technical appendix - synthetic-control counterfactual diagnostics (Week 4)

**Author:** Mohamed Aadhil M., Time-Series & Synthetic Control Analyst. **Project:** Causal Inference & Synthetic Control Engine for Algorithmic Pricing.

## 1. Data and frozen choices
- Source: the provisional analysis panel (date x region x product), not the team's final cleaned panel: rerun when that exists.
- Outcome: mean revenue per product-day, averaged in 7-day blocks anchored at 2026-07-01: 25 pre weeks (2026-01-07 to 2026-06-30), 8 post weeks (2026-07-01 to 2026-08-25). Partial blocks are dropped.
- Treated units: R01, R04 and their average. Primary donor pool: R07, R08 (no spillover exposure). Alternate pool: all 6 controls, including spillover-exposed R02, R03, R05, R06.
- Each series is indexed to its own pre-period mean = 100 for fitting, then converted back to revenue per product-day.

## 2. Method
- Weights: minimise mean over pre weeks of (treated - sum_j w_j * donor_j)^2 subject to w_j >= 0, sum w_j = 1. Post-period data are never used.
- Gap_t = actual_t - synthetic_t. Cumulative gap = running sum over post weeks of gap_t x 7 days (revenue per product).
- Pre-treatment fit: MSPE and RMSPE (index points); skill = 1 - MSPE_SC / MSPE_constant (constant = pre-period mean). Grade A >= 0.30, B >= 0.05, C < 0.05.
- Segment checks (Day 4): leave-one-donor-out, alternate donor pool, in-space placebo rank.

## 3. Results
- Fit grade A/B: 0 of 21 units; grade C: 21 of 21. Median skill -0.55.
- Average of R01 and R04, all products, clean pool: mean post gap 2.60 per product-day (0.86% of the counterfactual), cumulative gap 146.
- R01 and R04 have opposite-signed gaps (19.4 and -13.7) and offset in the average.
- Segment verdicts: Unsupported: pre-fit no better than constant baseline: 21.

## 4. Interpretation
Because the synthetic control does not track pre-treatment revenue better than a flat baseline in any unit, post-period gaps are descriptive comparisons, not estimates of a pricing effect. Report as inconclusive. DML intervals (Week 2) and placebo ranks (Week 3 and 4) agree: the effect is not distinguishable from zero.

## 5. Limitations
- Two treated regions, 25 pre weeks and 8 post weeks; no confidence interval for SC; placebo p-values have a floor of 1/7.
- Daily revenue of the treated regions is nearly uncorrelated with the controls in the pre-period.
- Spillover: exposed controls are excluded from the primary pool but affect the alternate pool.
- Median imputation in the provisional data.
- Scenario inputs in the app are what-if inputs, not causal forecasts.

## 6. Reproduction
Run the five Week 4 scripts in order (Day 1 to Day 5); the Week 3 folder must sit beside this one. Tests: `python -m unittest test_week4 -v`. Power BI tables are in `outputs/powerbi/`.
