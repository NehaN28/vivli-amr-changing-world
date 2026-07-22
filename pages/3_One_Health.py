"""Page 3: One Health Explorer."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from amr_changing_world.dashboard import COLORS, PRIMARY_IDS, base_layout, endpoint_label, endpoint_options, footer, header, load_csv, setup_page

setup_page("One Health Explorer", "🌿")
header("One Health Explorer", "Connected pressures, cautious inference", "Explore temperature, livestock structure and animal antimicrobial use alongside human AMR. All statistical results on this page are secondary or exploratory.")

context = load_csv("country_context.csv.gz")
models = load_csv("one_health_models.csv.gz")
woah = load_csv("woah_models.csv.gz")

country = st.selectbox("Country context (2023 exposure → 2024 AMR)", sorted(context.country))
r = context[context.country == country].iloc[0]
cols = st.columns(5)
cols[0].metric("Mean standardised AMR", f"{r.mean_standardised_resistance_pct_2024:.1f}%")
cols[1].metric("Conflict events", f"{r.conflict_events_2023:,.0f}" if pd.notna(r.conflict_events_2023) else "Not available")
cols[2].metric("Temperature anomaly", f"{r.temperature_anomaly_c_2023:+.2f} °C" if pd.notna(r.temperature_anomaly_c_2023) else "Not available")
cols[3].metric("Livestock units", f"{r.livestock_units_2023/1e6:.1f}M" if pd.notna(r.livestock_units_2023) else "Not available")
cols[4].metric("Animal AMU", f"{r.animal_amu_adjusted_mgkg_2023:.1f} mg/kg" if pd.notna(r.animal_amu_adjusted_mgkg_2023) else "Not available")

shares = pd.DataFrame({"Group": ["Cattle/buffalo", "Poultry", "Swine"], "Share": [r.cattle_buffalo_lu_share_2023, r.poultry_lu_share_2023, r.swine_lu_share_2023]}).dropna()
if len(shares):
    fig = px.bar(shares, x="Share", y="Group", orientation="h", color="Group", title=f"Selected livestock-unit shares in {country}", labels={"Share":"Share of livestock units"}, color_discrete_sequence=[COLORS["teal"], COLORS["gold"], COLORS["coral"]])
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    base_layout(fig, 300)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

st.divider()
opts = endpoint_options(PRIMARY_IDS)
selected = st.selectbox("Modelled primary outcome", list(opts), index=1)
eid = opts[selected]
family = st.radio("Evidence family", ["Temperature and livestock", "Animal antimicrobial use"], horizontal=True)
plot = models[models.endpoint_id == eid].copy() if family == "Temperature and livestock" else woah[woah.endpoint_id == eid].copy()
plot = plot[~plot.analysis.str.contains("Conflict ×", case=False, na=False)].copy()
plot["label"] = plot.analysis + " · " + plot.effect_scale
plot = plot.sort_values("odds_ratio")
fig = go.Figure()
fig.add_vline(x=1, line_dash="dash", line_color="#7C8B92")
fig.add_trace(go.Scatter(x=plot.odds_ratio, y=plot.label, mode="markers", marker=dict(size=10, color=[COLORS["coral"] if x else COLORS["teal"] for x in plot.fdr_significant_005]), error_x=dict(type="data", symmetric=False, array=plot.or_ci_high-plot.odds_ratio, arrayminus=plot.odds_ratio-plot.or_ci_low), customdata=plot[["fdr_p","countries"]], hovertemplate="OR %{x:.2f}<br>FDR p=%{customdata[0]:.3f}<br>Countries=%{customdata[1]}<extra></extra>"))
fig.update_xaxes(title="Odds ratio (95% CI)", type="log")
base_layout(fig, max(360, 56*len(plot)))
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

st.markdown('<div class="note"><b>Result summary:</b> Temperature, total livestock size, animal AMU and all conflict interactions were non-significant after FDR correction. Inverse swine-share associations for the two <i>K. pneumoniae</i> outcomes are ecological and compositional and must not be interpreted as protective or causal.</div>', unsafe_allow_html=True)
st.caption("WOAH models include only 6–14 countries depending on endpoint and are underpowered. Total livestock units are not livestock density because population or land denominators were unavailable.")
footer()
