"""Unit tests for the Week 2 DML pipeline (Member 5).  Run: python -m unittest test_dml_pipeline -v"""
import unittest
import numpy as np
import pandas as pd
from week2_day2_dml_preprocessing import validate_inputs, within_transform, make_folds, build_dml_dataset
from week2_day3_dml_estimation import fit_dml
from week2_day1_design_dml import CONFOUNDERS, TREATMENT, OUTCOME

def synthetic_panel(effect=25.0, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-01-01", periods=240)
    rows = []
    for ri, reg in enumerate([f"R0{i}" for i in range(1, 7)]):
        base = 200 + 40 * (reg in ("R01", "R04"))              # treated regions have higher baseline (confounding)
        for prod in ("P1", "P2"):
            d = pd.DataFrame({"date": dates, "region_id": reg, "product_id": prod})
            d["post_period"] = (d.date >= "2026-07-01").astype(int)
            for c in CONFOUNDERS:
                if c != "post_period":
                    d[c] = rng.normal(1, .1, len(d))
            d[TREATMENT] = ((reg in ("R01", "R04")) & (d.post_period == 1)).astype(int)
            d[OUTCOME] = base + 30 * d.demand_index + effect * d[TREATMENT] + rng.normal(0, 5, len(d))
            rows.append(d)
    return pd.concat(rows, ignore_index=True)

class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = synthetic_panel()

    def test_validation_passes_on_clean_panel(self):
        r = validate_inputs(self.df)
        # the synthetic panel starts treatment on 2026-07-01 and has no mediator columns in W
        self.assertTrue(r.passed.all(), r[~r.passed].to_string())

    def test_validation_flags_missing_values(self):
        bad = self.df.copy(); bad.loc[0, "demand_index"] = np.nan
        r = validate_inputs(bad); self.assertFalse(r.loc[r.check == "no missing in modeling columns", "passed"].item())

    def test_within_transform_removes_group_means(self):
        d = within_transform(self.df)
        g = d.region_id + d.product_id
        self.assertLess(d.groupby(g)[OUTCOME].mean().abs().max(), 1e-8)

    def test_folds_are_disjoint_and_cover_all_rows(self):
        f = make_folds(self.df.date, 5); te = np.concatenate([t for _, t in f])
        self.assertEqual(len(te), len(self.df)); self.assertEqual(len(set(te)), len(self.df))

    def test_dataset_has_fold_column(self):
        self.assertEqual(sorted(build_dml_dataset(self.df).fold.unique()), [0, 1, 2, 3, 4])

    def test_recovers_known_effect(self):
        r = fit_dml(self.df, learner="lasso")
        self.assertTrue(np.isfinite(r["theta"]) and np.isfinite(r["se"]))
        self.assertLess(abs(r["theta"] - 25.0), max(4 * r["se"], 3.0))

    def test_zero_effect_not_significant(self):
        r = fit_dml(synthetic_panel(effect=0.0, seed=1), learner="lasso")
        self.assertGreater(r["p_value"], 0.01)

if __name__ == "__main__":
    unittest.main()
