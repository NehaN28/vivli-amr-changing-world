"""Shared data, labels and visual helpers for the public dashboard."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

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


def setup_page(title: str, icon: str = "🧭") -> None:
    st.set_page_config(page_title=f"{title} | AMR in a changing world", page_icon=icon, layout="wide")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1450px;}
        h1, h2, h3 {color: #173B57; letter-spacing: -0.02em;}
        h1 {font-size: clamp(2rem, 4vw, 3.25rem) !important;}
        [data-testid="stMetric"] {background: white; border: 1px solid #DCE7E5; border-radius: 14px; padding: 1rem;}
        [data-testid="stMetricValue"] {color: #173B57;}
        .eyebrow {color:#0F766E; font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;}
        .lede {font-size:1.08rem; color:#52636C; max-width:850px; margin-bottom:1.4rem;}
        .note {background:#EEF4F3; border-left:4px solid #0F766E; padding:.85rem 1rem; border-radius:0 10px 10px 0; color:#31434B;}
        .warn {background:#FFF7E8; border-left-color:#D39A35;}
        .tier {display:inline-block; background:#E7F1EF; color:#0F766E; padding:.18rem .55rem; border-radius:999px; font-size:.76rem; font-weight:700;}
        .footer {color:#73828A; font-size:.78rem; padding-top:2rem;}
        @media (max-width: 700px) {.block-container {padding: 1rem .85rem 2rem;} h1 {line-height:1.08;} .lede {font-size:.98rem;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(eyebrow: str, title: str, lede: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="lede">{lede}</div>', unsafe_allow_html=True)


def base_layout(fig: go.Figure, height: int = 470) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#31434B"),
        hoverlabel=dict(bgcolor="white", font_size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#D7E2E0")
    fig.update_yaxes(gridcolor="#E7EEED", zeroline=False)
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
