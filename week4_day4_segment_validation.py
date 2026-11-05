"""WEEK 4 - DAY 4 (Mohamed Aadhil M.): Cross-check synthetic-control fit and counterfactual diagnostics for the segments used in the report.
Run:  python week4_day4_segment_validation.py
Out:  outputs/Week4_Day4_segment_validation.csv, outputs/Week4_Day4_segment_validation_notes.md
"""
from week4_day2_lookup_export import *   # noqa

def segment_checks(df, F):
    rows, panels = [], product_panels(df)
    for uid, g in F[F.donor_pool == "clean"].groupby("unit_id"):
        unit, prod = g.treated_unit.iloc[0], g.product_id.iloc[0]; idx, pm = panels[prod]; main = g.iloc[0]
        att_main = main.ATT_revenue_per_product_day
        loo = {d: run_sc(idx, pm, unit, [d])["att_level"] for d in CLEAN}          # leave-one-donor-out on frozen pool
        att_all6 = run_sc(idx, pm, unit, ALL_CONTROLS)["att_level"]
        stable = all(np.sign(v) == np.sign(att_main) for v in list(loo.values()) + [att_all6])
        p, rank = np.nan, np.nan
        if unit != "TREATED_AVG":                                                    # in-space placebo (Abadie): each control treated in turn
            t = run_sc(idx, pm, unit, ALL_CONTROLS); rt = t["post_MSPE"] ** .5 / t["pre_RMSPE"]; ratios = []
            for c in ALL_CONTROLS:
                r = run_sc(idx.rename(columns={c: "U"}), pm.rename({c: "U"}), "U", [d for d in ALL_CONTROLS if d != c]); ratios.append(r["post_MSPE"] ** .5 / r["pre_RMSPE"])
            rank = int(sum(x >= rt for x in ratios)) + 1; p = rank / (len(ratios) + 1)
        D = pd.read_pickle(HERE / "data" / "_D.pkl"); d = D[(D.unit_id == uid) & (D.donor_pool == "clean")]
        if main.fit_grade == "C": verdict = "Unsupported: pre-fit no better than constant baseline"
        elif not stable: verdict = "Weak: effect sign changes with donor pool"
        elif p == p and p <= 0.29: verdict = "Supported with caveats"
        else: verdict = "Weak: placebo does not separate treated from controls"
        rows.append((uid, unit, prod, main.fit_grade, round(main.skill_vs_constant, 2), round(att_main, 2), round(min(loo.values()), 2), round(max(loo.values()), 2),
                     round(att_all6, 2), stable, rank, p, round(d.weight.max(), 2), int((d.donor_type == "exposed").sum()), verdict))
    return pd.DataFrame(rows, columns=["unit_id", "treated_unit", "product_id", "fit_grade", "skill_vs_constant", "ATT_main_clean_pool", "ATT_min_leave_one_donor_out",
                                       "ATT_max_leave_one_donor_out", "ATT_all6_pool", "sign_stable_across_pools", "placebo_rank_of_7", "placebo_p", "max_donor_weight",
                                       "exposed_donors_used", "verdict"])

NOTES = """# Segment-level model validation notes (Week 4, Day 4)

Scope: {n} segments (treated unit x product, frozen clean donor pool R07/R08; all-6 pool and leave-one-donor-out as cross-checks).

## Result
- Fit grade A or B: {ab} of {n} segments. Grade C (pre-treatment fit no better than a constant baseline): {c} of {n}.
- Sign of the effect stable across donor pools and leave-one-donor-out: {st} of {n}.
- In-space placebo p-value <= 0.29 (rank 1 or 2 of 7) among the {npl} R01/R04 segments: {pl}.
- Verdict counts: {vc}.

## What this means for the report
- None of the segment-level gaps should be reported as a causal pricing effect. The synthetic control does not reproduce pre-treatment revenue in any segment.
- Segment gaps may be shown as descriptive actual-vs-counterfactual comparisons only, with the pre-treatment fit grade next to them.
- R01 and R04 point in opposite directions in most segments and cancel in the average, which is consistent with noise.
- Donor weights are concentrated on two clean regions (R07, R08) because exposed controls are excluded; the all-6 pool uses spillover-exposed donors and is a sensitivity check only.

## Limits of these checks
- Placebo p-values cannot go below 1/7 = 0.14 with 6 control regions.
- Product-level series are noisier than region-level series, so fit is worse for individual products.
- No confidence interval exists for synthetic-control gaps; uncertainty comes from the placebo ranks and the DML intervals (Week 2).
"""

def main():
    OUT.mkdir(exist_ok=True)
    F = pd.read_pickle(HERE / "data" / "_F.pkl"); df = pd.read_csv(DATA, parse_dates=["date"])
    V = segment_checks(df, F); V.to_csv(OUT / "Week4_Day4_segment_validation.csv", index=False)
    pl = V[V.treated_unit != "TREATED_AVG"]
    (OUT / "Week4_Day4_segment_validation_notes.md").write_text(NOTES.format(
        n=len(V), ab=int((V.fit_grade != "C").sum()), c=int((V.fit_grade == "C").sum()), st=int(V.sign_stable_across_pools.sum()), npl=len(pl),
        pl=int((pl.placebo_p <= 0.29).sum()), vc="; ".join(f"{k}: {v}" for k, v in V.verdict.value_counts().items())))
    print(V[["unit_id", "fit_grade", "ATT_main_clean_pool", "sign_stable_across_pools", "placebo_rank_of_7", "verdict"]].to_string(index=False))

if __name__ == "__main__":
    main()
