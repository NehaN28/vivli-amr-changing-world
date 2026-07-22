import tempfile
import unittest
from pathlib import Path

import pandas as pd

from amr_changing_world.transforms.acled import process_acled
from amr_changing_world.validation import ValidationReport


class TestACLEDCompleteness(unittest.TestCase):
    def test_partial_year_not_used_as_annual_exposure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "acled.xlsx"
            pd.DataFrame({
                "COUNTRY": ["India", "India"], "MONTH": ["January", "February"],
                "YEAR": [2020, 2020], "EVENTS": [1, 2],
            }).to_excel(path, index=False, sheet_name="Sheet1")
            _, annual = process_acled(path, ValidationReport())
            self.assertEqual(len(annual), 0)

    def test_omitted_zero_months_are_imputed_after_coverage_starts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "acled.xlsx"
            months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            pd.DataFrame({
                "COUNTRY": ["India"] * 14,
                "MONTH": months + ["January", "January"],
                "YEAR": [2020] * 12 + [2021, 2022],
                "EVENTS": [0] * 12 + [4, 1],
            }).to_excel(path, index=False, sheet_name="Sheet1")
            _, annual = process_acled(path, ValidationReport())
            row = annual.loc[annual["year"].eq(2021)].iloc[0]
            self.assertEqual(row["annual_events"], 4)
            self.assertEqual(row["zero_months_imputed"], 11)


if __name__ == "__main__":
    unittest.main()
