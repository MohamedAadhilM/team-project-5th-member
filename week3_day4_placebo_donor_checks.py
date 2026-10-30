"""WEEK 3 - DAY 4 (Mohamed Aadhil M): Synthetic-control placebo/donor checks and alternate pre-period/donor-pool specifications.
Run:  python week3_day4_placebo_donor_checks.py
Out:  outputs/Week3_Day4_sc_specifications.csv, _in_space_placebo.csv, _in_time_placebo.csv, _placebo_ratio_plot.png, _spec_forest_plot.png
"""
import numpy as np
import pandas as pd
from week3_day2_synthetic_control import *   # noqa

PRE_WINDOWS = {"full 25 wks": None, "last 18 wks": slice(-18, None), "last 12 wks": slice(-12, None)}

def specifications(idx, pre_mean):
    rows = []
    pools = {"clean R07,R08 (frozen)": CLEAN, "all 6 controls": ALL_CONTROLS,
             "drop R02,R03": [c for c in ALL_CONTROLS if c not in ("R02", "R03")],
             "drop R05,R06": [c for c in ALL_CONTROLS if c not in ("R05", "R06")]}
    for c in CLEAN:                                    # leave-one-donor-out on the frozen pool
        pools[f"clean minus {c}"] = [d for d in CLEAN if d != c]
    for c in ALL_CONTROLS:                             # leave-one-donor-out on the extended pool
        pools[f"all 6 minus {c}"] = [d for d in ALL_CONTROLS if d != c]
    for unit in TREATED + ["TREATED_AVG"]:
        for pn, pool in pools.items():
            for wn, sl in PRE_WINDOWS.items():
                if wn != "full 25 wks" and not pn.startswith(("clean R07", "all 6 controls")):
                    continue                           # alternate windows only for the two main pools
                r = run_sc(idx, pre_mean, unit, pool, pre_slice=sl)
                rows.append((unit, pn, wn, round(r["pre_MSPE"], 1), round(r["skill"], 2), round(r["att_index"], 2),
                             round(r["att_level"], 2), round(r["att_pct"], 2),
                             ", ".join(f"{d}:{w:.2f}" for d, w in r["weights"].items() if w > 0.005)))
    return pd.DataFrame(rows, columns=["treated_unit", "donor_pool", "pre_window", "pre_MSPE", "skill_vs_constant", "ATT_index_pts",
                                       "ATT_rev_per_product_day", "ATT_pct", "weights"])

def in_space_placebo(idx, pre_mean):
    """Abadie-style: treat each control as if treated (donors = other controls), compare post/pre RMSPE ratios."""
    rows = []
    for unit in TREATED:
        r = run_sc(idx, pre_mean, unit, ALL_CONTROLS)
        rows.append((unit, unit, "treated", r["pre_RMSPE"], r["post_MSPE"] ** .5, r["post_MSPE"] ** .5 / r["pre_RMSPE"], r["att_index"]))
        for c in ALL_CONTROLS:
            sub = idx.rename(columns={c: "U"}); pm = pre_mean.rename({c: "U"})
            others = [d for d in ALL_CONTROLS if d != c]
            rp = run_sc(sub, pm, "U", others)
            rows.append((unit, c, "placebo", rp["pre_RMSPE"], rp["post_MSPE"] ** .5, rp["post_MSPE"] ** .5 / rp["pre_RMSPE"], rp["att_index"]))
    out = pd.DataFrame(rows, columns=["treated_unit", "unit", "type", "pre_RMSPE", "post_RMSPE", "ratio_post_pre", "post_gap_index_pts"])
    summ = []
    for unit, g in out.groupby("treated_unit"):
        t = g[g.type == "treated"].iloc[0]; pl = g[g.type == "placebo"]
        summ.append((unit, round(t.ratio_post_pre, 2), int((pl.ratio_post_pre >= t.ratio_post_pre).sum()) + 1, len(pl) + 1,
                     round((int((pl.ratio_post_pre >= t.ratio_post_pre).sum()) + 1) / (len(pl) + 1), 3),
                     round(np.mean(np.abs(pl.post_gap_index_pts) >= abs(t.post_gap_index_pts)), 2)))
    return out.round(3), pd.DataFrame(summ, columns=["treated_unit", "treated_ratio", "rank_from_top", "n_units", "placebo_p_value_ratio",
                                                     "share_placebos_with_|gap|>=treated"])

def in_time_placebo(idx, pre_mean, pool_name, pool, weeks_back=(12, 8)):
    pre, _ = split_pre_post(idx); rows = []
    for unit in TREATED + ["TREATED_AVG"]:
        y = treated_series(pre, unit).values
        for k in weeks_back:
            cut = len(pre) - k; w = fit_weights(y[:cut], pre[pool].values[:cut])
            syn = pre[pool].values @ w; test = slice(cut, min(cut + 8, len(pre)))
            gap = y[test] - syn[test]; train_rmspe = mspe(y[:cut], syn[:cut]) ** .5
            rows.append((unit, pool_name, str(pre.index[cut].date()), cut, len(gap), round(train_rmspe, 2), round(gap.mean(), 2),
                         round(abs(gap.mean()) / train_rmspe, 2), "false positive risk (|gap| > 1 train RMSPE)" if abs(gap.mean()) > train_rmspe else "ok"))
    return pd.DataFrame(rows, columns=["treated_unit", "donor_pool", "fake_start_week", "train_weeks", "eval_weeks", "train_RMSPE",
                                       "placebo_gap_index_pts", "gap_over_train_RMSPE", "reading"])

def main():
    OUT.mkdir(exist_ok=True)
    wk = weekly_panel(load_daily()); idx, pre_mean = to_index(wk)
    spec = specifications(idx, pre_mean); spec.to_csv(OUT / "Week3_Day4_sc_specifications.csv", index=False)
    isp, summ = in_space_placebo(idx, pre_mean); isp.to_csv(OUT / "Week3_Day4_in_space_placebo.csv", index=False)
    summ.to_csv(OUT / "Week3_Day4_in_space_placebo_summary.csv", index=False)
    itp = pd.concat([in_time_placebo(idx, pre_mean, "clean (frozen)", CLEAN), in_time_placebo(idx, pre_mean, "all 6", ALL_CONTROLS)])
    itp.to_csv(OUT / "Week3_Day4_in_time_placebo.csv", index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for a, unit in zip(ax, TREATED):
        g = isp[isp.treated_unit == unit]; cols = ["#d62728" if t == "treated" else "#999999" for t in g.type]
        a.bar(g.unit, g.ratio_post_pre, color=cols); a.set_title(f"{unit} vs placebo controls: post/pre RMSPE ratio"); a.tick_params(axis="x", rotation=45)
    ax[0].set_ylabel("RMSPE ratio"); plt.tight_layout(); plt.savefig(OUT / "Week3_Day4_placebo_ratio_plot.png", dpi=130); plt.close()
    s = spec[(spec.treated_unit == "TREATED_AVG") & (spec.pre_window == "full 25 wks") | (spec.treated_unit == "TREATED_AVG") & spec.donor_pool.isin(["clean R07,R08 (frozen)", "all 6 controls"])]
    s = s.iloc[::-1]; fig, ax = plt.subplots(figsize=(9, 6)); lab = s.donor_pool + " | " + s.pre_window
    ax.barh(range(len(s)), s.ATT_rev_per_product_day, color=["#1f77b4" if p.startswith("clean R07") else "#7f7f7f" for p in s.donor_pool])
    ax.set_yticks(range(len(s))); ax.set_yticklabels(lab, fontsize=7); ax.axvline(0, color="k", lw=.8)
    ax.set_xlabel("SC effect estimate, avg of R01+R04 (revenue per product-day)"); ax.set_title("Effect across donor-pool / pre-period specifications")
    plt.tight_layout(); plt.savefig(OUT / "Week3_Day4_spec_forest_plot.png", dpi=130); plt.close()
    print(summ.to_string(index=False)); print(itp.to_string(index=False))
    a = spec[spec.treated_unit == "TREATED_AVG"]; print("ATT range (TREATED_AVG, rev/product-day):", a.ATT_rev_per_product_day.min(), a.ATT_rev_per_product_day.max())

if __name__ == "__main__":
    main()
