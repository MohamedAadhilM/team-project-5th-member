# Causal Assumptions & Adjustment Set — Week 1

**Member 5:** Mohamed Aadhil M — Causal Inference Analyst
**Project:** Causal Inference & Synthetic Control Engine for Algorithmic Pricing
**Files:** `src/causal_graph.py`, `outputs/dag/causal_dag.dot`, `outputs/dag/causal_dag.png`

---

## 1. Causal question

> What is the causal effect on **revenue** of running **Adaptive Dynamic Pricing v1** instead of the existing pricing policy, in the treated regions (R01 North Metro, R04 West Metro) from 2026-07-01 to 2026-08-31?

| Item | Definition |
|---|---|
| Treatment | `pricing_treatment_flag` (0/1). Intensity (`dynamic_price_multiplier`, 0.06–0.08 in the calendar) is *how* treatment acts, not the treatment itself |
| Outcome | `revenue` = `selling_price × units`, aggregated at `date + region_id + product_id` |
| Unit | Region-day-product |
| Estimand (Week 1) | ATT: effect on treated regions during the treatment window |
| Pre-period | 2026-01-01 → 2026-06-30 (baseline learning). Post: 2026-07-01 → 2026-08-31 |

## 2. Variable roles

| Role | Variables | Adjust? |
|---|---|---|
| **Confounders** (pre-treatment common causes of assignment and revenue) | `region_income_index`, `post_period`, `demand_index`, `competitor_price`, `inventory_pressure` (minimal set) + precision covariates `seasonality_index`, `holiday_flag`, `weekend_flag`, `local_event_flag`, `weather_index`, `marketing_spend`, `promotion_flag` | **Yes** |
| **Mediators** (treatment → … → revenue) | `dynamic_price_multiplier`, `selling_price`, `units` | **No** — adjusting removes the very effect we want (the price → demand → revenue channel) |
| **Interference** | `neighbor_treatment` (latent, derived from `region_network.csv`), `network_exposure` | Not needed for backdoor identification; handle via control selection (see §5) |
| Outcome-only causes | `weather_index`, `holiday_flag`, `marketing_spend`, … | Optional; reduce variance |

`revenue` itself is a deterministic function of the mediators (`price × units`), so **never put price or units in the adjustment set** — the script verifies this: adding `selling_price` makes the set invalid.

## 3. DAG summary

19 nodes, 37 edges (acyclic, checked). Key structure:

- **Assignment:** `region_income_index`, `post_period`, `demand_index`, `competitor_price`, `inventory_pressure` → `pricing_treatment_flag`.
- **Mechanism:** `pricing_treatment_flag` → `dynamic_price_multiplier` → `selling_price` → `units` → `revenue`.
- **Demand block:** seasonality, holidays, weekends, events, weather, marketing → `demand_index` → `units`/`revenue`.
- **Spillover:** `neighbor_treatment` → `network_exposure` → `selling_price`/`units`/`revenue`.

Colours in the PNG: blue = treatment, green = outcome, yellow = confounders/covariates, orange = mediators, purple = interference (dashed = latent).

## 4. Adjustment set (verified by the backdoor criterion)

Checked in `causal_graph.py` via d-separation after removing the treatment's outgoing edges:

| Set | Valid backdoor set? |
|---|---|
| ∅ (no adjustment) | ❌ |
| Minimal: `{region_income_index, post_period, demand_index, competitor_price, inventory_pressure}` | ✅ |
| Full recommended (all 12 confounders/covariates) | ✅ |
| Full + `selling_price` | ❌ (mediator) |
| Full + `network_exposure` | ✅ (not a descendant of own treatment) |

**Use the full recommended set for DML/regression** (precision); use the minimal set for sensitivity comparisons. Descendants of treatment that must stay out: `dynamic_price_multiplier`, `selling_price`, `units`.

## 5. Spillover / interference — limitations

SUTVA (no interference) is **violated by design**. From `region_network.csv`:

| Link | Type | Weight | Consequence |
|---|---|---|---|
| R01 → R02 | Customer substitution | 0.35 | R02 is contaminated; strongest |
| R04 → R03 | Customer substitution | 0.30 | R03 contaminated |
| R01 → R05 | Shared logistics | 0.20 | R05 contaminated |
| R04 → R06 | Shared logistics | 0.15 | R06 contaminated |
| R02→R01, R03→R04 | Substitution | 0.10 | Back-flow onto treated regions (feedback) |
| R05→R07, R06→R08 | Logistics | 0.12 / 0.10 | Second-order exposure to R07/R08 |

Consistent with `market_context.csv`: in the post period mean `network_exposure` is R02 0.35, R03 0.30, R05 0.20, R06 0.15, and 0 for R07/R08 (so R07/R08 are the cleanest direct donors; R05→R07 and R06→R08 are second-order links not captured in `network_exposure`).

Implications:
1. **Naive control comparisons are biased.** If treatment pushes customers into/out of R02/R03, the controls' revenue moves too, and a treated-vs-control difference gets the sign/size wrong (substitution typically *inflates* the apparent lift or deflates it depending on direction — it cannot be assumed away).
2. **Prefer R07 and R08 as primary donors**; treat R02, R03, R05, R06 as exposed controls (sensitivity analysis / explicit exposure covariate). Handoff to Member 6 for the donor shortlist.
3. **Feedback edges** (R02→R01, R03→R04) mean treated regions are themselves partly exposed to control regions' behaviour; the DAG is a unit-level simplification and does not model this loop (it would be cyclic over time — needs a time-indexed DAG).
4. The estimate is a **direct effect under limited interference**, not a total market effect. Total market impact = direct + spillover and needs a separate network-aware estimand.

## 6. Other identification assumptions & risks

| Assumption | Status / risk |
|---|---|
| **Conditional exchangeability** | Treatment is assigned by region and date, not randomised. Treated regions differ at baseline (higher revenue ~323 vs ~256, higher demand 1.22 vs 1.01, higher income 1.07 vs 0.96 in the pre-period). Observed covariates help, but **unobserved region-level traits are not blocked** → region fixed effects / DiD / synthetic control (Week 2) are needed |
| **Positivity** | Weak: within treated regions pre-July, treatment = 0 always; post-July = 1 always; controls never treated. Overlap exists only across region × time, so identification leans on parallel-trends-type reasoning rather than covariate overlap |
| **Consistency** | Treatment intensity differs (R01 0.08, R04 0.06) → two versions of treatment; effect is an average across them. CATE by region in Week 3 |
| **Time confounding** | `post_period` is a perfect proxy for "after rollout"; common shocks in Jul–Aug (seasonality, holidays) must be absorbed by control regions or `seasonality_index` |
| **`competitor_price` timing** | Competitors may *react* to our new prices (then it is post-treatment). Use pre-treatment/lagged values or competitor price before rollout; otherwise it's a possible mediator/collider |
| **`inventory_pressure`** | May respond to treatment-driven sales; same caution — lag it |
| **`demand_index`** | Can be affected by spillover from neighbours; treated as exogenous context here |
| **Data quality** | Provisional merge drops duplicates, zero-unit, missing-price rows; missing marketing spend and competitor price imputed by median — replace with the team's cleaned dataset |
| **Quick check (not an estimate)** | Raw difference-in-differences on region-day-product revenue ≈ −7 (treated fell ~19 vs controls ~12). Unadjusted, contaminated by spillover — shown only to flag that the sign needs proper adjustment, **do not report it** |

## 7. DoWhy setup

```python
from dowhy import CausalModel
model = CausalModel(data=df[cols], treatment="pricing_treatment_flag",
                    outcome="revenue", graph=gml_string)   # gml from causal_graph.to_gml()
estimand = model.identify_effect(proceed_when_unidentifiable=True)
```

`neighbor_treatment` is latent and removed before building the `CausalModel`. Running `python src/causal_graph.py` after `pip install dowhy` prints the identified estimand and saves it to `reports/identified_estimand.txt`.

## 8. Handoffs

- **Member 6 (synthetic control):** prefer R07/R08 as primary donors; flag R02, R03, R05, R06 as exposed.
- **Member 3 (data quality) / Member 1:** swap in the cleaned merged file via `--merged`; required columns are the DAG node names in `causal_graph.py`.
- **Week 2:** use region FE/DiD or synthetic control to address unobserved region confounding; DML on the full adjustment set.
