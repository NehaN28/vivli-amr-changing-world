import numpy as np
import pandas as pd

from amr_changing_world.phase5 import _livestock_country_year


def test_livestock_lag_and_total(tmp_path):
    frame = pd.DataFrame({
        "iso3": ["AAA", "AAA"], "year": [2020, 2020],
        "livestock_group": ["cattle_buffalo", "poultry"],
        "livestock_units": [700.0, 300.0], "livestock_unit_share": [0.7, 0.3],
    })
    frame.to_csv(tmp_path / "livestock_country_year_group.csv.gz", index=False)
    out = _livestock_country_year(tmp_path)
    assert out.loc[0, "year"] == 2021
    assert out.loc[0, "total_livestock_units"] == 1000
    assert np.isclose(out.loc[0, "cattle_buffalo"], 0.7)
