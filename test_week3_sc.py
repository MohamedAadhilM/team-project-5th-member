"""Unit tests for the Week 3 synthetic-control workflow. Run: python -m unittest test_week3_sc -v"""
import unittest
import numpy as np
import pandas as pd
from week3_day1_windows_baseline import weekly_panel, to_index, split_pre_post, rolling_folds, mspe, INTERVENTION
from week3_day2_synthetic_control import fit_weights, run_sc

def synthetic_daily(effect=10.0, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-01-01", "2026-08-31")
    t = np.arange(len(dates))
    common = {r: 100 + 15 * np.sin(2 * np.pi * (t + s) / 60) + rng.normal(0, 1.0, len(t)) for r, s in
              {"R02": 0, "R03": 20, "R05": 40, "R06": 10, "R07": 30, "R08": 50}.items()}
    treated = 0.6 * common["R07"] + 0.4 * common["R08"] + rng.normal(0, 0.5, len(t)) + effect * (dates >= INTERVENTION)
    rows = [pd.DataFrame({"date": dates, "region_id": r, "revenue": v}) for r, v in {**common, "R01": treated, "R04": treated}.items()]
    return pd.concat(rows, ignore_index=True)

class TestSC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wk = weekly_panel(synthetic_daily()); cls.idx, cls.pm = to_index(cls.wk)

    def test_weeks_are_full_and_anchored(self):
        pre, post = split_pre_post(self.wk)
        self.assertEqual((len(pre), len(post)), (25, 8)); self.assertIn(INTERVENTION, post.index)

    def test_weights_valid_and_recovered(self):
        pre, _ = split_pre_post(self.idx)
        w = fit_weights(pre["R01"].values, pre[["R07", "R08", "R02", "R03"]].values)
        self.assertAlmostEqual(w.sum(), 1.0, places=6); self.assertTrue((w >= -1e-9).all())
        self.assertAlmostEqual(w[0], 0.6, delta=0.1); self.assertAlmostEqual(w[1], 0.4, delta=0.1)

    def test_effect_recovered_with_low_pre_error(self):
        r = run_sc(self.idx, self.pm, "R01", ["R07", "R08", "R02", "R03", "R05", "R06"])
        self.assertLess(r["pre_RMSPE"], 3.0); self.assertAlmostEqual(r["att_level"], 10.0, delta=2.5)

    def test_weights_do_not_use_post_period_data(self):
        a = run_sc(self.idx, self.pm, "R01", ["R07", "R08"])
        idx2 = self.idx.copy(); idx2.loc[idx2.index >= INTERVENTION, ["R07", "R08"]] += 50
        b = run_sc(idx2, self.pm, "R01", ["R07", "R08"])
        self.assertEqual(a["weights"], b["weights"])

    def test_rolling_folds_have_no_leakage(self):
        f = rolling_folds(25); self.assertEqual(len(f), 4)
        for tr, te in f:
            self.assertLess(tr.max(), te.min()); self.assertEqual(len(set(tr) & set(te)), 0)

    def test_mspe_formula(self):
        self.assertAlmostEqual(mspe([1, 2, 3], [1, 2, 5]), 4 / 3)

if __name__ == "__main__":
    unittest.main()
