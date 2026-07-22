import unittest

import pandas as pd

from amr_changing_world.phase3 import primary_model_lock


class TestPhase3ModelLock(unittest.TestCase):
    def test_requires_three_years_and_within_country_exposure_variation(self):
        frame = pd.DataFrame({
            "endpoint_id": ["ECO_CAZ_R"] * 6,
            "iso3": ["AAA"] * 3 + ["BBB"] * 3,
            "country": ["A"] * 3 + ["B"] * 3,
            "year": [2019, 2020, 2021] * 2,
            "n_tested": [30] * 6,
            "n_resistant": [3] * 6,
            "conflict_annual_events_lag1": [1, 2, 4, 0, 0, 0],
            "conflict_log2p1_events_lag1": [1, 1.585, 2.322, 0, 0, 0],
        })
        final, country, summary = primary_model_lock(frame)
        self.assertEqual(set(final["iso3"]), {"AAA"})
        self.assertEqual(int(summary.loc[0, "eligible_country_year_cells"]), 3)
        excluded = country.loc[country["iso3"].eq("BBB")].iloc[0]
        self.assertFalse(bool(excluded["has_exposure_variation"]))


if __name__ == "__main__":
    unittest.main()
