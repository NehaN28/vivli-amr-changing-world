from pathlib import Path

import pandas as pd

from amr_changing_world.dashboard import (
    DATA, ENDPOINTS, PRIMARY_IDS, endpoint_label, world_choropleth,
)


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


def test_phase8_dashboard_tables_exist():
    required = {
        "endpoint_coverage.parquet",
        "one_health_country_year.parquet",
        "rd_annual_portfolio.parquet",
        "rd_country_year.parquet",
        "coverage_summary.parquet",
        "lag_associations.parquet",
    }
    assert required <= {p.name for p in DATA.glob("*.parquet")}


def test_home_page_identifies_challenge_and_team_without_contacts():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pages" / "0_Home.py").read_text(encoding="utf-8")
    assert "Vivli AMR Data Challenge 2026" in source
    assert "Dr. Neha Nityadarshini" in source
    assert "Team Lead" in source
    assert "Dr. Jaya Biswas" in source
    assert "AIIMS-CAPFIMS" in source
    assert "@" not in source
    assert (root / "assets" / "team" / "neha_nityadarshini.png").is_file()
    assert (root / "assets" / "team" / "jaya_biswas.png").is_file()


def test_world_map_keeps_full_context():
    frame = pd.DataFrame(
        {"iso3": ["IND"], "country": ["India"], "value": [12.5]}
    )
    figure = world_choropleth(frame, "value", "Test", "Value")
    assert figure.layout.geo.scope == "world"
    assert figure.layout.geo.showland is True
    assert figure.layout.geo.fitbounds is False
    assert figure.layout.geo.landcolor == "#E9EEEF"
