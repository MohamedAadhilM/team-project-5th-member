"""WEEK 2 - DAY 1 (Member 5): Design the DML estimator.
Run:  python week2_day1_design_dml.py
Out:  outputs/Week2_Day1_dml_design.csv, outputs/Week2_Day1_task_contract.csv
"""
from pathlib import Path
import pandas as pd

OUT = Path(__file__).parent / "outputs"
DATA = Path(__file__).parent / "data" / "analysis_dataset.csv"   # Week 1 / M2 modeling panel

TREATMENT, OUTCOME = "pricing_treatment_flag", "revenue"
TREATED = ["R01", "R04"]
EXPOSED_CONTROLS = ["R02", "R03", "R05", "R06"]   # spillover-exposed (Week 1, region_network.csv)
CLEAN_DONORS = ["R07", "R08"]
INTERVENTION_DATE = "2026-07-01"
# Confounders from the Week 1 DAG adjustment set (time-varying ones; region constants are absorbed by FE)
CONFOUNDERS = ["demand_index", "seasonality_index", "holiday_flag", "weekend_flag", "local_event_flag",
               "weather_index", "marketing_spend", "competitor_price", "inventory_pressure",
               "promotion_flag", "post_period"]
NEVER_ADJUST = ["dynamic_price_multiplier", "selling_price", "units"]   # mediators
K_FOLDS, LEARNER, SEED = 5, "gbr", 0

DESIGN = [
    ("estimand", "ATT-style average effect of pricing_treatment_flag on revenue (partially linear model Y = theta*T + g(W) + e)", "Week 1 causal question"),
    ("treatment (T)", TREATMENT, "binary rollout flag; treated R01, R04 from 2026-07-01"),
    ("outcome (Y)", OUTCOME, "revenue = selling_price x units at date-region-product"),
    ("confounders (W)", ", ".join(CONFOUNDERS), "Week 1 adjustment set (time-varying part)"),
    ("never adjusted", ", ".join(NEVER_ADJUST), "mediators on the T -> Y path"),
    ("region FE handling", "within-transform Y, T and W by region x product", "T is fully determined by region x post, so region identity must be partialled out (positivity)"),
    ("nuisance learners", "E[Y|W] and E[T|W] with gradient boosting (alternatives: random forest, lasso)", "flexible, handles high-dimensional W"),
    ("cross-fitting", f"{K_FOLDS}-fold GroupKFold by ISO week", "avoids overfitting bias; keeps neighbouring days together"),
    ("estimator", "theta = sum(res_T * res_Y) / sum(res_T^2) (Robinson partialling-out)", "Neyman-orthogonal score"),
    ("standard error", "HC1-style robust sandwich on residual scores", "only 2 treated regions: cluster-robust SE would be unreliable"),
    ("sensitivity (Day 4)", "clean donors only, log outcome, learners, seeds, folds, placebo date", "spillover and stability checks"),
]
CONTRACT = [
    ("input", "data/analysis_dataset.csv", "date, region_id, product_id, revenue, pricing_treatment_flag, W columns", "from M2 panel / Week 1 provisional merge"),
    ("input", "confounder list", "from M3 (DAG review) - currently Week 1 adjustment set", "M3 -> M5"),
    ("output", "Week2_Day3_dml_estimate.csv", "theta, se, ci_low, ci_high, p_value, n", "M5 -> M6 (validation, final report)"),
    ("output", "Week2_Day4_dml_robustness.csv", "estimates under sensitivity variants", "M5 -> M6"),
    ("not needed", "synthetic control weights (M4)", "DML does not use SC weights; compared in M6 final report", "-"),
]

def main():
    OUT.mkdir(exist_ok=True)
    pd.DataFrame(DESIGN, columns=["item", "specification", "rationale"]).to_csv(OUT / "Week2_Day1_dml_design.csv", index=False)
    pd.DataFrame(CONTRACT, columns=["kind", "name", "content", "hand-off"]).to_csv(OUT / "Week2_Day1_task_contract.csv", index=False)
    print(pd.DataFrame(DESIGN, columns=["item", "specification", "rationale"]).to_string(index=False))

if __name__ == "__main__":
    main()
