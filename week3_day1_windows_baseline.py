"""WEEK 3 - DAY 1 (Mohamed Aadhil M, Time-Series / Synthetic Control Analyst):
Freeze analysis windows and donor/control candidates; define time-aware folds and baseline MSPE.
Run:  python week3_day1_windows_baseline.py
Out:  outputs/Week3_Day1_analysis_windows.csv, _donor_candidates.csv, _time_aware_folds.csv, _baseline_mspe.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "outputs"
DATA = HERE / "data" / "analysis_dataset.csv"

INTERVENTION = pd.Timestamp("2026-07-01")
TREATED = ["R01", "R04"]
EXPOSED = ["R02", "R03", "R05", "R06"]      # spillover-exposed controls (Week 1 region_network.csv)
CLEAN = ["R07", "R08"]                      # no direct exposure -> FROZEN primary donor pool
ALL_CONTROLS = EXPOSED + CLEAN
BLOCK_DAYS = 7
FOLD_TRAIN_START_WEEKS, FOLD_TEST_WEEKS = 9, 4   # expanding-window rolling origin on the pre-period

def load_daily(path=DATA):
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def weekly_panel(df, outcome="revenue"):
    """Mean revenue per product-day, per region, averaged over 7-day blocks ANCHORED at the intervention date.
    Partial blocks are dropped. Returns (levels, week_start index, week number relative to intervention)."""
    daily = df.groupby(["date", "region_id"])[outcome].mean().unstack()
    rel = (daily.index - INTERVENTION).days
    blk = np.floor_divide(rel, BLOCK_DAYS)
    g = daily.groupby(blk)
    full = g.size() == BLOCK_DAYS
    wk = g.mean()[full]
    wk.index = [INTERVENTION + pd.Timedelta(days=int(b) * BLOCK_DAYS) for b in wk.index]
    wk.index.name = "week_start"
    return wk

def split_pre_post(wk):
    return wk[wk.index < INTERVENTION], wk[wk.index >= INTERVENTION]

def to_index(wk):
    """Index every region to its own pre-period mean = 100 (convex weights cannot match level differences)."""
    pre, _ = split_pre_post(wk)
    return wk / pre.mean() * 100, pre.mean()

def rolling_folds(n_pre, start=FOLD_TRAIN_START_WEEKS, test=FOLD_TEST_WEEKS):
    """Expanding-window folds: train = weeks [0, t), test = weeks [t, t+test). Never uses future data for training."""
    folds, t = [], start
    while t + test <= n_pre:
        folds.append((np.arange(0, t), np.arange(t, t + test)))
        t += test
    return folds

def mspe(y, yhat):
    """MSPE = (1/T) * sum_t (Y_treated,t - sum_j w_j * Y_j,t)^2  over the evaluation window (index points^2)."""
    return float(np.mean((np.asarray(y) - np.asarray(yhat)) ** 2))

def main():
    OUT.mkdir(exist_ok=True)
    df = load_daily()
    wk = weekly_panel(df); idx, pre_mean = to_index(wk); pre, post = split_pre_post(idx)
    win = pd.DataFrame([
        ("pre-treatment (learning)", pre.index.min().date(), (pre.index.max() + pd.Timedelta(days=6)).date(), len(pre), "weights, folds, baseline MSPE"),
        ("post-treatment (effect)", post.index.min().date(), (post.index.max() + pd.Timedelta(days=6)).date(), len(post), "gap between treated and synthetic"),
        ("dropped partial blocks", "2026-01-01..2026-01-05 and 2026-08-26..2026-08-31", "-", 0, "7-day blocks anchored at 2026-07-01"),
        ("outcome", "revenue (mean per product-day), 7-day mean, indexed to own pre-mean = 100", "-", 0, "daily series are too noisy: pre-period daily correlation between regions is ~0"),
    ], columns=["window", "start", "end", "n_weeks", "use"])
    win.to_csv(OUT / "Week3_Day1_analysis_windows.csv", index=False)

    expo = df[df.post_period == 1].groupby("region_id").network_exposure.mean().round(3)
    cand = pd.DataFrame([(r, "treated" if r in TREATED else "donor candidate",
                          expo.get(r, 0.0), "FROZEN primary pool" if r in CLEAN else ("alternate pool only (spillover-exposed)" if r in EXPOSED else "treated unit"),
                          round(float(pre_mean[r]), 2)) for r in sorted(idx.columns)],
                        columns=["region_id", "role", "post_mean_network_exposure", "decision", "pre_mean_revenue_per_product_day"])
    cand.to_csv(OUT / "Week3_Day1_donor_candidates.csv", index=False)

    rows = []
    for i, (tr, te) in enumerate(rolling_folds(len(pre)), 1):
        rows.append((i, pre.index[tr[0]].date(), pre.index[tr[-1]].date(), len(tr), pre.index[te[0]].date(), pre.index[te[-1]].date(),
                     len(te), pre.index[tr[-1]] < pre.index[te[0]]))
    pd.DataFrame(rows, columns=["fold", "train_start", "train_last_week", "train_weeks", "test_start", "test_last_week", "test_weeks",
                                "no_future_leakage"]).to_csv(OUT / "Week3_Day1_time_aware_folds.csv", index=False)

    rows = []
    for t in TREATED + ["TREATED_AVG"]:
        y = (pre[TREATED].mean(axis=1) if t == "TREATED_AVG" else pre[t]).values
        rows.append((t, "constant pre-mean (=100)", mspe(y, np.full_like(y, y.mean())), "naive floor: SC must beat this"))
        for nm, pool in (("equal-weight clean donors", CLEAN), ("equal-weight all 6 controls", ALL_CONTROLS)):
            rows.append((t, nm, mspe(y, pre[pool].mean(axis=1).values), "simple donor average"))
    base = pd.DataFrame(rows, columns=["treated_unit", "baseline", "pre_MSPE", "note"]); base["pre_RMSPE"] = base.pre_MSPE ** .5
    base.round(2).to_csv(OUT / "Week3_Day1_baseline_mspe.csv", index=False)
    print(win.to_string(index=False)); print(cand.to_string(index=False)); print(base.round(1).to_string(index=False))

if __name__ == "__main__":
    main()
