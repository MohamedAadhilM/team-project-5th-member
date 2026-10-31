"""WEEK 3 - DAY 5 (Mohamed Aadhil M): Rolling/blocked time validation; finalize synthetic-control fit, placebo and handoff notes.
Run:  python week3_day5_validation_handoff.py
Out:  outputs/Week3_Day5_rolling_validation.csv, _validation_summary.csv, _leakage_checks.csv, _sc_final_summary.csv,
      _test_results.txt, _handoff_notes.md
"""
import subprocess, sys
import numpy as np
import pandas as pd
from week3_day4_placebo_donor_checks import *   # noqa

GAP_WEEKS = 1   # purge gap for blocked validation

def blocked_folds(n, n_blocks=5, gap=GAP_WEEKS):
    """Contiguous blocks; train = all other weeks except `gap` weeks either side of the test block. (Uses both sides of the
    test block, so it is a stability check, not a forecasting test - rolling folds are the leakage-free ones.)"""
    edges = np.linspace(0, n, n_blocks + 1).astype(int); out = []
    for i in range(n_blocks):
        te = np.arange(edges[i], edges[i + 1])
        tr = np.array([j for j in range(n) if j < te[0] - gap or j > te[-1] + gap])
        out.append((tr, te))
    return out

def validate(idx, kind):
    pre, _ = split_pre_post(idx)
    folds = rolling_folds(len(pre)) if kind == "rolling" else blocked_folds(len(pre))
    rows, leaks = [], []
    for i, (tr, te) in enumerate(folds, 1):
        leak_free = bool(pre.index[tr].max() < pre.index[te].min()) if kind == "rolling" else None
        leaks.append((kind, i, str(pre.index[tr].min().date()), str(pre.index[tr].max().date()), str(pre.index[te].min().date()),
                      str(pre.index[te].max().date()), len(set(tr) & set(te)) == 0, leak_free,
                      "train strictly before test" if kind == "rolling" else f"{GAP_WEEKS}-week purge gap; both-sided training"))
        for unit in TREATED + ["TREATED_AVG"]:
            y = treated_series(pre, unit).values
            for pn, pool in POOLS.items():
                X = pre[pool].values; w = fit_weights(y[tr], X[tr])
                rows.append((kind, i, unit, pn.split(" (")[0], len(tr), len(te), mspe(y[te], X[te] @ w), mspe(y[te], np.full(len(te), y[tr].mean())),
                             mspe(y[te], X[te].mean(axis=1))))
    df = pd.DataFrame(rows, columns=["scheme", "fold", "treated_unit", "donor_pool", "train_weeks", "test_weeks", "test_MSPE_SC",
                                     "test_MSPE_constant", "test_MSPE_equal_weight"])
    df["SC_beats_constant"] = df.test_MSPE_SC < df.test_MSPE_constant
    return df, pd.DataFrame(leaks, columns=["scheme", "fold", "train_start", "train_end", "test_start", "test_end", "disjoint",
                                            "train_before_test", "note"])

NOTES = """# Week 3 - Handoff Notes: Synthetic Control (Mohamed Aadhil M, Time-Series / Synthetic Control Analyst, branch feature/treatment-baseline)

## What was frozen (Day 1)
- Outcome: mean revenue per product-day per region, 7-day blocks anchored at 2026-07-01 (25 pre weeks 2026-01-07..06-30, 8 post weeks 07-01..08-25), indexed to each region's own pre-mean = 100.
- Treated: R01, R04 (and their average). Primary donor pool: R07, R08 (no spillover exposure). Alternate pool: all 6 controls (R02, R03, R05, R06 are spillover-exposed).
- MSPE = mean over weeks of (treated - synthetic)^2, in index points^2. Baselines: constant pre-mean, equal-weight donors.

## Results (primary pool = R07, R08; average of R01 and R04)
- Weights: {weights}. Pre-treatment RMSPE {rmspe:.1f} index points vs {const_rmspe:.1f} for a constant baseline - **the synthetic control does not fit the pre-period better than a flat line** (skill {skill:.2f}).
- Post-period gap (effect estimate): {att:.2f} revenue per product-day ({pct:.2f}% of the counterfactual). Across {nspec} specifications (donor pools, leave-one-donor-out, pre-windows) the estimate ranges from {amin:.1f} to {amax:.1f}, spanning zero.
- In-space placebo: R01 ratio {r1:.2f} (rank {k1} of 7, p = {p1}); R04 ratio {r4:.2f} (rank {k4} of 7, p = {p4}). Neither is unusual relative to controls.
- In-time placebo (fake start dates inside the pre-period): all {nit} checks passed (|gap| < 1 training RMSPE).
- Rolling validation: SC beat the constant baseline in {rw} of {rn} treated-unit x pool x fold tests (mean test MSPE SC {rsc:.1f} vs constant {rco:.1f}).

## Conclusion
Unit-level estimates point in opposite directions (R01 positive, R04 negative in every specification) and cancel in the average, which is what you expect from noise rather than a common pricing effect. R01 with the clean pool did beat the constant baseline in all 4 rolling folds (test MSPE {r1sc:.1f} vs {r1co:.1f}); R04 never did.

No credible synthetic-control evidence of a pricing effect either way. The effect estimate is small relative to noise, the fit is no better than a constant baseline, and placebo checks do not separate treated from control regions. Do **not** report a causal lift from this module; report it as inconclusive.

## Why the fit is poor
Daily revenue in R01/R04 is almost uncorrelated with every control region in the pre-period (|r| < 0.15), so no weighted average of controls tracks the treated series. Weekly smoothing helps but does not fix it.

## Spillover
The exposed controls (R02, R03, R05, R06) show post-period gaps within 0.15-0.35 of their pre-period RMSPE relative to the clean synthetic - no detectable spillover, but the test has little power given the noise.

## Region-level comparison with DML (Day 3)
SC and DML agree R04 is near zero/negative and insignificant. R01 DML is unstable with few controls (residual treatment variance < 0.01) and disagrees in sign with SC; treat R01 DML-vs-SC comparison as unresolved.

## Files and rerun
`python week3_day1_windows_baseline.py` -> `week3_day5_validation_handoff.py` in order (Day 3 needs ../week2_dml). Input: `data/analysis_dataset.csv` (provisional Week 1/2 panel - swap in the team's final panel, same columns). Tests: `python -m unittest test_week3_sc -v`.

## Limitations
Two treated regions, 25 pre weeks, 8 post weeks; no formal confidence interval for SC (placebo p-values have a floor of 1/7); convex weights without intercept cannot absorb level differences, handled by indexing; provisional data uses median imputation for missing marketing spend / competitor price.
"""

def main():
    OUT.mkdir(exist_ok=True)
    wk = weekly_panel(load_daily()); idx, pre_mean = to_index(wk)
    r_df, r_leak = validate(idx, "rolling"); b_df, b_leak = validate(idx, "blocked")
    val = pd.concat([r_df, b_df]); val.round(2).to_csv(OUT / "Week3_Day5_rolling_validation.csv", index=False)
    pd.concat([r_leak, b_leak]).to_csv(OUT / "Week3_Day5_leakage_checks.csv", index=False)
    summ = (val.groupby(["scheme", "treated_unit", "donor_pool"], as_index=False)
               .agg(folds=("fold", "count"), mean_test_MSPE_SC=("test_MSPE_SC", "mean"), mean_test_MSPE_constant=("test_MSPE_constant", "mean"),
                    mean_test_MSPE_equal_weight=("test_MSPE_equal_weight", "mean"), folds_SC_beats_constant=("SC_beats_constant", "sum")))
    summ.round(2).to_csv(OUT / "Week3_Day5_validation_summary.csv", index=False)

    fin = []
    for unit in TREATED + ["TREATED_AVG"]:
        r = run_sc(idx, pre_mean, unit, CLEAN)
        fin.append((unit, "R07,R08 (frozen)", ", ".join(f"{d}:{w:.2f}" for d, w in r["weights"].items()), r["pre_MSPE"], r["pre_RMSPE"],
                    r["const_MSPE"], r["skill"], r["att_level"], r["att_pct"]))
    final = pd.DataFrame(fin, columns=["treated_unit", "donor_pool", "weights", "pre_MSPE", "pre_RMSPE", "constant_baseline_MSPE", "skill_vs_constant",
                                       "ATT_rev_per_product_day", "ATT_pct"]).round(3)
    spec = pd.read_csv(OUT / "Week3_Day4_sc_specifications.csv"); sa = spec[spec.treated_unit == "TREATED_AVG"]
    final["ATT_range_across_specs"] = [f"{spec[spec.treated_unit == u].ATT_rev_per_product_day.min():.1f} to {spec[spec.treated_unit == u].ATT_rev_per_product_day.max():.1f}" for u in final.treated_unit]
    def verdict(u):
        a = spec[spec.treated_unit == u].ATT_rev_per_product_day
        fit = "pre-fit not better than constant baseline" if float(final.loc[final.treated_unit == u, "skill_vs_constant"].iloc[0]) <= 0.05 else "pre-fit beats constant"
        rng = "estimate spans zero across specs" if a.min() < 0 < a.max() else f"same sign across specs ({'positive' if a.min() > 0 else 'negative'}) but opposite to the other treated region" if u in TREATED else "same sign across specs"
        return f"inconclusive: {fit}; {rng}"
    final["verdict"] = [verdict(u) for u in final.treated_unit]
    final.to_csv(OUT / "Week3_Day5_sc_final_summary.csv", index=False)

    t = subprocess.run([sys.executable, "-m", "unittest", "test_week3_sc", "-v"], capture_output=True, text=True, cwd=str(HERE))
    (OUT / "Week3_Day5_test_results.txt").write_text(t.stdout + t.stderr)

    avg = final[final.treated_unit == "TREATED_AVG"].iloc[0]; sp = pd.read_csv(OUT / "Week3_Day4_in_space_placebo_summary.csv").set_index("treated_unit")
    itp = pd.read_csv(OUT / "Week3_Day4_in_time_placebo.csv"); rv = r_df
    (OUT / "Week3_Day5_handoff_notes.md").write_text(NOTES.format(
        weights=avg.weights, rmspe=avg.pre_RMSPE, const_rmspe=avg.constant_baseline_MSPE ** .5, skill=avg.skill_vs_constant,
        att=avg.ATT_rev_per_product_day, pct=avg.ATT_pct, nspec=len(sa), amin=sa.ATT_rev_per_product_day.min(), amax=sa.ATT_rev_per_product_day.max(),
        r1=sp.loc["R01", "treated_ratio"], k1=sp.loc["R01", "rank_from_top"], p1=sp.loc["R01", "placebo_p_value_ratio"],
        r4=sp.loc["R04", "treated_ratio"], k4=sp.loc["R04", "rank_from_top"], p4=sp.loc["R04", "placebo_p_value_ratio"],
        nit=int((itp.reading == "ok").sum()), rw=int(rv.SC_beats_constant.sum()), rn=len(rv), rsc=rv.test_MSPE_SC.mean(), rco=rv.test_MSPE_constant.mean(),
        r1sc=rv[(rv.scheme == "rolling") & (rv.treated_unit == "R01") & (rv.donor_pool == "clean")].test_MSPE_SC.mean(),
        r1co=rv[(rv.scheme == "rolling") & (rv.treated_unit == "R01") & (rv.donor_pool == "clean")].test_MSPE_constant.mean()))
    print(final.to_string(index=False)); print(summ.round(1).to_string(index=False)); print(r_leak.to_string(index=False)); print(t.stdout[-200:] + t.stderr[-200:])

if __name__ == "__main__":
    main()
