"""WEEK 2 - DAY 4 (Member 5): Review DML estimates - robustness, missing/unstable results, placebo.
Run:  python week2_day4_dml_review.py
Out:  outputs/Week2_Day4_dml_robustness.csv, Week2_Day4_stability_checks.csv, Week2_Day4_estimates_forest.png
"""
import numpy as np
import pandas as pd
from week2_day3_dml_estimation import *   # noqa

def run_variant(name, df, **kw):
    r = fit_dml(df, **kw)
    fold_th = [f[2] for f in r["folds"]]
    return dict(variant=name, theta=r["theta"], se=r["se"], ci_low=r["ci_low"], ci_high=r["ci_high"], p_value=r["p_value"],
                n=r["n"], resid_T_var=r["resid_T_var"], fold_theta_min=np.nanmin(fold_th), fold_theta_max=np.nanmax(fold_th))

def placebo_panel(df, fake_date):
    p = df[df.post_period == 0].copy()
    p[TREATMENT] = (p.region_id.isin(TREATED) & (p.date >= fake_date)).astype(int)
    p["post_period"] = (p.date >= fake_date).astype(int)
    return p

def run_all(df):
    rows = [run_variant("baseline (gbr, 5 folds, all regions)", df)]
    rows.append(run_variant("clean donors only (R01,R04,R07,R08)", df[df.region_id.isin(TREATED + CLEAN_DONORS)]))
    rows.append(run_variant("drop strongest-exposed controls (R02,R03)", df[~df.region_id.isin(["R02", "R03"])]))
    rows.append(run_variant("log(revenue) outcome", df.assign(log_revenue=np.log(df.revenue)), y="log_revenue"))
    rows.append(run_variant("+ network_exposure as covariate", df, w=CONFOUNDERS + ["network_exposure"]))
    for l in ["rf", "lasso"]:
        rows.append(run_variant(f"learner = {l}", df, learner=l))
    for k in [3, 10]:
        rows.append(run_variant(f"{k} folds", df, k=k))
    for s in [1, 2, 3, 4]:
        rows.append(run_variant(f"gbr seed {s}", df, seed=s))
    rows.append(run_variant("PLACEBO: fake start 2026-04-01 (pre-period only)", placebo_panel(df, "2026-04-01")))
    rows.append(run_variant("PLACEBO: fake start 2026-05-15 (pre-period only)", placebo_panel(df, "2026-05-15")))
    return pd.DataFrame(rows)

def stability_checks(rob):
    base = rob.iloc[0]; seeds = rob[rob.variant.str.startswith("gbr seed")]
    real = rob[~rob.variant.str.startswith("PLACEBO") & ~rob.variant.str.contains("log")]
    plc = rob[rob.variant.str.startswith("PLACEBO")]
    allseeds = pd.concat([rob.iloc[[0]], seeds])
    chk = [
        ("no missing/infinite estimates", bool(np.isfinite(rob[["theta", "se"]].values).all()), int((~np.isfinite(rob[["theta", "se"]].values)).sum())),
        ("residual treatment variance > 0.005 (positivity after partialling-out)", bool((rob.resid_T_var > 0.005).all()), round(rob.resid_T_var.min(), 4)),
        ("baseline CI excludes zero", bool(base.ci_low > 0 or base.ci_high < 0), f"[{base.ci_low:.1f}, {base.ci_high:.1f}]"),
        ("sign stable across variants (revenue level)", bool((np.sign(real.theta) == np.sign(base.theta)).all()), f"{int((np.sign(real.theta) != np.sign(base.theta)).sum())} of {len(real)} flip"),
        ("seed stability: spread of theta <= 1 SE", bool(allseeds.theta.max() - allseeds.theta.min() <= base.se), round(allseeds.theta.max() - allseeds.theta.min(), 2)),
        ("fold stability: fold thetas agree in sign", bool(base.fold_theta_min * base.fold_theta_max > 0), f"{base.fold_theta_min:.1f} to {base.fold_theta_max:.1f}"),
        ("placebo effects insignificant", bool((plc.p_value > 0.05).all()), ", ".join(f"p={p:.2f}" for p in plc.p_value)),
    ]
    return pd.DataFrame(chk, columns=["check", "passed", "detail"])

def main():
    OUT.mkdir(exist_ok=True)
    rob = run_all(load_panel())
    rob.round(4).to_csv(OUT / "Week2_Day4_dml_robustness.csv", index=False)
    chk = stability_checks(rob); chk.to_csv(OUT / "Week2_Day4_stability_checks.csv", index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    p = rob[~rob.variant.str.contains("log")].iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(p.theta, range(len(p)), xerr=[p.theta - p.ci_low, p.ci_high - p.theta], fmt="o", capsize=3)
    ax.axvline(0, color="red", ls="--"); ax.set_yticks(range(len(p))); ax.set_yticklabels(p.variant, fontsize=7)
    ax.set_xlabel("DML estimate of effect on revenue (95% CI)"); ax.set_title("DML estimates across checks (revenue level)")
    plt.tight_layout(); plt.savefig(OUT / "Week2_Day4_estimates_forest.png", dpi=130); plt.close()
    print(rob[["variant", "theta", "se", "p_value", "resid_T_var"]].round(3).to_string(index=False)); print(chk.to_string(index=False))

if __name__ == "__main__":
    main()
