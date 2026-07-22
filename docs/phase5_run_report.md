# Phase 5 One Health and R&D analyses

Analysis date: 23 July 2026

Pipeline version: 0.5.0

Status: Secondary and exploratory analyses

## One Health results

Forty isolate-level models evaluated lagged temperature anomaly, total livestock units, cattle/buffalo, poultry and swine livestock-unit shares, and their interactions with preceding-year conflict. Models retained the locked Phase 4 country/year fixed effects and isolate-composition adjustment. Benjamini–Hochberg correction was applied separately to main effects and interactions.

No temperature, livestock-size or conflict-interaction coefficient survived correction. Two inverse swine-share associations remained: *K. pneumoniae* ceftazidime resistance, adjusted OR 0.688 per 10-percentage-point share increase (95% CI 0.551–0.859; FDR p=0.0149), and *K. pneumoniae* meropenem resistance, OR 0.458 (95% CI 0.306–0.686; FDR p=0.0068). These are compositional ecological associations and are not interpreted as protective or causal.

Total livestock units are explicitly described as system size, not livestock density, because population and agricultural-land denominators were not supplied.

## WOAH results

The lagged WOAH complete-case subsets contained 14 countries for *E. coli*, 13 for each *K. pneumoniae* outcome and 6 for *A. baumannii*. No adjusted or unadjusted total animal-AMU association, cephalosporin proxy association or conflict interaction survived FDR correction. The all-generation cephalosporin series was used as a proxy for ceftazidime outcomes because the exported 3rd/4th-generation series contained zero values. No carbapenem-specific class was available.

## R&D alignment

Projects starting in 2015–2024 were fractionally allocated across pathogens, sectors and research areas to prevent multiple counting. Human-sector research represented 86.5% of funding, animal 7.6% and environment 2.6%. Cross-sector projects represented 6.9% of reported funding.

Among mapped pathogen-specific funding, *S. aureus* received 26.1%, *E. coli* 24.3%, *P. aeruginosa* 22.7%, *K. pneumoniae* 9.2% and *A. baumannii* 8.4%. *A. baumannii* had the highest 2024 standardised resistance among the three directly comparable primary pathogens. This is reported as an attention-alignment signal, not proof of underfunding.

## Dashboard framework

The country context table retains separate AMR level, AMR trajectory, conflict, temperature, livestock, WOAH AMU, R&D capacity and coverage components. No composite vulnerability score is calculated. The table includes 42 countries with 2024 standardised AMR data and explicitly records component availability.

## Quality assurance

All 60 Phase 5 statistical models converged. Thirteen automated tests passed. The report was rendered and visually checked page by page. Every workbook sheet was rendered, the summary formulas were inspected, and the formula-error scan found no matches.
