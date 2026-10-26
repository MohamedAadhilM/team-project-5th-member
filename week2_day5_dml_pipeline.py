"""WEEK 2 - DAY 5 (Member 5): Finalize the DML pipeline - integrate, test, document.
Run:  python week2_day5_dml_pipeline.py
Out:  outputs/Week2_Day5_dml_final_results.csv, Week2_Day5_test_results.txt, Week2_Day5_dml_documentation.md
"""
import subprocess, sys
import numpy as np
import pandas as pd
from week2_day4_dml_review import *   # noqa

def run_pipeline(df):
    """validate -> preprocess -> cross-fit DML -> key robustness checks. Returns (checks, results)."""
    checks = validate_inputs(df)
    if not checks.passed.all():
        raise ValueError("input validation failed:\n" + checks[~checks.passed].to_string())
    res = pd.DataFrame([
        run_variant("MAIN: DML (gbr, 5 folds, all regions)", df),
        run_variant("clean donors only (R01,R04,R07,R08)", df[df.region_id.isin(TREATED + CLEAN_DONORS)]),
        run_variant("log(revenue) outcome", df.assign(log_revenue=np.log(df.revenue)), y="log_revenue"),
        run_variant("PLACEBO: fake start 2026-05-15", placebo_panel(df, "2026-05-15")),
    ])
    return checks, res

DOC = """# Week 2 - DML Estimation: Documentation (Member 5, Mohamed Aadhil M)

## Result
Main DML estimate of the effect of dynamic pricing on revenue (per region-day-product): **{theta:.2f}** (robust SE {se:.2f}, 95% CI [{lo:.1f}, {hi:.1f}], p = {p:.2f}, n = {n}).
The effect is **not statistically distinguishable from zero**. In log terms the estimate is {lth:.3f} (SE {lse:.3f}), i.e. about {lpct:.1f}% with a CI of roughly +/-{lci:.0f}%.

## Method (formulas)
Partially linear model: Y = theta*T + g(W) + e, T = m(W) + v.
1. Within-transform Y, T and time-varying W by region x product (fixed effects).
2. Cross-fit ({k}-fold GroupKFold by ISO week): learn E[Y|W] and E[T|W] on training folds, residualize on the held-out fold.
3. theta = sum(res_T * res_Y) / sum(res_T^2); SE = sqrt(sum((res_T*psi)^2)) / sum(res_T^2), psi = res_Y - theta*res_T.

## Inputs and outputs
- Input: `data/analysis_dataset.csv` (Week 1 provisional merge; replace with M2's pre/post panel). Required columns: date, region_id, product_id, revenue, pricing_treatment_flag, and the confounders in `week2_day1_design_dml.py`.
- Outputs: `outputs/Week2_Day3_dml_estimate.csv`, `Week2_Day4_dml_robustness.csv`, `Week2_Day4_stability_checks.csv`, `Week2_Day5_dml_final_results.csv`.
- Confounders (from the Week 1 DAG adjustment set): {w}. Mediators never adjusted: {m}.

## Checks run
{checks_md}

## Assumptions
- Conditional exchangeability given W and region x product fixed effects (parallel-trends-type assumption); unobserved time-varying shocks specific to treated regions are not controlled.
- Positivity: T is fully determined by region x time, so region identity is partialled out; identification comes from within-region change after 2026-07-01 relative to controls.
- SUTVA is violated by design (R02, R03, R05, R06 exposed to R01/R04); sensitivity run on clean donors R07/R08 only.

## Limitations
- Only 2 treated regions: SE is a robust (not cluster) SE and likely understated; fold-level estimates vary widely, so the point estimate is imprecise.
- Nuisance model R^2 for revenue is low ({r2y:.3f}), so the confounders explain little within-region variation.
- Spillover-adjusted (total market) effects are not estimated here.
- Provisional data: missing marketing spend / competitor price were median-imputed.
"""

def main():
    OUT.mkdir(exist_ok=True)
    df = load_panel()
    checks, res = run_pipeline(df)
    res.round(4).to_csv(OUT / "Week2_Day5_dml_final_results.csv", index=False)
    m, lg = res.iloc[0], res.iloc[2]
    stab = pd.read_csv(OUT / "Week2_Day4_stability_checks.csv") if (OUT / "Week2_Day4_stability_checks.csv").exists() else checks
    r2y = fit_dml(df)["r2_Y"]
    md = "\n".join(f"- {'PASS' if r.passed else 'FLAG'}: {r.check} ({r.detail})" for r in stab.itertuples())
    (OUT / "Week2_Day5_dml_documentation.md").write_text(DOC.format(
        theta=m.theta, se=m.se, lo=m.ci_low, hi=m.ci_high, p=m.p_value, n=int(m.n), lth=lg.theta, lse=lg.se,
        lpct=100 * lg.theta, lci=196 * lg.se, k=K_FOLDS, w=", ".join(CONFOUNDERS), m=", ".join(NEVER_ADJUST),
        checks_md=md, r2y=r2y))
    t = subprocess.run([sys.executable, "-m", "unittest", "test_dml_pipeline", "-v"], capture_output=True, text=True,
                       cwd=str(OUT.parent))
    (OUT / "Week2_Day5_test_results.txt").write_text(t.stdout + t.stderr)
    print(res[["variant", "theta", "se", "p_value"]].round(3).to_string(index=False)); print((t.stdout + t.stderr)[-300:])

if __name__ == "__main__":
    main()
