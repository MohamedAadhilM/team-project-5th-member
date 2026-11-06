"""WEEK 4 - DAY 5 (Mohamed Aadhil M.): Finalize actual-vs-synthetic visuals, pre-treatment fit evidence, cumulative gap outputs,
technical appendix, and the Power BI data package.
Run:  python week4_day5_final_package.py
Out:  outputs/Week4_Day5_*.{csv,png,md,txt}  and  outputs/powerbi/*.csv
"""
import subprocess, sys
from week4_day4_segment_validation import *   # noqa
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

PB = OUT / "powerbi"

def powerbi_tables(S, F, D, V):
    key = lambda u, p: u + "|" + p
    for t in (S, F, D): t["unit_pool_key"] = [key(u, p) for u, p in zip(t.unit_id, t.donor_pool)]
    V = V.copy(); V["unit_pool_key"] = V.unit_id.map(lambda u: key(u, "clean"))
    dim = F[["unit_pool_key", "unit_id", "treated_unit", "product_id", "donor_pool", "fit_grade"]].copy()
    dim["region_label"] = dim.treated_unit.map(lambda u: "R01+R04 average" if u == "TREATED_AVG" else u)
    dim["product_label"] = dim.product_id.map(lambda p: "All products" if p == "ALL" else p)
    dim["pool_label"] = dim.donor_pool.map({"clean": "Clean donors R07,R08 (frozen)", "all6": "All 6 controls (alternate)"})
    weeks = sorted(S.week_start.unique())
    date = pd.DataFrame({"week_start": weeks}); date["week_index"] = range(1, len(date) + 1)
    date["period"] = np.where(pd.to_datetime(date.week_start) < w1.INTERVENTION, "pre", "post")
    date["weeks_from_intervention"] = (pd.to_datetime(date.week_start) - w1.INTERVENTION).dt.days // 7
    date["month"] = pd.to_datetime(date.week_start).dt.strftime("%Y-%m")
    S2 = S.drop(columns=["treated_unit", "product_id", "donor_pool", "unit_id", "period"]).rename(columns={})
    tables = {"DimUnit": dim, "DimDate": date, "FactCounterfactual": S2.round(3),
              "FactFit": F.drop(columns=["unit_id", "treated_unit", "product_id", "donor_pool"]).round(3),
              "FactDonor": D.drop(columns=["unit_id", "treated_unit", "product_id", "donor_pool"]).round(3),
              "FactValidation": V.drop(columns=["unit_id", "treated_unit", "product_id", "fit_grade"]).round(3),
              "MetricSel": pd.DataFrame({"Metric": ["Actual revenue", "Synthetic revenue", "Gap (actual - synthetic)"], "Order": [1, 2, 3]})}
    for n, t in tables.items(): t.to_csv(PB / f"{n}.csv", index=False)
    return tables

APPENDIX = """# Technical appendix - synthetic-control counterfactual diagnostics (Week 4)

**Author:** Mohamed Aadhil M., Time-Series & Synthetic Control Analyst. **Project:** Causal Inference & Synthetic Control Engine for Algorithmic Pricing.

## 1. Data and frozen choices
- Source: the provisional analysis panel (date x region x product), not the team's final cleaned panel: rerun when that exists.
- Outcome: mean revenue per product-day, averaged in 7-day blocks anchored at 2026-07-01: {npre} pre weeks (2026-01-07 to 2026-06-30), {npost} post weeks (2026-07-01 to 2026-08-25). Partial blocks are dropped.
- Treated units: R01, R04 and their average. Primary donor pool: R07, R08 (no spillover exposure). Alternate pool: all 6 controls, including spillover-exposed R02, R03, R05, R06.
- Each series is indexed to its own pre-period mean = 100 for fitting, then converted back to revenue per product-day.

## 2. Method
- Weights: minimise mean over pre weeks of (treated - sum_j w_j * donor_j)^2 subject to w_j >= 0, sum w_j = 1. Post-period data are never used.
- Gap_t = actual_t - synthetic_t. Cumulative gap = running sum over post weeks of gap_t x 7 days (revenue per product).
- Pre-treatment fit: MSPE and RMSPE (index points); skill = 1 - MSPE_SC / MSPE_constant (constant = pre-period mean). Grade A >= 0.30, B >= 0.05, C < 0.05.
- Segment checks (Day 4): leave-one-donor-out, alternate donor pool, in-space placebo rank.

## 3. Results
- Fit grade A/B: {ab} of {n} units; grade C: {c} of {n}. Median skill {skill:.2f}.
- Average of R01 and R04, all products, clean pool: mean post gap {gap:.2f} per product-day ({pct:.2f}% of the counterfactual), cumulative gap {cum:.0f}.
- R01 and R04 have opposite-signed gaps ({g1:.1f} and {g4:.1f}) and offset in the average.
- Segment verdicts: {vc}.

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
"""

def main():
    OUT.mkdir(exist_ok=True); PB.mkdir(exist_ok=True)
    S, F = load_day1(); D = pd.read_pickle(HERE / "data" / "_D.pkl"); V = pd.read_csv(OUT / "Week4_Day4_segment_validation.csv")
    G = pd.read_csv(OUT / "Week4_Day3_gap_outputs.csv")
    fin = F[F.donor_pool == "clean"].merge(V[["unit_id", "sign_stable_across_pools", "placebo_rank_of_7", "verdict"]], on="unit_id").merge(
        G[G.donor_pool == "clean"][["unit_id", "mean_gap", "weeks_gap_positive", "gap_pct_of_synthetic"]], on="unit_id")
    fin[["unit_id", "pre_weeks", "post_weeks", "pre_RMSPE_index", "pre_RMSPE_pct_of_actual", "skill_vs_constant", "fit_grade", "pre_correlation", "mean_gap",
         "gap_pct_of_synthetic", "cumulative_gap_end", "weeks_gap_positive", "sign_stable_across_pools", "placebo_rank_of_7", "verdict"]].round(3).to_csv(
        OUT / "Week4_Day5_final_counterfactual_diagnostics.csv", index=False)
    S[S.donor_pool == "clean"][["unit_id", "week_start", "period", "actual_revenue", "synthetic_revenue", "gap", "cumulative_gap"]].round(3).to_csv(
        OUT / "Week4_Day5_cumulative_gap_outputs.csv", index=False)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for a, u in zip(ax, ["R01|ALL", "R04|ALL", "TREATED_AVG|ALL"]):
        d = S[(S.unit_id == u) & (S.donor_pool == "clean")]; x = pd.to_datetime(d.week_start); f = F[(F.unit_id == u) & (F.donor_pool == "clean")].iloc[0]
        a.plot(x, d.actual_revenue, label="actual"); a.plot(x, d.synthetic_revenue, "--", label="synthetic")
        a.axvline(w1.INTERVENTION, color="red", ls=":"); a.set_title(f"{u}: pre RMSPE {f.pre_RMSPE_pct_of_actual:.1f}% of revenue, grade {f.fit_grade}", fontsize=9)
        a.text(.02, .02, "Pre-fit no better than constant baseline:\ngap is not an effect estimate", transform=a.transAxes, fontsize=7, color="darkred"); a.tick_params(axis="x", rotation=45)
    ax[0].legend(); ax[0].set_ylabel("revenue per product-day"); plt.tight_layout(); plt.savefig(OUT / "Week4_Day5_final_actual_vs_synthetic.png", dpi=140); plt.close()
    c = F[F.donor_pool == "clean"].sort_values("skill_vs_constant"); fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(c.unit_id, c.skill_vs_constant, color="#c62828"); ax.axvline(0.05, color="orange", ls="--", label="grade B threshold (0.05)"); ax.axvline(0.30, color="green", ls="--", label="grade A threshold (0.30)")
    ax.set_xlabel("pre-treatment skill vs constant baseline"); ax.set_title("Pre-treatment fit evidence: every unit is below the usable threshold"); ax.tick_params(axis="y", labelsize=7); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(OUT / "Week4_Day5_pretreatment_fit_evidence.png", dpi=140); plt.close()

    a = fin[fin.unit_id == "TREATED_AVG|ALL"].iloc[0]
    (OUT / "Week4_Day5_technical_appendix.md").write_text(APPENDIX.format(
        npre=int(a.pre_weeks), npost=int(a.post_weeks), ab=int((fin.fit_grade != "C").sum()), c=int((fin.fit_grade == "C").sum()), n=len(fin),
        skill=fin.skill_vs_constant.median(), gap=a.mean_gap, pct=a.gap_pct_of_synthetic, cum=a.cumulative_gap_end,
        g1=fin[fin.unit_id == "R01|ALL"].mean_gap.iloc[0], g4=fin[fin.unit_id == "R04|ALL"].mean_gap.iloc[0],
        vc="; ".join(f"{k}: {v}" for k, v in fin.verdict.value_counts().items())))
    powerbi_tables(S.copy(), F.copy(), D.copy(), V)
    t = subprocess.run([sys.executable, "-m", "unittest", "test_week4", "-v"], capture_output=True, text=True, cwd=str(HERE))
    (OUT / "Week4_Day5_test_results.txt").write_text(t.stdout + t.stderr); print((t.stdout + t.stderr)[-350:])

if __name__ == "__main__":
    main()
