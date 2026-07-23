from pathlib import Path

import plotly.graph_objects as go
import pytest
from streamlit.testing.v1 import AppTest

from amr_changing_world.dashboard import (
    CHART_CONFIG,
    DASHBOARD_CSS,
    base_layout,
    world_choropleth,
)


ROOT = Path(__file__).resolve().parents[1]


def test_responsive_css_has_laptop_and_mobile_breakpoints():
    assert "@media (max-width: 900px)" in DASHBOARD_CSS
    assert "@media (max-width: 640px)" in DASHBOARD_CSS
    assert 'data-testid="stColumn"' in DASHBOARD_CSS
    assert "flex-basis: 100%" in DASHBOARD_CSS
    assert "overflow-wrap: anywhere" in DASHBOARD_CSS


def test_plotly_contract_wraps_titles_and_keeps_labels_inside_canvas():
    fig = go.Figure(
        go.Scatter(
            x=[2020, 2021],
            y=[1, 2],
            name="A deliberately long legend label used for responsive testing",
        )
    )
    fig.update_layout(
        title=(
            "A deliberately long chart title that must wrap instead of being clipped "
            "at narrower dashboard widths"
        )
    )
    base_layout(fig)
    assert "<br>" in fig.layout.title.text
    assert fig.layout.xaxis.automargin is True
    assert fig.layout.yaxis.automargin is True
    assert fig.layout.legend.orientation == "h"
    assert fig.layout.legend.y < 0
    assert fig.layout.legend.entrywidth is None
    assert fig.layout.legend.entrywidthmode is None
    assert fig.layout.margin.b >= 120
    assert CHART_CONFIG["responsive"] is True


def test_world_map_has_stable_context_and_compact_colorbar():
    import pandas as pd

    frame = pd.DataFrame(
        {
            "iso3": ["IND", "DMA", ""],
            "country": ["India", "Dominica", ""],
            "value": [12.5, 7.0, 100.0],
        }
    )
    figure = world_choropleth(frame, "value", "Test map", "Example value")
    trace = figure.data[0]
    assert figure.layout.geo.scope == "world"
    assert figure.layout.geo.fitbounds is False
    assert figure.layout.geo.showland is True
    assert trace.colorbar.orientation == "h"
    assert any("no data" in annotation.text.lower() for annotation in figure.layout.annotations)
    assert len(figure.data) == 2
    assert figure.data[1].type == "scattergeo"
    assert figure.data[0].locations.tolist() == ["IND", "DMA"]


@pytest.mark.parametrize(
    "page",
    [
        "0_Home.py",
        "1_Global_AMR.py",
        "2_Conflict_and_AMR.py",
        "3_One_Health.py",
        "4_RD_Alignment.py",
        "5_Country_Profile.py",
        "6_Methods_and_Data_Quality.py",
    ],
)
def test_every_page_renders_without_exception(page):
    app = AppTest.from_file(ROOT / "pages" / page, default_timeout=45).run()
    assert not app.exception


def test_one_health_sparse_and_five_country_states_render():
    app = AppTest.from_file(
        ROOT / "pages" / "3_One_Health.py",
        default_timeout=45,
    ).run()
    app.selectbox[1].set_value("Animal antimicrobial use (adjusted mg/kg)")
    app.run()
    assert not app.exception
    selected = list(app.multiselect[0].options[:5])
    app.multiselect[0].set_value(selected)
    app.radio[0].set_value("Indexed change (first observed year = 100)")
    app.run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2


def test_one_health_empty_country_state_is_explained():
    app = AppTest.from_file(
        ROOT / "pages" / "3_One_Health.py",
        default_timeout=45,
    ).run()
    app.multiselect[0].set_value([])
    app.run()
    assert not app.exception
    assert any(
        "Select at least one country" in info.value
        for info in app.info
    )
