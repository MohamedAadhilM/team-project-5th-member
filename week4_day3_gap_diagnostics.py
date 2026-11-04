"""WEEK 4 - DAY 3 (Mohamed Aadhil M.): Generate actual vs synthetic revenue, pointwise gap, cumulative gap and pre-treatment fit diagnostics.
Run:  python week4_day3_gap_diagnostics.py
Out:  outputs/Week4_Day3_gap_outputs.csv, _pretreatment_fit.csv, _actual_vs_synthetic.png, _gap_and_cumulative_gap.png
"""
from week4_day2_lookup_export import *   # noqa
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

def main():
    OUT.mkdir(exist_ok=True)
    S, F = load_day1()
    post = S[S.period == "post"]
    gaps = (post.groupby(["unit_id", "treated_unit", "product_id", "donor_pool"], as_index=False)
                .agg(mean_gap=("gap", "mean"), mean_actual=("actual_revenue", "mean"), mean_synthetic=("synthetic_revenue", "mean"),
                     cumulative_gap_end=("cumulative_gap", "last"), weeks_gap_positive=("gap", lambda g: int((g > 0).sum())), post_weeks=("gap", "size")))
    gaps["gap_pct_of_synthetic"] = gaps.mean_gap / gaps.mean_synthetic * 100
    gaps["fit_grade"] = gaps.set_index(["unit_id", "donor_pool"]).index.map(F.set_index(["unit_id", "donor_pool"]).fit_grade)
    gaps["reading"] = np.where(gaps.fit_grade == "C", "gap not interpretable: pre-fit no better than constant", "gap interpretable with caveats")
    gaps.round(3).to_csv(OUT / "Week4_Day3_gap_outputs.csv", index=False)
    fit = F[["unit_id", "donor_pool", "pre_weeks", "pre_MSPE_index", "pre_RMSPE_index", "pre_RMSPE_pct_of_actual", "constant_baseline_MSPE",
             "skill_vs_constant", "fit_grade", "pre_correlation", "max_abs_pre_gap"]].copy()
    fit["limitation"] = np.where(fit.fit_grade == "C", "Counterfactual does not track pre-treatment revenue; do not read the post gap as an effect", "-")
    fit.round(3).to_csv(OUT / "Week4_Day3_pretreatment_fit.csv", index=False)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4), sharey=False)
    for a, u in zip(ax, ["R01|ALL", "R04|ALL", "TREATED_AVG|ALL"]):
        d = S[(S.unit_id == u) & (S.donor_pool == "clean")]; x = pd.to_datetime(d.week_start)
        a.plot(x, d.actual_revenue, label="actual"); a.plot(x, d.synthetic_revenue, "--", label="synthetic (R07,R08)")
        a.axvline(w1.INTERVENTION, color="red", ls=":"); a.set_title(f"{u}  |  fit grade {F[(F.unit_id == u) & (F.donor_pool == 'clean')].fit_grade.iloc[0]}", fontsize=10); a.tick_params(axis="x", rotation=45)
    ax[0].set_ylabel("revenue per product-day"); ax[0].legend(); plt.tight_layout(); plt.savefig(OUT / "Week4_Day3_actual_vs_synthetic.png", dpi=130); plt.close()
    fig, ax = plt.subplots(2, 3, figsize=(16, 7), sharex="col")
    for j, u in enumerate(["R01|ALL", "R04|ALL", "TREATED_AVG|ALL"]):
        d = S[(S.unit_id == u) & (S.donor_pool == "clean")]; x = pd.to_datetime(d.week_start)
        ax[0, j].bar(x, d.gap, width=5, color=np.where(d.gap >= 0, "#2ca02c", "#d62728")); ax[0, j].axvline(w1.INTERVENTION, color="k", ls=":"); ax[0, j].set_title(f"{u}: weekly gap")
        ax[1, j].plot(x[d.period == "post"], d.cumulative_gap[d.period == "post"]); ax[1, j].axhline(0, color="k", lw=.8); ax[1, j].set_title("cumulative gap (post)")
        ax[1, j].tick_params(axis="x", rotation=45)
    plt.tight_layout(); plt.savefig(OUT / "Week4_Day3_gap_and_cumulative_gap.png", dpi=130); plt.close()
    print(gaps[(gaps.donor_pool == "clean") & (gaps.product_id == "ALL")][["unit_id", "mean_gap", "gap_pct_of_synthetic", "cumulative_gap_end", "weeks_gap_positive", "fit_grade"]].round(2).to_string(index=False))

if __name__ == "__main__":
    main()
