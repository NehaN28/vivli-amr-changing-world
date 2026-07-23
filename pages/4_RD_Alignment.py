"""Page 4: temporal AMR R&D explorer."""

import plotly.express as px
import streamlit as st

from amr_changing_world.dashboard import (
    COUNTRY_COLORS, base_layout, dataframe_download, footer, header, load_table,
    no_data, plotly_chart, setup_page, world_choropleth,
)

setup_page("R&D Investment Explorer", "🔬")
header(
    "R&D Investment Explorer",
    "How reported AMR research attention changes over time",
    "Explore annual reported commitments and project starts by sector, research area, "
    "pathogen and recipient-institution country. Funding location describes research capacity, "
    "not disease burden or ultimate beneficiaries.",
)

portfolio = load_table("rd_annual_portfolio")
geography = load_table("rd_country_year")

dimension_names = {
    "sector": "Sector",
    "research_area": "Research area",
    "pathogen": "Pathogen",
}
available_dimensions = {
    dimension_names.get(d, str(d).replace("_", " ").title()): d
    for d in portfolio.dimension.dropna().unique()
}
dimension_label = st.selectbox("Group annual investment by", list(available_dimensions))
dimension = available_dimensions[dimension_label]
subset = portfolio[portfolio.dimension.eq(dimension)].copy()
categories = subset.groupby("category").reported_commitment_usd.sum(min_count=1).sort_values(ascending=False).index.tolist()
selected_categories = st.multiselect(
    f"Compare {dimension_label.lower()} categories",
    categories,
    default=categories[: min(5, len(categories))],
    max_selections=8,
)

metric_label = st.radio(
    "Measure",
    ["Reported commitments (USD)", "Fractional project count"],
    horizontal=True,
)
metric = "reported_commitment_usd" if metric_label.startswith("Reported") else "fractional_projects"
trend = subset[subset.category.isin(selected_categories)].dropna(subset=[metric]).copy()

if trend.empty:
    no_data()
else:
    trend["display_category"] = trend["category"].str.wrap(28).str.replace("\n", "<br>")
    fig = px.line(
        trend, x="year", y=metric, color="display_category", markers=True,
        labels={
            "year": "Project start year",
            metric: metric_label,
            "display_category": dimension_label,
        },
        color_discrete_sequence=px.colors.qualitative.Safe,
        title=f"Annual AMR R&D by {dimension_label.lower()}",
    )
    fig.update_layout(legend_title_text=dimension_label)
    if metric == "reported_commitment_usd":
        fig.update_yaxes(tickprefix="$", tickformat="~s")
    base_layout(fig, 520)
    plotly_chart(fig, key="rd-portfolio-trends")
    st.caption("Amounts are shown only where a commitment was reported. A low annual total can reflect missing amount data as well as lower investment.")

country_totals = geography.groupby("country").reported_commitment_usd.sum(min_count=1).sort_values(ascending=False)
country_options = country_totals.index.tolist()
selected_countries = st.multiselect(
    "Compare recipient-institution countries (maximum five)",
    country_options,
    default=country_options[: min(3, len(country_options))],
    max_selections=5,
)
country_trend = geography[geography.country.isin(selected_countries)].copy()
if len(country_trend):
    fig = px.line(
        country_trend, x="year", y="reported_commitment_usd", color="country",
        markers=True, color_discrete_sequence=COUNTRY_COLORS,
        title="Annual reported commitments by recipient-institution country",
        labels={"year": "Project start year", "reported_commitment_usd": "Reported commitments (USD)", "country": "Country"},
    )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    base_layout(fig, 470)
    plotly_chart(fig, key="rd-country-trends")

latest_year = int(geography.year.max())
map_data = geography[geography.year.eq(latest_year)]
fig = world_choropleth(
    map_data, "reported_commitment_usd",
    f"Recipient-institution funding for projects starting in {latest_year}",
    "Reported USD",
)
plotly_chart(fig, key="rd-map")
st.caption("Grey countries have no reported recipient commitment in the selected year. Zero and missing are not treated as the same.")

st.markdown(
    '<div class="note warn"><b>Interpretation:</b> These figures describe the reported R&D '
    'portfolio. They do not establish whether investment is sufficient, equitable, spent in the '
    'same year, or aligned with population disease burden.</div>',
    unsafe_allow_html=True,
)
dataframe_download(trend, "Download selected portfolio trends", "rd_annual_portfolio_selection.csv", "rd-portfolio-download")
footer()
