# Phase 8C dashboard redesign

Date: 2026-07-23  
Branch: `phase8-redesign`

## Scope

Phase 8C converts the validated Phase 8A annual tables and Phase 8B exploratory
outputs into a self-explanatory scientific data product. It does not modify the
four locked confirmatory conflict models or any Phase 8B estimate.

## Information architecture

- A new landing page states the research question, linked sources, intended use,
  central findings and interpretation boundaries.
- Navigation begins at `Start here`, followed by the six analytical and methods pages.
- The Global AMR selector displays analysis tier and eligible isolate coverage.
- Endpoint detail shows isolates, countries, country-years, time span, phenotype
  and inclusion rationale.

## Longitudinal explorers

- The One Health page aligns annual AMR, the selected indicator and isolate
  volume on a shared year axis for up to five countries.
- Temperature, livestock units/composition and animal AMU are available in
  absolute and indexed views.
- Missing observations remain as gaps.
- Exploratory lag estimates retain coverage, confidence intervals and FDR q values.
- The R&D page displays annual portfolio trends by sector, research area or
  pathogen and annual recipient-country comparisons.
- Missing reported commitments are not treated as zero.

## Map contract

Every redesigned choropleth:

- retains a fixed full-world natural-earth viewport;
- displays all land and country boundaries;
- renders countries without data in neutral grey;
- separates missing from low or zero values;
- avoids data-driven zoom that makes countries appear as floating shapes.

## Scientific interpretation contract

- The four locked primary endpoints and the `n >= 30` public threshold remain unchanged.
- Confirmatory, secondary and exploratory evidence remain distinct.
- Country estimates are not presented as population prevalence.
- Ecological associations are not described as causal.
- Nominal signals are not highlighted without multiplicity, coverage and uncertainty.
- No composite vulnerability score or country ranking is introduced.

## Verification

- All Phase 8 dashboard tables are aggregated and disclosure-safe.
- The Streamlit entry point and all seven pages ran without exceptions.
- The complete automated test suite passed.
