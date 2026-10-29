"""WEEK 3 - DAY 3 (Mohamed Aadhil M): Compare region-level effects with synthetic-control patterns; flag disagreements
and spillover concerns.
Run:  python week3_day3_region_comparison.py
Out:  outputs/Week3_Day3_region_effect_comparison.csv, _spillover_screen.csv, _region_effects_plot.png
Needs ../week2_dml (Member 5 DML code from Week 2) for the region-level DML estimates.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "week2_dml"))
from week3_day2_synthetic_control import *   # noqa
from week2_day3_dml_estimation import fit_dml   # noqa  (Week 2 cross-fitted DML)

def region_dml(df, region, controls):
    r = fit_dml(df[df.region_id.isin([region] + controls)], learner="gbr")
    return r["theta"], r["se"], r["ci_low"], r["ci_high"], r["p_value"], r["resid_T_var"]

def main():
    OUT.mkdir(exist_ok=True)
    df = load_daily(); wk = weekly_panel(df); idx, pre_mean = to_index(wk)
    expo = df[df.post_period == 1].groupby("region_id").network_exposure.mean()

    rows = []
    for tr in TREATED:
        for pname, pool in POOLS.items():
            sc = run_sc(idx, pre_mean, tr, pool)
            ctrl = pool
            th, se, lo, hi, p, rtv = region_dml(df, tr, ctrl)
            sc_lvl = sc["att_level"]
            flags = []
            if np.sign(th) != np.sign(sc_lvl): flags.append("sign disagreement")
            if abs(th - sc_lvl) > 1.0 * se: flags.append("differ by > 1 DML SE")
            if rtv < 0.01: flags.append(f"DML unstable (residual treatment variance {rtv:.4f} < 0.01)")
            if lo <= 0 <= hi: flags.append("DML CI includes 0")
            if sc["skill"] <= 0.05: flags.append("SC pre-fit not better than constant")
            if any(d in EXPOSED for d in pool): flags.append("donors include spillover-exposed regions")
            rows.append((tr, pname, round(sc_lvl, 2), round(sc["att_pct"], 2), round(sc["pre_RMSPE"], 2), round(sc["skill"], 2),
                         round(th, 2), round(se, 2), round(lo, 1), round(hi, 1), round(p, 3), "; ".join(flags) or "agree"))
    cmp_ = pd.DataFrame(rows, columns=["treated_region", "donor_pool", "SC_ATT_rev_per_product_day", "SC_ATT_pct", "SC_pre_RMSPE_idx",
                                       "SC_skill_vs_constant", "DML_theta", "DML_se", "DML_ci_low", "DML_ci_high", "DML_p", "flags"])
    cmp_.to_csv(OUT / "Week3_Day3_region_effect_comparison.csv", index=False)

    srows = []
    for c in EXPOSED:
        sub = idx.rename(columns={c: "U"}); pm = pre_mean.rename({c: "U"})
        r = run_sc(sub, pm, "U", CLEAN)
        srows.append((c, round(float(expo[c]), 3), round(r["att_index"], 2), round(r["att_level"], 2), round(r["pre_RMSPE"], 2),
                      round(abs(r["att_index"]) / r["pre_RMSPE"], 2),
                      "possible spillover (|gap| > 1 pre-RMSPE)" if abs(r["att_index"]) > r["pre_RMSPE"] else "within normal pre-period noise"))
    scr = pd.DataFrame(srows, columns=["exposed_control", "post_mean_network_exposure", "post_gap_index_pts", "post_gap_rev_per_product_day",
                                       "pre_RMSPE_idx", "gap_over_RMSPE", "reading"])
    scr.to_csv(OUT / "Week3_Day3_spillover_screen.csv", index=False)

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4.5)); labels, k = [], 0
    for _, r in cmp_.iterrows():
        ax.bar(k - .18, r.SC_ATT_rev_per_product_day, .34, color="#1f77b4", label="Synthetic control" if k == 0 else None)
        ax.bar(k + .18, r.DML_theta, .34, color="#ff7f0e", yerr=1.96 * r.DML_se, capsize=3, label="DML (95% CI)" if k == 0 else None)
        labels.append(f"{r.treated_region}\n{r.donor_pool.split(' (')[0]}"); k += 1
    ax.axhline(0, color="k", lw=.8); ax.set_xticks(range(k)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("effect on revenue per product-day"); ax.set_title("Region-level effect: synthetic control vs DML"); ax.legend()
    plt.tight_layout(); plt.savefig(OUT / "Week3_Day3_region_effects_plot.png", dpi=130); plt.close()
    print(cmp_.to_string(index=False)); print(scr.to_string(index=False))

if __name__ == "__main__":
    main()
