# Segment-level model validation notes (Week 4, Day 4)

Scope: 21 segments (treated unit x product, frozen clean donor pool R07/R08; all-6 pool and leave-one-donor-out as cross-checks).

## Result
- Fit grade A or B: 0 of 21 segments. Grade C (pre-treatment fit no better than a constant baseline): 21 of 21.
- Sign of the effect stable across donor pools and leave-one-donor-out: 12 of 21.
- In-space placebo p-value <= 0.29 (rank 1 or 2 of 7) among the 14 R01/R04 segments: 4.
- Verdict counts: Unsupported: pre-fit no better than constant baseline: 21.

## What this means for the report
- None of the segment-level gaps should be reported as a causal pricing effect. The synthetic control does not reproduce pre-treatment revenue in any segment.
- Segment gaps may be shown as descriptive actual-vs-counterfactual comparisons only, with the pre-treatment fit grade next to them.
- R01 and R04 point in opposite directions in most segments and cancel in the average, which is consistent with noise.
- Donor weights are concentrated on two clean regions (R07, R08) because exposed controls are excluded; the all-6 pool uses spillover-exposed donors and is a sensitivity check only.

## Limits of these checks
- Placebo p-values cannot go below 1/7 = 0.14 with 6 control regions.
- Product-level series are noisier than region-level series, so fit is worse for individual products.
- No confidence interval exists for synthetic-control gaps; uncertainty comes from the placebo ranks and the DML intervals (Week 2).
