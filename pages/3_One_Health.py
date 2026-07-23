"""Page 3: longitudinal One Health trend studio."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from amr_changing_world.dashboard import (
    COLORS, COUNTRY_COLORS, ENDPOINTS, base_layout, dataframe_download,
    endpoint_label, footer, header, load_table, no_data, plotly_chart, setup_page,
    world_choropleth,
)

setup_page("One Health Trend Studio", "🌿")
header(
    "One Health Trend Studio",
    "Compare human AMR with animal and environmental context",
    "Follow yearly AMR and a selected One Health indicator for up to five countries. "
    "Aligned panels support comparison without implying that parallel trends are causal.",
)

data = load_table("one_health_country_year")
coverage = load_table("endpoint_coverage")
lag_models = load_table("lag_associations")

indicator_options = {
    "Temperature anomaly (°C)": "temperature_anomaly_c",
    "Total livestock units": "livestock_units_total",
    "Animal antimicrobial use (adjusted mg/kg)": "total_mgkg_adjusted",
    "Cattle/buffalo share of livestock units": "livestock_share_cattle_buffalo",
    "Poultry share of livestock units": "livestock_share_poultry",
    "Swine share of livestock units": "livestock_share_swine",
}
indicator_units = {
    "temperature_anomaly_c": "°C",
    "livestock_units_total": "livestock units",
    "total_mgkg_adjusted": "mg/kg",
    "livestock_share_cattle_buffalo": "share",
    "livestock_share_poultry": "share",
    "livestock_share_swine": "share",
}

c1, c2 = st.columns([1.1, 1])
with c1:
    endpoint_labels = {
        f"{endpoint_label(r.endpoint_id)} · {r.analysis_tier}": r.endpoint_id
        for r in coverage.itertuples()
    }
    selected_endpoint = st.selectbox("AMR endpoint", list(endpoint_labels))
    eid = endpoint_labels[selected_endpoint]
with c2:
    selected_indicator = st.selectbox("One Health indicator", list(indicator_options))
    indicator = indicator_options[selected_indicator]

eligible = data[data.endpoint_id.eq(eid)].dropna(subset=[indicator])
country_counts = eligible.groupby("country").year.nunique().sort_values(ascending=False)
countries = country_counts.index.tolist()
default = countries[: min(3, len(countries))]
selected_countries = st.multiselect(
    "Compare countries (maximum five)",
    countries,
    default=default,
    max_selections=5,
    help="Countries are ordered by the number of years with both AMR and the selected indicator.",
)

view = st.radio(
    "Trend scale",
    ["Absolute values", "Indexed change (first observed year = 100)"],
    horizontal=True,
    help="Indexed change compares direction and relative change when indicators use very different scales.",
)

if not selected_countries:
    no_data("Select at least one country to draw the trend panels.")
else:
    trend = data[
        data.endpoint_id.eq(eid) & data.country.isin(selected_countries)
    ].sort_values(["country", "year"]).copy()
    if view.startswith("Indexed"):
        for col in ["resistance_pct", indicator]:
            trend[f"{col}_plot"] = trend.groupby("country")[col].transform(
                lambda x: 100 * x / x.dropna().iloc[0] if len(x.dropna()) and x.dropna().iloc[0] != 0 else np.nan
            )
        amr_y, indicator_y = "resistance_pct_plot", f"{indicator}_plot"
        amr_title, context_title = "AMR index", "Indicator index"
    else:
        amr_y, indicator_y = "resistance_pct", indicator
        amr_title, context_title = "Resistance (%)", f"{selected_indicator}"

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=.09,
        subplot_titles=(f"Human AMR · {endpoint_label(eid)}", selected_indicator, "Eligible tested isolates"),
    )
    for i, country in enumerate(selected_countries):
        d = trend[trend.country.eq(country)]
        color = COUNTRY_COLORS[i]
        fig.add_scatter(x=d.year, y=d[amr_y], mode="lines+markers", name=country, legendgroup=country, line=dict(color=color, width=3), row=1, col=1)
        fig.add_scatter(x=d.year, y=d[indicator_y], mode="lines+markers", name=country, legendgroup=country, showlegend=False, line=dict(color=color, width=2), connectgaps=False, row=2, col=1)
        fig.add_bar(x=d.year, y=d.n_tested, name=country, legendgroup=country, showlegend=False, marker_color=color, opacity=.7, row=3, col=1)
    fig.update_yaxes(title=amr_title, row=1, col=1)
    fig.update_yaxes(
        title=context_title.replace(" (", "<br>(") if len(context_title) > 30 else context_title,
        row=2,
        col=1,
    )
    fig.update_yaxes(title="Isolates", row=3, col=1)
    for row in range(1, 4):
        fig.update_xaxes(showticklabels=True, dtick=1, row=row, col=1)
    fig.update_xaxes(title="Year", row=3, col=1, dtick=1)
    base_layout(fig, 820)
    fig.update_layout(barmode="group")
    plotly_chart(fig, key="one-health-trends")
    st.caption("A break in a line means the linked indicator was not reported for that country-year. AMR cells with fewer than 30 isolates are suppressed.")

latest = eligible.sort_values("year").groupby("iso3", as_index=False).tail(1)
if len(latest):
    fig = world_choropleth(
        latest, indicator, f"Latest available {selected_indicator.lower()}", selected_indicator,
        colorscale=["#F4F7F6", "#65AFA7", "#173B57"],
    )
    plotly_chart(fig, key="one-health-map")
    st.caption("Each country uses its latest available year; hover to interpret the value. Grey indicates no linked data. The complete world remains visible.")

with st.expander("What does this indicator mean?"):
    if indicator == "livestock_units_total":
        st.write(
            "Livestock units combine animal species using species-specific conversion factors. "
            "They approximate the scale and composition of a national livestock system. They are "
            "not livestock density because no population or agricultural-land denominator is used."
        )
    elif indicator.startswith("livestock_share"):
        st.write(
            "This is the selected animal group's share of total standardised livestock units, not "
            "its share of animals by head count. Shares are compositional: an increase in one group "
            "necessarily changes the relative shares of others."
        )
    elif indicator == "total_mgkg_adjusted":
        st.write(
            "WOAH adjusted mg/kg is a country-level estimate of antimicrobial quantities used in "
            "animals relative to an animal-biomass denominator. Reporting coverage is limited and "
            "changes in national reporting can affect trends."
        )
    else:
        st.write("Annual land-surface temperature anomaly relative to the source reference period.")

model = lag_models[
    lag_models.endpoint_id.eq(eid) & lag_models.indicator.eq(indicator)
].sort_values("lag_years")
if len(model):
    st.subheader("Exploratory lag estimates")
    shown = model[["lag_years", "countries", "paired_country_year_cells", "odds_ratio_per_sd", "or_ci_low", "or_ci_high", "fdr_q_value"]].copy()
    shown.columns = ["Lag (years)", "Countries", "Paired country-years", "OR per SD", "CI low", "CI high", "FDR q"]
    st.dataframe(shown, width="stretch", hide_index=True)
    st.caption("Models adjust for country and calendar year. They remain ecological and hypothesis-generating; 144 comparisons were FDR-corrected together.")

dataframe_download(
    trend if selected_countries else eligible.iloc[0:0],
    "Download selected annual trends",
    f"{eid}_{indicator}_trends.csv",
    "one-health-trend-download",
)
footer()
