# Week 2 - DML Estimation: Documentation (Member 5, Mohamed Aadhil M)

## Result
Main DML estimate of the effect of dynamic pricing on revenue (per region-day-product): **-0.31** (robust SE 11.64, 95% CI [-23.1, 22.5], p = 0.98, n = 11660).
The effect is **not statistically distinguishable from zero**. In log terms the estimate is 0.039 (SE 0.038), i.e. about 3.9% with a CI of roughly +/-7%.

## Method (formulas)
Partially linear model: Y = theta*T + g(W) + e, T = m(W) + v.
1. Within-transform Y, T and time-varying W by region x product (fixed effects).
2. Cross-fit (5-fold GroupKFold by ISO week): learn E[Y|W] and E[T|W] on training folds, residualize on the held-out fold.
3. theta = sum(res_T * res_Y) / sum(res_T^2); SE = sqrt(sum((res_T*psi)^2)) / sum(res_T^2), psi = res_Y - theta*res_T.

## Inputs and outputs
- Input: `data/analysis_dataset.csv` (Week 1 provisional merge; replace with M2's pre/post panel). Required columns: date, region_id, product_id, revenue, pricing_treatment_flag, and the confounders in `week2_day1_design_dml.py`.
- Outputs: `outputs/Week2_Day3_dml_estimate.csv`, `Week2_Day4_dml_robustness.csv`, `Week2_Day4_stability_checks.csv`, `Week2_Day5_dml_final_results.csv`.
- Confounders (from the Week 1 DAG adjustment set): demand_index, seasonality_index, holiday_flag, weekend_flag, local_event_flag, weather_index, marketing_spend, competitor_price, inventory_pressure, promotion_flag, post_period. Mediators never adjusted: dynamic_price_multiplier, selling_price, units.

## Checks run
- PASS: no missing/infinite estimates (0)
- PASS: residual treatment variance > 0.005 (positivity after partialling-out) (0.0062)
- FLAG: baseline CI excludes zero ([-23.1, 22.5])
- PASS: sign stable across variants (revenue level) (0 of 12 flip)
- PASS: seed stability: spread of theta <= 1 SE (1.58)
- FLAG: fold stability: fold thetas agree in sign (-29.6 to 54.0)
- PASS: placebo effects insignificant (p=0.27, p=0.74)

## Assumptions
- Conditional exchangeability given W and region x product fixed effects (parallel-trends-type assumption); unobserved time-varying shocks specific to treated regions are not controlled.
- Positivity: T is fully determined by region x time, so region identity is partialled out; identification comes from within-region change after 2026-07-01 relative to controls.
- SUTVA is violated by design (R02, R03, R05, R06 exposed to R01/R04); sensitivity run on clean donors R07/R08 only.

## Limitations
- Only 2 treated regions: SE is a robust (not cluster) SE and likely understated; fold-level estimates vary widely, so the point estimate is imprecise.
- Nuisance model R^2 for revenue is low (0.006), so the confounders explain little within-region variation.
- Spillover-adjusted (total market) effects are not estimated here.
- Provisional data: missing marketing spend / competitor price were median-imputed.
