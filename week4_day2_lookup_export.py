"""WEEK 4 - DAY 2 (Mohamed Aadhil M.): Export standardized counterfactual lookup/output files and align keys with app filters.
Run:  python week4_day2_lookup_export.py
Out:  outputs/Week4_Day2_counterfactual_lookup.csv, _filter_keys.csv, _key_alignment_checks.csv
"""
from week4_day1_counterfactual_contract import *   # noqa

def load_day1():
    return pd.read_pickle(HERE / "data" / "_S.pkl"), pd.read_pickle(HERE / "data" / "_F.pkl")

def alignment_checks(S, F, df):
    key = ["unit_id", "donor_pool", "week_start"]
    weeks = S.groupby(["unit_id", "donor_pool"]).week_start.nunique()
    app_regions, app_products = set(df.region_id), set(df.product_id)
    return pd.DataFrame([
        ("unique key (unit_id, donor_pool, week_start)", not S.duplicated(key).any(), int(S.duplicated(key).sum())),
        ("every unit has the same number of weeks (33 = 25 pre + 8 post)", bool((weeks == 33).all()), sorted(weeks.unique().tolist())),
        ("no missing values in actual/synthetic/gap", not S[["actual_revenue", "synthetic_revenue", "gap"]].isna().any().any(), int(S[["actual_revenue", "synthetic_revenue", "gap"]].isna().sum().sum())),
        ("gap = actual - synthetic", bool(np.allclose(S.gap, S.actual_revenue - S.synthetic_revenue)), "max abs diff %.2e" % float((S.gap - (S.actual_revenue - S.synthetic_revenue)).abs().max())),
        ("cumulative gap is 0 throughout the pre period", bool(S[S.period == "pre"].cumulative_gap.eq(0).all()), "-"),
        ("weeks start on 7-day grid anchored at 2026-07-01", bool((((pd.to_datetime(S.week_start) - w1.INTERVENTION).dt.days) % 7 == 0).all()), "-"),
        ("treated regions in app filter list", set(S.treated_unit) - {"TREATED_AVG"} <= app_regions, sorted(set(S.treated_unit))),
        ("products align with app product filter", set(S.product_id) - {"ALL"} == app_products, sorted(app_products)),
        ("every unit_id has a fit-metrics row", set(S.unit_id) == set(F.unit_id), len(set(F.unit_id))),
    ], columns=["check", "passed", "detail"])

def main():
    OUT.mkdir(exist_ok=True)
    S, F = load_day1(); df = pd.read_csv(DATA, parse_dates=["date"])
    S.round(3).to_csv(OUT / "Week4_Day2_counterfactual_lookup.csv", index=False)
    keys = F[["unit_id", "treated_unit", "product_id", "donor_pool", "pre_weeks", "post_weeks", "fit_grade", "skill_vs_constant"]].copy()
    keys["region_filter_value"] = keys.treated_unit.map(lambda u: "R01+R04 average" if u == "TREATED_AVG" else u)
    keys["product_filter_value"] = keys.product_id.map(lambda p: "All products" if p == "ALL" else p)
    keys["app_default"] = (keys.unit_id == "TREATED_AVG|ALL") & (keys.donor_pool == "clean")
    keys["interpretable"] = keys.fit_grade != "C"
    keys.round(3).to_csv(OUT / "Week4_Day2_filter_keys.csv", index=False)
    chk = alignment_checks(S, F, df); chk.to_csv(OUT / "Week4_Day2_key_alignment_checks.csv", index=False)
    print(chk.to_string(index=False)); print(len(S), "lookup rows")

if __name__ == "__main__":
    main()
