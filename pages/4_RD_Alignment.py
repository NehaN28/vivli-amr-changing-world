"""Page 4: AMR R&D Investment Alignment."""

import plotly.express as px
import streamlit as st

from amr_changing_world.dashboard import COLORS, base_layout, dataframe_download, footer, header, load_csv, setup_page

setup_page("R&D Investment Alignment", "🔬")
header("R&D Investment Alignment", "Where global research attention goes", "Compare reported AMR R&D commitments across sectors, research areas, pathogens and recipient-institution geographies. Funding location is interpreted as research-capacity location, not beneficiary burden.")

sector = load_csv("rd_sector.csv.gz")
areas = load_csv("rd_research_area.csv.gz")
pathogen = load_csv("rd_pathogen.csv.gz")
geo = load_csv("rd_geography.csv.gz")

c1, c2, c3 = st.columns(3)
c1.metric("Human-sector funding", f"{sector.loc[sector.sector=='Human','funding_share_pct'].iloc[0]:.1f}%")
c2.metric("Animal-sector funding", f"{sector.loc[sector.sector=='Animal','funding_share_pct'].iloc[0]:.1f}%")
c3.metric("Environment-sector funding", f"{sector.loc[sector.sector=='Environment','funding_share_pct'].iloc[0]:.1f}%")

left, right = st.columns(2)
with left:
    fig = px.pie(sector, names="sector", values="fractional_funding_usd", hole=.58, title="Funding portfolio by sector", color_discrete_sequence=[COLORS["navy"], COLORS["teal"], COLORS["gold"], COLORS["coral"], COLORS["grey"]])
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>$%{value:,.0f}<extra></extra>")
    base_layout(fig, 430)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
with right:
    a = areas.sort_values("fractional_funding_usd")
    fig = px.bar(a, x="fractional_funding_usd", y="research_area", orientation="h", title="Funding by research area", labels={"fractional_funding_usd":"Reported commitments (USD)","research_area":""}, color_discrete_sequence=[COLORS["teal"]])
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    base_layout(fig, 430)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

mapped = pathogen.dropna(subset=["latest_standardised_resistance_pct"]).copy()
fig = px.scatter(mapped, x="share_of_pathogen_specific_funding_pct", y="latest_standardised_resistance_pct", size="fractional_projects", text="pathogen", color="annual_change_pp", color_continuous_scale="RdBu_r", title="Pathogen attention and latest observed resistance", labels={"share_of_pathogen_specific_funding_pct":"Share of mapped pathogen-specific funding (%)", "latest_standardised_resistance_pct":"2024 standardised resistance (%)", "annual_change_pp":"Annual AMR change (pp)"})
fig.update_traces(textposition="top center")
base_layout(fig, 460)
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

fig = px.choropleth(geo, locations="iso3", color="recipient_funding_usd", hover_name="country", hover_data={"iso3":False,"recipient_projects":":,.0f","recipient_funding_usd":":$,.0f"}, color_continuous_scale=["#E7F1EF", "#65AFA7", "#173B57"], title="Recipient-institution geography, 2015–2024", labels={"recipient_funding_usd":"Reported funding (USD)","recipient_projects":"Projects"})
fig.update_geos(showframe=False, showcoastlines=False, bgcolor="rgba(0,0,0,0)", projection_type="natural earth")
base_layout(fig, 500)
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

st.markdown('<div class="note warn"><b>Interpretation:</b> <i>A. baumannii</i> had the highest 2024 standardised resistance among the directly comparable primary pathogens but 8.4% of mapped pathogen-specific funding. This is an attention-alignment signal, not proof of underfunding. Resistance percentage is not disease burden.</div>', unsafe_allow_html=True)
dataframe_download(pathogen, "Download pathogen alignment table", "rd_pathogen_alignment.csv", "rd-download")
footer()
