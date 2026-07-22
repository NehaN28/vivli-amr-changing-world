"""Page 6: Methods and data quality."""

import streamlit as st

from amr_changing_world.dashboard import excel_bytes, footer, header, load_csv, setup_page

setup_page("Methods and Data Quality", "📘")
header("Methods and Data Quality", "How to read this dashboard", "Definitions, inclusion rules, statistical methods, limitations and downloadable disclosure-safe results.")

tabs = st.tabs(["Study design", "Outcomes", "Models", "Data quality", "Limitations", "Downloads"])
with tabs[0]:
    st.subheader("Design")
    st.write("Longitudinal ecological analysis of human clinical isolates linked by country and year to political violence, temperature, livestock structure, animal antimicrobial use and AMR R&D investment.")
    st.markdown("""
    - Primary AMR outcome years: **2019–2024**
    - Primary exposure: preceding-year **log₂(1 + ACLED political-violence events)**
    - Primary design: endpoint-specific unbalanced panel
    - Eligible country-year: at least **30 tested isolates**, complete lagged exposure, at least three eligible years, and within-country exposure variation
    - Confirmatory sample: **809 country-year-endpoint cells**, **98,562 endpoint-level records**, **69,547 unique isolates**
    """)
with tabs[1]:
    st.subheader("Four confirmatory outcomes")
    st.markdown("""
    1. *Escherichia coli*–ceftazidime resistance
    2. *Klebsiella pneumoniae*–ceftazidime resistance
    3. *K. pneumoniae*–meropenem resistance
    4. *Acinetobacter baumannii*–meropenem resistance
    """)
    st.info("Ceftazidime is the prespecified 2018–2024 operational indicator for third-generation cephalosporin resistance in ATLAS. It is not presented as interchangeable with ceftriaxone.")
with tabs[2]:
    st.subheader("Statistical analysis")
    st.write("Primary associations were estimated using isolate-level logistic regression with country and calendar-year fixed effects and country-clustered uncertainty. Models adjusted for age group, sex, specimen group and clinical specialty. Holm correction covered the four confirmatory coefficients.")
    st.write("Country-year standardised resistance was derived using partially pooled models, holding patient and specimen composition to a common distribution while retaining each country-year's calendar year. Phase 5 models are secondary or exploratory and use family-specific FDR correction.")
with tabs[3]:
    st.subheader("Built-in safeguards")
    st.markdown("""
    - MIC inequalities retained as censoring bounds
    - Missing exposure values never converted to zero
    - ACLED zero-event months reconstructed only after official coverage began
    - Small ATLAS cells suppressed when **n < 30**
    - Raw and isolate-level ATLAS data excluded from the public application
    - Country harmonisation uses reviewed ISO3 mappings
    - R&D projects deduplicated and fractionally allocated across categories
    - Dashboard tables originate from the same pipeline as manuscript results
    """)
with tabs[4]:
    st.subheader("Important limitations")
    st.markdown("""
    - Clinical isolate surveillance is not population-representative.
    - Residual confounding, changing testing practices and selection into surveillance remain possible.
    - Country-year ecological relationships cannot identify patient-level mechanisms.
    - ACLED events measure recorded political violence, not the full humanitarian impact of conflict.
    - WOAH animal-AMU coverage is limited to 6–14 countries in modelled subsets.
    - Livestock totals are not density measures because population or land denominators were unavailable.
    - Recipient-institution country is not necessarily the research site or beneficiary country.
    - A non-significant result is not proof of no effect.
    """)
with tabs[5]:
    st.subheader("Disclosure-safe downloads")
    files = {
        "Standardised AMR": load_csv("standardised_amr.csv.gz"),
        "Main conflict models": load_csv("main_conflict_models.csv.gz"),
        "Country context": load_csv("country_context.csv.gz"),
        "One Health models": load_csv("one_health_models.csv.gz"),
        "WOAH models": load_csv("woah_models.csv.gz"),
        "R&D pathogen alignment": load_csv("rd_pathogen.csv.gz"),
    }
    st.download_button("Download core results workbook", excel_bytes(files), file_name="AMR_changing_world_dashboard_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("The workbook contains aggregated estimates and model results only. Restricted isolate-level data are not included.")

st.markdown('<div class="note warn"><b>Responsible use:</b> The dashboard is designed for hypothesis generation, comparative context and transparent reporting. It should not be used to rank health systems or infer causation from a single country trend.</div>', unsafe_allow_html=True)
footer()
