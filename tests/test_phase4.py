import unittest

import pandas as pd

from amr_changing_world.phase4 import holm_adjust


class Phase4Tests(unittest.TestCase):
    def test_holm_adjustment_known_values(self):
        raw = pd.Series([0.01, 0.04, 0.03, 0.002], index=list("abcd"))
        adjusted = holm_adjust(raw)
        expected = pd.Series([0.03, 0.06, 0.06, 0.008], index=list("abcd"))
        pd.testing.assert_series_equal(adjusted, expected)

    def test_holm_is_monotone_in_rank_order(self):
        raw = pd.Series([0.5, 0.001, 0.03, 0.02])
        adjusted = holm_adjust(raw)
        order = raw.sort_values().index
        self.assertTrue(adjusted.loc[order].is_monotonic_increasing)


if __name__ == "__main__":
    unittest.main()
