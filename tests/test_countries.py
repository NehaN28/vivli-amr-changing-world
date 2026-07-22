import unittest

import pandas as pd

from amr_changing_world.countries import CountryCrosswalk


class TestCountryCrosswalk(unittest.TestCase):
    def setUp(self):
        self.crosswalk = CountryCrosswalk()

    def test_atlas_aliases(self):
        result = self.crosswalk.map_series(pd.Series(["Korea, South", "Turkey"]), "atlas")
        self.assertEqual(result["iso3"].tolist(), ["KOR", "TUR"])

    def test_non_country_acled_label(self):
        result = self.crosswalk.map_series(pd.Series(["Atlantic Ocean"]), "acled")
        self.assertEqual(result.loc[0, "status"], "non_country")


if __name__ == "__main__":
    unittest.main()

