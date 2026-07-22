"""Page 5: Country profile."""

import pandas as pd
import plotly.express as px
import streamlit as st

from amr_changing_world.dashboard import COLORS, base_layout, dataframe_download, endpoint_label, footer, header, load_csv, setup_page

setup_page("Country Profile", "📍")
header("Country Profile", "One country, all available evidence", "A concise view of ATLAS coverage, AMR trajectories, political violence, temperature, livestock, animal AMU and recipient research capacity.")

context = load_csv("country_context.csv.gz")
amr = load_csv("standardised_amr.csv.gz")
country = st.selectbox("Select country", sorted(context.country))
r = context[context.country == country].iloc[0]

st.subheader(country)
cols = st.columns(4)
cols[0].metric("2024 endpoints", int(r.endpoints_in_2024))
cols[1].metric("2024 tested isolates", f"{int(r.total_tested_isolates_2024):,}")
cols[2].metric("Mean AMR trajectory", f"{r.mean_amr_change_pp_per_year:+.1f} pp/year")
cols[3].metric("Context completeness", f"{int(r.context_components_available)}/{int(r.context_components_total)}")

d = amr[amr.country == country].copy()
d["Outcome"] = d.endpoint_id.map(endpoint_label)
fig = px.line(d, x="year", y="standardised_resistance_pct", color="Outcome", markers=True, title="Standardised AMR trajectories", labels={"standardised_resistance_pct":"Resistance (%)","year":"Year"}, color_discrete_sequence=px.colors.qualitative.Safe)
fig.update_yaxes(range=[0,100])
base_layout(fig, 470)
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

st.subheader("2023 context for 2024 AMR")
cards = [
    ("Political-violence events", r.conflict_events_2023, "events", ",.0f"),
    ("Temperature anomaly", r.temperature_anomaly_c_2023, "°C", "+.2f"),
    ("Livestock units", r.livestock_units_2023, "LU", ",.0f"),
    ("Adjusted animal AMU", r.animal_amu_adjusted_mgkg_2023, "mg/kg", ".1f"),
    ("Recipient projects, 2015–2024", r.recipient_projects_2015_2024, "projects", ",.0f"),
    ("Reported recipient funding", r.recipient_funding_usd_2015_2024, "USD", ",.0f"),
]
for row in [cards[:3], cards[3:]]:
    columns = st.columns(3)
    for col, (name, value, unit, fmt) in zip(columns, row):
        shown = "Not available" if pd.isna(value) else f"{format(value, fmt)} {unit}"
        col.metric(name, shown)

st.markdown('<div class="note">No composite vulnerability score is calculated. Components are shown separately so missingness and scientific uncertainty remain visible.</div>', unsafe_allow_html=True)
dataframe_download(d.drop(columns="Outcome"), "Download country AMR estimates", f"{r.iso3}_standardised_amr.csv", "country-download")
footer()
