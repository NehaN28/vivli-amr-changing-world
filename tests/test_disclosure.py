import unittest

import pandas as pd

from amr_changing_world.linkage import disclosure_safe


class TestDisclosure(unittest.TestCase):
    def test_small_cells_suppressed(self):
        frame = pd.DataFrame({
            "n_tested": [29, 30], "n_resistant": [10, 10], "n_intermediate": [0, 0],
            "n_susceptible": [19, 20], "n_mic": [29, 30],
            "resistance_pct": [34.48, 33.33], "mic_coverage_pct": [100.0, 100.0],
        })
        result = disclosure_safe(frame, 30)
        self.assertTrue(pd.isna(result.loc[0, "n_tested"]))
        self.assertEqual(result.loc[1, "n_tested"], 30)


if __name__ == "__main__":
    unittest.main()

