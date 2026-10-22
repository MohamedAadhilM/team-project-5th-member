"""WEEK 2 - DAY 2 (Member 5): DML preprocessing scaffold (validation, within-transform, cross-fit folds).
Run:  python week2_day2_dml_preprocessing.py
Out:  outputs/Week2_Day2_input_checks.csv, outputs/Week2_Day2_dml_dataset.csv
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from week2_day1_design_dml import *   # noqa

def load_panel(path=DATA):
    return pd.read_csv(path, parse_dates=["date"])

def validate_inputs(df, y=OUTCOME, w=CONFOUNDERS):
    need = ["date", "region_id", "product_id", y, TREATMENT] + list(w)
    checks = [("required columns present", all(c in df for c in need), ", ".join(c for c in need if c not in df) or "-")]
    present = [c for c in need if c in df]
    checks += [("no missing in modeling columns", int(df[present].isna().sum().sum()) == 0, int(df[present].isna().sum().sum())),
               ("treatment is binary", set(df[TREATMENT].dropna().unique()) <= {0, 1}, sorted(df[TREATMENT].unique().tolist())),
               ("unique date-region-product key", not df.duplicated(["date", "region_id", "product_id"]).any(),
                int(df.duplicated(["date", "region_id", "product_id"]).sum())),
               ("revenue >= 0", bool((df[y] >= 0).all()), float(df[y].min())),
               ("treated regions only treated after intervention",
                bool(df[df[TREATMENT] == 1].date.min() >= pd.Timestamp(INTERVENTION_DATE)), str(df[df[TREATMENT] == 1].date.min().date())),
               ("no mediators in confounder set", not set(w) & set(NEVER_ADJUST), "-"),
               ("pre and post periods both present", bool(df.post_period.nunique() == 2), df.groupby("post_period").size().to_dict())]
    return pd.DataFrame(checks, columns=["check", "passed", "detail"])

def within_transform(df, y=OUTCOME, w=CONFOUNDERS):
    """Remove region x product means (fixed effects) from Y, T and time-varying W (post_period kept as is)."""
    d = df.copy()
    g = d.region_id.astype(str) + "_" + d.product_id.astype(str)
    cols = [y, TREATMENT] + [c for c in w if c != "post_period"]
    d[cols] = d[cols] - d.groupby(g)[cols].transform("mean")
    return d

def make_folds(dates, k=K_FOLDS):
    """Cross-fitting folds: GroupKFold by ISO week. Returns list of (train_idx, test_idx)."""
    wk = pd.Series(dates).dt.isocalendar().week.values
    return list(GroupKFold(k).split(np.zeros(len(wk)), groups=wk))

def build_dml_dataset(df, y=OUTCOME, w=CONFOUNDERS, k=K_FOLDS):
    d = within_transform(df, y, w)
    fold = np.zeros(len(d), dtype=int)
    for i, (_, te) in enumerate(make_folds(d.date, k)):
        fold[te] = i
    d["fold"] = fold
    return d

def main():
    OUT.mkdir(exist_ok=True)
    df = load_panel()
    chk = validate_inputs(df); chk.to_csv(OUT / "Week2_Day2_input_checks.csv", index=False)
    d = build_dml_dataset(df)
    d[["date", "region_id", "product_id", OUTCOME, TREATMENT] + CONFOUNDERS + ["fold"]].to_csv(OUT / "Week2_Day2_dml_dataset.csv", index=False)
    print(chk.to_string(index=False)); print("dataset", d.shape, "| rows per fold:", d.fold.value_counts().sort_index().to_dict())

if __name__ == "__main__":
    main()
