"""Shared data, labels and visual helpers for the public dashboard."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from textwrap import wrap

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "dashboard"

ENDPOINTS = {
    "ECO_CAZ_R": ("Escherichia coli", "Ceftazidime", "Primary"),
    "KPN_CAZ_R": ("Klebsiella pneumoniae", "Ceftazidime", "Primary"),
    "KPN_MEM_R": ("Klebsiella pneumoniae", "Meropenem", "Primary"),
    "ABA_MEM_R": ("Acinetobacter baumannii", "Meropenem", "Primary"),
    "ECO_MEM_R": ("Escherichia coli", "Meropenem", "Secondary"),
    "PAE_MEM_R": ("Pseudomonas aeruginosa", "Meropenem", "Secondary"),
    "SAU_OXA_R": ("Staphylococcus aureus", "Oxacillin", "Secondary"),
    "EFA_VAN_R": ("Enterococcus faecium", "Vancomycin", "Exploratory"),
    "SPN_ERY_R": ("Streptococcus pneumoniae", "Erythromycin", "Secondary"),
    "HIN_AMP_R": ("Haemophilus influenzae", "Ampicillin", "Exploratory"),
    "GAS_ERY_R": ("Streptococcus pyogenes", "Erythromycin", "Exploratory"),
    "ECO_CIP_R": ("Escherichia coli", "Ciprofloxacin", "Secondary"),
    "KPN_CIP_R": ("Klebsiella pneumoniae", "Ciprofloxacin", "Secondary"),
    "ECO_GEN_R": ("Escherichia coli", "Gentamicin", "Secondary"),
    "KPN_GEN_R": ("Klebsiella pneumoniae", "Gentamicin", "Secondary"),
    "ECO_COL_R": ("Escherichia coli", "Colistin", "Exploratory"),
    "KPN_COL_R": ("Klebsiella pneumoniae", "Colistin", "Exploratory"),
}
PRIMARY_IDS = [key for key, value in ENDPOINTS.items() if value[2] == "Primary"]

COLORS = {
    "teal": "#0F766E",
    "navy": "#173B57",
    "blue": "#3B82A0",
    "gold": "#D39A35",
    "coral": "#D46A5E",
    "grey": "#6B7B83",
    "light": "#E7F1EF",
}
COUNTRY_COLORS = [
    "#0F766E", "#D39A35", "#3B82A0", "#D46A5E", "#705C99"
]
SMALL_GEOGRAPHY_COORDS = {
    "CYP": (35.13, 33.43),
    "DMA": (15.42, -61.37),
    "HKG": (22.32, 114.17),
    "LUX": (49.82, 6.13),
    "MLT": (35.94, 14.38),
    "MUS": (-20.20, 57.50),
    "PRI": (18.22, -66.59),
    "PSE": (31.95, 35.23),
    "QAT": (25.29, 51.18),
    "REU": (-21.12, 55.54),
    "SGP": (1.35, 103.82),
    "VCT": (13.25, -61.20),
}

DASHBOARD_CSS = """
<style>
.block-container {
    padding-top: 1.7rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}
h1, h2, h3 {
    color: #173B57;
    letter-spacing: -0.02em;
    overflow-wrap: anywhere;
}
h1 {
    font-size: clamp(2rem, 4vw, 3.25rem) !important;
    line-height: 1.08 !important;
}
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #DCE7E5;
    border-radius: 14px;
    min-height: 7.4rem;
    padding: .9rem 1rem;
}
[data-testid="stMetricLabel"] {
    min-height: 2.5rem;
    white-space: normal;
    line-height: 1.25;
    overflow-wrap: anywhere;
}
[data-testid="stMetricValue"] {
    color: #173B57;
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.12;
    font-size: clamp(1.2rem, 1.8vw, 1.85rem);
}
[data-testid="stPlotlyChart"] {
    overflow: visible;
}
.eyebrow {
    color: #0F766E;
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.lede {
    font-size: 1.08rem;
    line-height: 1.58;
    color: #52636C;
    max-width: 900px;
    margin-bottom: 1.4rem;
}
.note {
    background: #EEF4F3;
    border-left: 4px solid #0F766E;
    padding: .85rem 1rem;
    border-radius: 0 10px 10px 0;
    color: #31434B;
    line-height: 1.5;
}
.warn {
    background: #FFF7E8;
    border-left-color: #D39A35;
}
.tier {
    display: inline-block;
    background: #E7F1EF;
    color: #0F766E;
    padding: .18rem .55rem;
    border-radius: 999px;
    font-size: .76rem;
    font-weight: 700;
}
.hero {
    background: linear-gradient(135deg,#173B57 0%,#0F766E 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    margin: .5rem 0 1.4rem;
}
.hero h1 {
    color: white !important;
    margin: 0 0 .6rem;
}
.hero p {
    font-size: 1.08rem;
    line-height: 1.55;
    max-width: 900px;
    margin: 0;
    opacity: .94;
}
.step-card {
    background: #F7FAF9;
    border: 1px solid #DCE7E5;
    border-radius: 14px;
    padding: 1rem;
    min-height: 150px;
    line-height: 1.45;
}
[data-testid="stImage"] img {
    border-radius: 14px;
    border: 1px solid #DCE7E5;
}
.footer {
    color: #73828A;
    font-size: .78rem;
    line-height: 1.45;
    padding-top: 2rem;
}
@media (max-width: 900px) {
    .block-container {
        padding: 1.25rem 1rem 2.5rem;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        gap: .85rem;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 245px !important;
        min-width: min(100%, 245px) !important;
        width: auto !important;
    }
    [data-testid="stMetric"] {
        min-height: 6.8rem;
    }
}
@media (max-width: 640px) {
    .block-container {
        padding: .9rem .75rem 2rem;
    }
    h1 {
        font-size: 2rem !important;
    }
    h2 {
        font-size: 1.45rem !important;
    }
    .lede, .hero p {
        font-size: .96rem;
    }
    .hero {
        padding: 1.25rem;
        border-radius: 14px;
    }
    .step-card {
        min-height: 0;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex-basis: 100% !important;
        min-width: 100% !important;
    }
    [data-testid="stMetricLabel"] {
        min-height: 0;
    }
    [data-testid="stMetric"] {
        min-height: 0;
    }
}
</style>
"""

CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def endpoint_label(endpoint_id: str, italic: bool = False) -> str:
    species, drug, _ = ENDPOINTS.get(endpoint_id, (endpoint_id, "", ""))
    if italic:
        return f"<i>{species}</i> – {drug}"
    return f"{species} – {drug}"


def endpoint_options(ids: list[str] | None = None) -> dict[str, str]:
    ids = ids or list(ENDPOINTS)
    return {endpoint_label(i): i for i in ids}


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(f"Dashboard data file is missing: {path.name}")
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    """Load a dashboard table by basename, preferring compact Parquet."""
    parquet = DATA / f"{name}.parquet"
    if parquet.exists():
        return pd.read_parquet(parquet)
    return load_csv(f"{name}.csv.gz")


def setup_page(title: str, icon: str = "🧭") -> None:
    st.set_page_config(page_title=f"{title} | AMR in a changing world", page_icon=icon, layout="wide")
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


def header(eyebrow: str, title: str, lede: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="lede">{lede}</div>', unsafe_allow_html=True)


def _wrap_plot_text(value: object, width: int = 58) -> object:
    """Add HTML line breaks to long Plotly labels without changing short labels."""
    if not isinstance(value, str) or "<br>" in value or len(value) <= width:
        return value
    return "<br>".join(wrap(value, width=width, break_long_words=False))


def base_layout(fig: go.Figure, height: int = 470) -> go.Figure:
    title = fig.layout.title.text
    has_legend = any(
        trace.showlegend is not False and trace.name not in (None, "")
        for trace in fig.data
    )
    layout = dict(
        height=height,
        margin=dict(l=64, r=32, t=82, b=120 if has_legend else 52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#31434B"),
        hoverlabel=dict(bgcolor="white", font_size=13),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="left",
            x=0,
            font=dict(size=11),
            title=dict(font=dict(size=11)),
        ),
        hovermode="closest",
    )
    if title:
        layout["title"] = dict(
            text=_wrap_plot_text(title),
            x=0,
            xanchor="left",
            font=dict(size=18),
        )
    fig.update_layout(**layout)
    fig.update_xaxes(
        showgrid=False,
        linecolor="#D7E2E0",
        automargin=True,
        title_standoff=12,
    )
    fig.update_yaxes(
        gridcolor="#E7EEED",
        zeroline=False,
        automargin=True,
        title_standoff=12,
    )
    return fig


def plotly_chart(fig: go.Figure, *, key: str | None = None) -> None:
    """Render a responsive chart with a consistent, uncluttered mode bar."""
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG, key=key)


def world_choropleth(
    df: pd.DataFrame,
    value: str,
    title: str,
    colorbar_title: str,
    *,
    hover_name: str = "country",
    range_color: tuple[float, float] | None = None,
    colorscale: list[str] | str | None = None,
    hover_data: dict[str, object] | None = None,
    height: int = 510,
) -> go.Figure:
    """Create a stable full-world map with an explicit neutral no-data context."""
    valid_iso3 = df["iso3"].fillna("").astype(str).str.fullmatch(r"[A-Z]{3}")
    clean = df.loc[valid_iso3].dropna(subset=[value]).copy()
    hover_columns = [column for column in (hover_data or {}) if column in clean.columns]
    hover_template = f"<b>%{{text}}</b><br>{colorbar_title}: %{{z:,.2f}}"
    for index, column in enumerate(hover_columns):
        label = column.replace("_", " ").title()
        hover_template += f"<br>{label}: %{{customdata[{index}]}}"
    hover_template += "<extra></extra>"
    fig = go.Figure(
        go.Choropleth(
            locations=clean["iso3"],
            z=clean[value],
            text=clean[hover_name],
            customdata=clean[hover_columns],
            colorscale=colorscale or ["#E7F1EF", "#65AFA7", "#173B57"],
            zmin=range_color[0] if range_color else None,
            zmax=range_color[1] if range_color else None,
            marker_line_color="white",
            marker_line_width=0.35,
            colorbar=dict(
                title=dict(text=_wrap_plot_text(colorbar_title, 36), side="top"),
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.04,
                yanchor="top",
                len=0.62,
                thickness=12,
                outlinewidth=0,
            ),
            hovertemplate=hover_template,
        )
    )
    small = clean[clean["iso3"].isin(SMALL_GEOGRAPHY_COORDS)].copy()
    if not small.empty:
        coordinates = small["iso3"].map(SMALL_GEOGRAPHY_COORDS)
        small["latitude"] = coordinates.map(lambda point: point[0])
        small["longitude"] = coordinates.map(lambda point: point[1])
        marker_customdata = small[[value, *hover_columns]]
        marker_hover = f"<b>%{{text}}</b><br>{colorbar_title}: %{{customdata[0]:,.2f}}"
        for index, column in enumerate(hover_columns, start=1):
            label = column.replace("_", " ").title()
            marker_hover += f"<br>{label}: %{{customdata[{index}]}}"
        marker_hover += "<extra></extra>"
        fig.add_trace(
            go.Scattergeo(
                lon=small["longitude"],
                lat=small["latitude"],
                text=small[hover_name],
                customdata=marker_customdata,
                mode="markers",
                marker=dict(
                    size=7,
                    color="white",
                    line=dict(color="#173B57", width=1.5),
                ),
                hovertemplate=marker_hover,
                showlegend=False,
            )
        )
    fig.update_geos(
        scope="world",
        projection_type="natural earth",
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#AAB8BD",
        coastlinewidth=0.5,
        showland=True,
        landcolor="#E9EEEF",
        showcountries=True,
        countrycolor="white",
        countrywidth=0.45,
        showocean=True,
        oceancolor="#F7FAFB",
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85],
        lonaxis_range=[-180, 180],
    )
    fig.update_layout(
        title=title,
        geo=dict(fitbounds=False, domain=dict(y=[0.1, 1])),
        annotations=[
            dict(
                text="Light grey = no data",
                x=0,
                y=0.01,
                xref="paper",
                yref="paper",
                showarrow=False,
                bgcolor="rgba(255,255,255,.9)",
                bordercolor="#DCE7E5",
                borderwidth=1,
                borderpad=4,
                font=dict(size=11, color="#52636C"),
            ),
            *(
                [
                    dict(
                        text="Outlined circles = small geographies with data",
                        x=1,
                        y=0.01,
                        xref="paper",
                        yref="paper",
                        xanchor="right",
                        showarrow=False,
                        bgcolor="rgba(255,255,255,.9)",
                        bordercolor="#DCE7E5",
                        borderwidth=1,
                        borderpad=4,
                        font=dict(size=11, color="#52636C"),
                    )
                ]
                if not small.empty
                else []
            ),
        ],
    )
    base_layout(fig, height)
    fig.update_layout(margin=dict(l=18, r=18, t=82, b=72), showlegend=False)
    return fig


def no_data(message: str = "No data are available for this selection.") -> None:
    st.info(message, icon="ℹ️")


def dataframe_download(df: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


def footer() -> None:
    st.markdown(
        '<div class="footer">Vivli 2026 AMR Data Challenge · Aggregated, disclosure-checked outputs · Cells with fewer than 30 isolates are suppressed</div>',
        unsafe_allow_html=True,
    )
