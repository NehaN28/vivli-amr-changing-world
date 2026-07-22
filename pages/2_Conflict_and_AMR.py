"""Page 2: Conflict and AMR."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from amr_changing_world.dashboard import (
    COLORS, PRIMARY_IDS, base_layout, dataframe_download, endpoint_label,
    endpoint_options, footer, header, load_csv, no_data, setup_page,
)

setup_page("Conflict and AMR", "⚖️")
header("Conflict and AMR", "Political violence and resistance", "View aligned country timelines and the four prespecified fixed-effects estimates. Temporal association does not automatically establish causation.")

amr = load_csv("standardised_amr.csv.gz")
conflict = load_csv("acled_country_year.csv.gz")
models = load_csv("main_conflict_models.csv.gz")
events = load_csv("event_trajectories.csv.gz")

opts = endpoint_options(PRIMARY_IDS)
c1, c2 = st.columns([1, 1])
with c1:
    selected_label = st.selectbox("Primary outcome", list(opts), index=0)
    eid = opts[selected_label]
with c2:
    available = sorted(amr.loc[amr.endpoint_id == eid, "country"].unique())
    country = st.selectbox("Country", available)

left, right = st.columns([1.55, 1])
with left:
    a = amr[(amr.endpoint_id == eid) & (amr.country == country)].sort_values("year")
    c = conflict[conflict.iso3 == a.iso3.iloc[0]].copy() if len(a) else conflict.iloc[0:0]
    if a.empty:
        no_data()
    else:
        c = c[c.year.between(int(a.year.min()) - 1, int(a.year.max()) - 1)]
        c["outcome_year"] = c.year + 1
        merged = a.merge(c[["outcome_year", "annual_events"]], left_on="year", right_on="outcome_year", how="left")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=merged.year, y=merged.annual_events, name="Conflict events (preceding year)", marker_color="rgba(211,154,53,.42)"), secondary_y=True)
        fig.add_trace(go.Scatter(x=merged.year, y=merged.standardised_resistance_pct, name="Standardised resistance", mode="lines+markers", line=dict(color=COLORS["teal"], width=3), error_y=dict(type="data", symmetric=False, array=merged.standardised_ci_high-merged.standardised_resistance_pct, arrayminus=merged.standardised_resistance_pct-merged.standardised_ci_low)), secondary_y=False)
        fig.update_yaxes(title_text="Resistance (%)", range=[0, 100], secondary_y=False)
        fig.update_yaxes(title_text="Political-violence events", rangemode="tozero", secondary_y=True, showgrid=False)
        fig.update_xaxes(title="AMR outcome year")
        fig.update_layout(title=f"{country}: aligned annual timeline")
        base_layout(fig, 500)
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
with right:
    st.subheader("Model estimate")
    row = models[models.endpoint_id == eid].iloc[0]
    st.metric("OR per doubling of 1 + events", f"{row.or_per_doubling_1plus_events:.3f}")
    st.write(f"95% CI: **{row.or_ci_low:.3f}–{row.or_ci_high:.3f}**")
    st.write(f"Holm-adjusted p value: **{row.holm_p:.3f}**")
    st.write(f"{int(row.countries)} countries · {int(row.country_year_cells)} country-years · {int(row.tested_isolates):,} isolates")
    st.markdown('<div class="note warn"><b>Main result:</b> No primary association was statistically significant after multiplicity correction. This is absence of a detectable association in the available sample, not proof of no effect.</div>', unsafe_allow_html=True)

st.subheader("Confirmatory estimates")
plot = models.sort_values("or_per_doubling_1plus_events").copy()
plot["label"] = plot.endpoint_id.map(endpoint_label)
fig = go.Figure()
fig.add_vline(x=1, line_dash="dash", line_color="#7C8B92")
fig.add_trace(go.Scatter(x=plot.or_per_doubling_1plus_events, y=plot.label, mode="markers", marker=dict(size=11, color=COLORS["teal"]), error_x=dict(type="data", symmetric=False, array=plot.or_ci_high-plot.or_per_doubling_1plus_events, arrayminus=plot.or_per_doubling_1plus_events-plot.or_ci_low), hovertemplate="OR %{x:.3f}<extra></extra>"))
fig.update_xaxes(title="Adjusted odds ratio per exposure doubling")
base_layout(fig, 330)
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

with st.expander("Exploratory escalation trajectories"):
    st.caption("Only 17 minimally usable endpoint-windows across five countries were available. These are descriptive, not pooled causal estimates.")
    st.dataframe(events, width="stretch", hide_index=True)
    dataframe_download(events, "Download trajectories", "exploratory_escalation_trajectories.csv", "events-download")

footer()
