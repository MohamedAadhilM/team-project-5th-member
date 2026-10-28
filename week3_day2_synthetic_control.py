"""WEEK 3 - DAY 2 (Mohamed Aadhil M): Fit synthetic-control baseline; report donor weights, pre-treatment fit and MSPE.
Run:  python week3_day2_synthetic_control.py
Out:  outputs/Week3_Day2_sc_weights.csv, _sc_fit.csv, _sc_series.csv, _sc_fit_plot.png
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from week3_day1_windows_baseline import *   # noqa

def fit_weights(y, X):
    """Convex weights: min_w mean((y - Xw)^2)  s.t. w >= 0, sum(w) = 1  (SLSQP)."""
    k = X.shape[1]
    if k == 1:
        return np.ones(1)
    r = minimize(lambda w: np.mean((y - X @ w) ** 2), np.ones(k) / k, jac=lambda w: -2 * X.T @ (y - X @ w) / len(y),
                 bounds=[(0, 1)] * k, constraints={"type": "eq", "fun": lambda w: w.sum() - 1}, method="SLSQP",
                 options={"maxiter": 500, "ftol": 1e-12})
    w = np.clip(r.x, 0, None)
    return w / w.sum()

def treated_series(idx, unit):
    return idx[TREATED].mean(axis=1) if unit == "TREATED_AVG" else idx[unit]

def run_sc(idx, pre_mean, unit, pool, pre_slice=None):
    """Fit on the pre-period (optionally a sub-window), return dict with weights, MSPE, gap path and ATT."""
    pre, post = split_pre_post(idx)
    ypre = treated_series(pre, unit); ypost = treated_series(post, unit)
    fit_rows = np.arange(len(pre))[pre_slice] if pre_slice is not None else np.arange(len(pre))
    w = fit_weights(ypre.values[fit_rows], pre[pool].values[fit_rows])
    syn_pre, syn_post = pre[pool].values @ w, post[pool].values @ w
    gap_post = ypost.values - syn_post
    scale = (pre_mean[TREATED].mean() if unit == "TREATED_AVG" else pre_mean[unit]) / 100
    base = mspe(ypre.values[fit_rows], np.full(len(fit_rows), ypre.values[fit_rows].mean()))
    m = mspe(ypre.values[fit_rows], syn_pre[fit_rows])
    return dict(unit=unit, pool=pool, weights=dict(zip(pool, w)), pre_MSPE=m, pre_RMSPE=m ** .5, const_MSPE=base,
                skill=1 - m / base if base > 0 else np.nan, post_MSPE=mspe(ypost.values, syn_post),
                att_index=float(gap_post.mean()), att_level=float(gap_post.mean() * scale),
                att_pct=float(gap_post.mean() / syn_post.mean() * 100), gap_post=gap_post,
                syn_pre=syn_pre, syn_post=syn_post, ypre=ypre.values, ypost=ypost.values)

POOLS = {"clean (frozen primary)": CLEAN, "all 6 controls (alternate)": ALL_CONTROLS}

def main():
    OUT.mkdir(exist_ok=True)
    wk = weekly_panel(load_daily()); idx, pre_mean = to_index(wk); pre, post = split_pre_post(idx)
    wrows, frows, srows, res = [], [], [], {}
    for unit in TREATED + ["TREATED_AVG"]:
        for pname, pool in POOLS.items():
            r = run_sc(idx, pre_mean, unit, pool); res[(unit, pname)] = r
            for d, wt in r["weights"].items():
                wrows.append((unit, pname, d, round(wt, 3), "exposed" if d in EXPOSED else "clean"))
            frows.append((unit, pname, r["pre_MSPE"], r["pre_RMSPE"], r["const_MSPE"], r["skill"], r["post_MSPE"],
                          r["att_index"], r["att_level"], r["att_pct"],
                          "fit no better than constant baseline" if r["skill"] <= 0.05 else "fit beats constant baseline"))
            if pname.startswith("clean"):
                for i, d in enumerate(post.index):
                    srows.append((unit, d.date(), "post", r["ypost"][i], r["syn_post"][i], r["gap_post"][i]))
                for i, d in enumerate(pre.index):
                    srows.append((unit, d.date(), "pre", r["ypre"][i], r["syn_pre"][i], r["ypre"][i] - r["syn_pre"][i]))
    pd.DataFrame(wrows, columns=["treated_unit", "donor_pool", "donor", "weight", "donor_type"]).to_csv(OUT / "Week3_Day2_sc_weights.csv", index=False)
    fit = pd.DataFrame(frows, columns=["treated_unit", "donor_pool", "pre_MSPE", "pre_RMSPE", "constant_baseline_MSPE", "skill_vs_constant",
                                       "post_MSPE", "ATT_index_pts", "ATT_revenue_per_product_day", "ATT_pct_of_counterfactual", "fit_verdict"])
    fit.round(3).to_csv(OUT / "Week3_Day2_sc_fit.csv", index=False)
    pd.DataFrame(srows, columns=["treated_unit", "week_start", "period", "treated_index", "synthetic_index", "gap"]).round(3).to_csv(
        OUT / "Week3_Day2_sc_series.csv", index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4), sharey=True)
    for a, unit in zip(ax, TREATED + ["TREATED_AVG"]):
        r = res[(unit, "clean (frozen primary)")]; x = list(pre.index) + list(post.index)
        a.plot(x, np.r_[r["ypre"], r["ypost"]], label="treated"); a.plot(x, np.r_[r["syn_pre"], r["syn_post"]], "--", label="synthetic")
        a.axvline(INTERVENTION, color="red", ls=":"); a.set_title(f"{unit}: pre RMSPE {r['pre_RMSPE']:.1f}", fontsize=10); a.tick_params(axis="x", rotation=45)
    ax[0].legend(); ax[0].set_ylabel("revenue index (pre-mean = 100)"); plt.tight_layout(); plt.savefig(OUT / "Week3_Day2_sc_fit_plot.png", dpi=130); plt.close()
    print(fit.round(2).to_string(index=False)); print(pd.DataFrame(wrows, columns=["u", "p", "d", "w", "t"]).query("p.str.startswith('clean')").to_string(index=False))

if __name__ == "__main__":
    main()
