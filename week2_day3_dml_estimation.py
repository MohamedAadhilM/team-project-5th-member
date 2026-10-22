"""WEEK 2 - DAY 3 (Member 5): Implement DML (cross-fitted partialling-out) treatment-effect estimation.
Run:  python week2_day3_dml_estimation.py
Out:  outputs/Week2_Day3_dml_estimate.csv, Week2_Day3_fold_estimates.csv, Week2_Day3_residuals_plot.png
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LassoCV
from week2_day2_dml_preprocessing import *   # noqa

def make_learner(name, seed=SEED):
    if name == "gbr":
        return GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.07, subsample=0.8, random_state=seed)
    if name == "rf":
        return RandomForestRegressor(n_estimators=100, min_samples_leaf=20, n_jobs=-1, random_state=seed)
    if name == "lasso":
        return LassoCV(cv=3, random_state=seed)
    raise ValueError(name)

def fit_dml(df, y=OUTCOME, w=CONFOUNDERS, k=K_FOLDS, learner=LEARNER, seed=SEED):
    """df: raw panel. Returns dict with theta, robust se, CI, p, residuals and per-fold thetas."""
    d = build_dml_dataset(df, y, w, k)
    X, Y, T = d[w].values.astype(float), d[y].values.astype(float), d[TREATMENT].values.astype(float)
    ry, rt = np.zeros(len(d)), np.zeros(len(d))
    for _, te in make_folds(d.date, k):
        tr = np.setdiff1d(np.arange(len(d)), te)
        ry[te] = Y[te] - make_learner(learner, seed).fit(X[tr], Y[tr]).predict(X[te])
        rt[te] = T[te] - make_learner(learner, seed).fit(X[tr], T[tr]).predict(X[te])
    denom = (rt ** 2).sum()
    theta = (rt * ry).sum() / denom if denom > 0 else np.nan
    psi = ry - theta * rt
    se = np.sqrt(((rt * psi) ** 2).sum()) / denom if denom > 0 else np.nan
    z = theta / se if se and se > 0 else np.nan
    folds = []
    for i, (_, te) in enumerate(make_folds(d.date, k)):
        den = (rt[te] ** 2).sum()
        folds.append((i, len(te), (rt[te] * ry[te]).sum() / den if den > 0 else np.nan, (rt[te] ** 2).mean()))
    return dict(theta=theta, se=se, ci_low=theta - 1.96 * se, ci_high=theta + 1.96 * se,
                p_value=2 * (1 - stats.norm.cdf(abs(z))) if np.isfinite(z) else np.nan, n=len(d),
                resid_T_var=(rt ** 2).mean(), r2_T=1 - (rt ** 2).sum() / ((T - T.mean()) ** 2).sum(),
                r2_Y=1 - (ry ** 2).sum() / ((Y - Y.mean()) ** 2).sum(), rt=rt, ry=ry, folds=folds)

def main():
    OUT.mkdir(exist_ok=True)
    r = fit_dml(load_panel())
    est = pd.DataFrame([{k: round(float(r[k]), 4) for k in ["theta", "se", "ci_low", "ci_high", "p_value", "resid_T_var", "r2_T", "r2_Y"]} | {"n": r["n"], "outcome": OUTCOME, "learner": LEARNER, "folds": K_FOLDS}])
    est.to_csv(OUT / "Week2_Day3_dml_estimate.csv", index=False)
    pd.DataFrame(r["folds"], columns=["fold", "n", "theta", "resid_T_var"]).round(4).to_csv(OUT / "Week2_Day3_fold_estimates.csv", index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].scatter(r["rt"], r["ry"], s=3, alpha=.25); xs = np.linspace(r["rt"].min(), r["rt"].max(), 10)
    ax[0].plot(xs, r["theta"] * xs, color="red", label=f"theta = {r['theta']:.2f}"); ax[0].legend()
    ax[0].set_xlabel("residual treatment"); ax[0].set_ylabel("residual revenue"); ax[0].set_title("Partialled-out revenue vs treatment")
    ax[1].hist(r["ry"], bins=60); ax[1].set_title("Outcome residuals (revenue)"); plt.tight_layout()
    plt.savefig(OUT / "Week2_Day3_residuals_plot.png", dpi=130); plt.close()
    print(est.to_string(index=False)); print(pd.DataFrame(r["folds"], columns=["fold", "n", "theta", "resid_T_var"]).round(3).to_string(index=False))

if __name__ == "__main__":
    main()
