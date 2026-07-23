"""Landing page for the AMR in a Changing World data product."""

import streamlit as st

from amr_changing_world.dashboard import ROOT, footer, load_table, setup_page

setup_page("Home", "🧭")

coverage = load_table("endpoint_coverage")
one_health = load_table("one_health_country_year")
availability = load_table("coverage_summary")

st.markdown('<div class="eyebrow">Vivli 2026 AMR Data Challenge</div>', unsafe_allow_html=True)
st.title("Human AMR trends in a changing world")
st.markdown(
    """
    <div class="hero">
      <p><b>Developed for the Vivli AMR Data Challenge 2026.</b> This interactive research platform links human clinical resistance surveillance with political violence, climate, livestock systems, animal antimicrobial use and global AMR R&amp;D investment.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clinical endpoints", f"{len(coverage)}")
c2.metric("Eligible isolates", f"{int(coverage.eligible_tested_isolates.sum()):,}")
c3.metric("Countries with AMR", f"{one_health.iso3.nunique():,}")
c4.metric("Annual linked records", f"{len(one_health):,}")

st.subheader("The question")
st.write(
    "Antimicrobial resistance does not evolve in isolation. Health-system disruption, environmental "
    "change, animal antimicrobial use, livestock systems and the distribution of research investment "
    "may all shape the conditions in which resistance emerges and spreads. This project asks how "
    "human AMR trajectories vary across countries and what national indicators of these wider forces "
    "can tell us about their context."
)
st.write(
    "The dashboard integrates fragmented global datasets in one reproducible platform so users can "
    "compare trends, identify divergent country trajectories and see where linked evidence is strong "
    "or limited. It is designed for exploration and hypothesis generation; ecological associations "
    "are not treated as proof of causation."
)

st.subheader("Explore in three steps")
cards = st.columns(3)
with cards[0]:
    st.markdown('<div class="step-card"><b>1 · Start with AMR</b><br><br>Choose a clinically selected organism–drug endpoint. Review its isolate, country and year coverage before interpreting maps or trends.</div>', unsafe_allow_html=True)
with cards[1]:
    st.markdown('<div class="step-card"><b>2 · Add context</b><br><br>Compare up to five countries over time against conflict or a selected One Health indicator. Missing linked data remain visible.</div>', unsafe_allow_html=True)
with cards[2]:
    st.markdown('<div class="step-card"><b>3 · Read the evidence tier</b><br><br>Confirmatory results are separated from exploratory models and descriptive patterns. Effect size, uncertainty and coverage travel together.</div>', unsafe_allow_html=True)

st.subheader("What the analysis found")
f1, f2, f3 = st.columns(3)
f1.metric("Increasing trajectories", "82")
f2.metric("Decreasing trajectories", "94")
f3.metric("No clear linear change", "511")
st.markdown(
    '<div class="note"><b>Central insight:</b> AMR trajectories are heterogeneous and linked-data '
    'coverage is uneven. None of the four prespecified conflict associations was significant after '
    'multiplicity correction. One of 144 exploratory One Health lag models survived FDR correction, '
    'but it used only 15 countries and is treated as hypothesis-generating.</div>',
    unsafe_allow_html=True,
)

st.subheader("Five connected data sources")
st.markdown(
    """
    - **ATLAS:** aggregated human clinical isolate susceptibility data
    - **ACLED:** recorded political-violence events by country and year
    - **FAOSTAT:** temperature anomalies and livestock structure
    - **WOAH:** reported antimicrobial use in animals
    - **Global AMR R&D Hub:** reported research projects and commitments
    """
)

with st.expander("What this dashboard can and cannot show"):
    st.write(
        "It can reveal temporal patterns, compare countries, expose coverage gaps and support "
        "hypothesis generation. It cannot estimate population prevalence, attribute a national "
        "trend to a single exposure, rank health systems, or replace patient-level and subnational studies."
    )
    st.write(
        "All public AMR country-year cells contain at least 30 tested isolates. Restricted "
        "isolate-level ATLAS data are not included in the application."
    )

st.subheader("Project team")
st.caption(
    "Clinical microbiologists combining AMR, infectious-disease and data-science expertise."
)
team = st.columns(2)
with team[0]:
    photo, biography = st.columns([1, 2.25])
    with photo:
        st.image(
            ROOT / "assets" / "team" / "neha_nityadarshini.png",
            caption="Dr. Neha Nityadarshini",
            width="stretch",
        )
    with biography:
        st.markdown("#### Dr. Neha Nityadarshini")
        st.markdown('<span class="tier">Team Lead</span>', unsafe_allow_html=True)
        st.write(
            "Clinical microbiologist and Senior Scientific Consultant with the National One Health "
            "Mission at ICMR Headquarters, India. Her work focuses on AMR analytics, One Health "
            "surveillance, metagenomics, machine learning and scientific data visualisation."
        )

with team[1]:
    photo, biography = st.columns([1, 2.25])
    with photo:
        st.image(
            ROOT / "assets" / "team" / "jaya_biswas.png",
            caption="Dr. Jaya Biswas",
            width="stretch",
        )
    with biography:
        st.markdown("#### Dr. Jaya Biswas")
        st.markdown('<span class="tier">Team Member</span>', unsafe_allow_html=True)
        st.write(
            "Clinical microbiologist and Assistant Professor of Microbiology at AIIMS-CAPFIMS, "
            "India. Her interests include antimicrobial resistance, clinical diagnostics, "
            "mycobacteriology and the application of artificial intelligence to infectious-disease "
            "diagnostics and surveillance."
        )

st.caption(
    "The project team is solely responsible for the analyses, interpretations and dashboard design."
)

footer()
