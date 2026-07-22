from pathlib import Path

import pandas as pd

from amr_changing_world.dashboard import DATA, ENDPOINTS, PRIMARY_IDS, endpoint_label


def test_dashboard_files_exist():
    required = {
        "amr_country_year.csv.gz", "standardised_amr.csv.gz", "main_conflict_models.csv.gz",
        "country_context.csv.gz", "one_health_models.csv.gz", "woah_models.csv.gz",
        "rd_pathogen.csv.gz",
    }
    assert required <= {p.name for p in DATA.glob("*.csv.gz")}


def test_public_amr_cells_are_suppressed_below_30():
    df = pd.read_csv(DATA / "amr_country_year.csv.gz")
    visible = df[df["sufficient_atlas_data"]]
    assert visible["n_tested"].ge(30).all()
    hidden = df[~df["sufficient_atlas_data"]]
    assert hidden["n_tested"].isna().all()
    assert hidden["n_resistant"].isna().all()


def test_standardised_outputs_are_primary_and_disclosure_safe():
    df = pd.read_csv(DATA / "standardised_amr.csv.gz")
    assert set(df["endpoint_id"]) == set(PRIMARY_IDS)
    assert df["n_tested"].ge(30).all()
    assert df["standardised_resistance_pct"].between(0, 100).all()
    assert (df["standardised_ci_low"] <= df["standardised_resistance_pct"]).all()
    assert (df["standardised_ci_high"] >= df["standardised_resistance_pct"]).all()


def test_endpoint_labels_complete():
    assert len(ENDPOINTS) == 17
    assert all(" – " in endpoint_label(key) for key in ENDPOINTS)
