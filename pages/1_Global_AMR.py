"""Page 1: Global AMR Explorer."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from amr_changing_world.dashboard import (
    COLORS, ENDPOINTS, PRIMARY_IDS, base_layout, dataframe_download, endpoint_label,
    endpoint_options, footer, header, load_csv, no_data, setup_page,
)

setup_page("Global AMR Explorer", "🌍")
header(
    "Global AMR Explorer",
    "Human AMR trends in a changing world",
    "Explore disclosure-checked resistance estimates from ATLAS. Standardised estimates adjust patient and specimen composition for the four prespecified primary outcomes.",
)

dashboard = load_csv("amr_country_year.csv.gz")
standard = load_csv("standardised_amr.csv.gz")

with st.sidebar:
    st.header("Explore")
    organism = st.selectbox("Pathogen", sorted(dashboard["species"].dropna().unique()))
    organism_rows = dashboard[dashboard["species"] == organism]
    drugs = sorted(organism_rows["drug"].dropna().unique())
    drug = st.selectbox("Antimicrobial", drugs)
    eid = organism_rows.loc[organism_rows["drug"] == drug, "endpoint_id"].iloc[0]
    tier = ENDPOINTS[eid][2]
    estimate_choices = ["Crude"] + (["Standardised"] if eid in PRIMARY_IDS else [])
    estimate = st.radio("Estimate", estimate_choices, horizontal=True)
    source = standard[standard.endpoint_id == eid] if estimate == "Standardised" else dashboard[(dashboard.endpoint_id == eid) & dashboard.sufficient_atlas_data]
    if len(source):
        years = (int(source.year.min()), int(source.year.max()))
        year_range = st.slider("Year range", years[0], years[1], years)
    else:
        year_range = (2019, 2024)

st.markdown(f'<span class="tier">{tier} outcome</span>', unsafe_allow_html=True)
st.subheader(endpoint_label(eid))

if estimate == "Standardised":
    df = standard[(standard.endpoint_id == eid) & standard.year.between(*year_range)].copy()
    value = "standardised_resistance_pct"
else:
    df = dashboard[(dashboard.endpoint_id == eid) & dashboard.sufficient_atlas_data & dashboard.year.between(*year_range)].copy()
    value = "resistance_pct"

if df.empty:
    no_data()
else:
    latest_year = int(df.year.max())
    latest = df[df.year == latest_year]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest year", latest_year)
    c2.metric("Countries", f"{latest.iso3.nunique():,}")
    c3.metric("Tested isolates", f"{int(latest.n_tested.sum()):,}")
    c4.metric("Median resistance", f"{latest[value].median():.1f}%")

    map_df = latest.dropna(subset=[value])
    fig = px.choropleth(
        map_df, locations="iso3", color=value, hover_name="country",
        hover_data={"iso3": False, value: ":.1f", "n_tested": ":,.0f"},
        color_continuous_scale=["#E7F1EF", "#65AFA7", "#D39A35", "#B5483D"],
        range_color=(0, 100), labels={value: "Resistance (%)", "n_tested": "Tested"},
        title=f"Resistance in {latest_year}",
    )
    fig.update_geos(showframe=False, showcoastlines=False, bgcolor="rgba(0,0,0,0)", projection_type="natural earth")
    base_layout(fig, 500)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

    countries = sorted(df.country.unique())
    selected = st.multiselect("Compare countries", countries, default=countries[:1], max_selections=6)
    if selected:
        trend = df[df.country.isin(selected)]
        fig = px.line(trend, x="year", y=value, color="country", markers=True,
                      labels={value: f"{estimate} resistance (%)", "year": "Year", "country": "Country"},
                      title="Country trends", color_discrete_sequence=px.colors.qualitative.Safe)
        if estimate == "Standardised":
            for country in selected:
                d = trend[trend.country == country]
                fig.add_trace(go.Scatter(x=d.year, y=d.standardised_ci_high, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=d.year, y=d.standardised_ci_low, mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(15,118,110,.08)", showlegend=False, hoverinfo="skip"))
        base_layout(fig)
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

    table_cols = ["country", "iso3", "year", "n_tested", "n_resistant", value]
    if estimate == "Standardised": table_cols += ["standardised_ci_low", "standardised_ci_high"]
    dataframe_download(df[table_cols], "Download current selection", f"{eid}_{estimate.lower()}_{year_range[0]}_{year_range[1]}.csv", "global-download")

st.markdown('<div class="note"><b>Interpretation:</b> Country estimates reflect available clinical isolates, not population prevalence. Differences may reflect surveillance, patient mix and testing practices. Cells with fewer than 30 isolates are not displayed.</div>', unsafe_allow_html=True)
footer()
