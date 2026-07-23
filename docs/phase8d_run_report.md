# Phase 8D responsive and visual-quality hardening

Date: 2026-07-23  
Branch: `phase8-redesign`

## Scope

Phase 8D hardens the Phase 8C dashboard for desktop, laptop and mobile use.
It addresses text clipping, compressed metric cards, chart-label collisions,
legend overflow, narrow map colour bars and small-geography visibility. It does
not modify the source data, endpoint definitions, statistical models, estimates
or disclosure rules.

## Responsive layout

- Shared breakpoints cover laptop/tablet widths at 900 px and mobile widths at
  640 px.
- Multi-column rows wrap on narrower displays and become single-column on
  mobile.
- Metric labels and values wrap rather than being ellipsised or clipped.
- Hero, explanatory text, cards and page headings use smaller mobile spacing
  and type sizes.
- Fixed card heights are removed on mobile.

## Chart readability

- All Plotly charts use one responsive rendering configuration.
- Long chart titles are wrapped automatically.
- Axis labels use automatic margins and additional title spacing.
- Legends sit below the plotting area in fixed fractional entries, reducing
  collisions with titles and allowing multi-row wrapping.
- Long endpoint and R&D category labels are split across readable lines.
- Global and One Health country comparison controls consistently allow a
  maximum of five countries.

## Map contract

Every public choropleth now:

- retains the fixed full-world natural-earth viewport;
- leaves countries without data in neutral light grey;
- includes an in-map no-data key;
- uses a horizontal colour bar below the map;
- excludes blank or invalid ISO3 locations;
- adds unobtrusive outlined markers for small geographies with data;
- retains country boundaries, coastlines and surrounding geographic context.

This prevents sparse selections from appearing as isolated floating shapes and
keeps small eligible geographies discoverable by hover.

## State-based verification

Automated application checks covered:

- all seven page entry states;
- the default high-coverage One Health view;
- the lower-coverage animal-AMU view;
- a five-country indexed comparison;
- an empty country selection with an explanatory message;
- map rendering with only two valid countries, including a small island state
  and an invalid blank ISO3 record.

## Verification results

- All seven Streamlit pages rendered without exceptions.
- All 44 automated tests passed.
- Release validation passed.
- Python compilation and Git whitespace checks passed.
- No restricted or isolate-level data were added.

## Final live visual check

The protected local app could not be opened through the cloud browser bridge
because local addresses were blocked by that browser environment. The
responsive behavior was therefore validated through shared CSS/Plotly contract
tests and Streamlit state-based application tests in this phase. A final
pixel-level browser inspection at desktop, laptop and mobile widths remains a
required gate after the redesign branch is deployed as a production candidate
and before it replaces the current live release.
