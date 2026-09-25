# German Public EV Charging Rollout vs. EV Registration Growth

Does Germany's public charging network track where electric vehicles actually are? This project joins the Bundesnetzagentur's national charging station register with KBA (Kraftfahrt-Bundesamt) vehicle registration statistics to measure infrastructure supply against EV demand, state by state.

## Data Sources

- **Bundesnetzagentur Ladesäulenregister** (public charging point register), snapshot 2026-09-01. 116,443 individual charging point records: location, operator, power rating, connector type, coordinates.
- **KBA FZ14 — Pkw mit Elektroantrieb** (EV passenger car registrations), by Zulassungsbezirk (registration district) and by region/state, quarterly time series through 2025 Q1 (latest published KBA data at time of writing).
- **KBA vehicle density register** (Fahrzeugdichte), used to derive a population estimate per state for per-capita normalization.

All three are official German government open data.

## Pipeline

Bronze → Silver → Gold, in Python/pandas (DuckDB-compatible logic, run locally for cost reasons; SQL-equivalent joins would map directly to BigQuery/dbt models):

- **Bronze:** raw ingestion of all three source files as-is.
- **Silver:** type-cleaning, numeric parsing (German decimal commas), deriving a `is_fast` flag for DC charging ≥43kW, aggregating charging points and EV registrations to state (Bundesland) level, deriving population estimates from vehicle density figures.
- **Gold:** state-level join across all three sources (clean match on all 16 states), computing:
  - Charge points per 100,000 residents
  - Charge points per 1,000 registered EVs (the core infrastructure-to-demand ratio)
  - Share of charging locations offering DC fast charging
  - EV share of each state's total registered car fleet
  - National EV adoption trend over time

## Key Findings

**Infrastructure doesn't track adoption — it runs opposite to it.** The states with the *fewest* EVs on the road (Mecklenburg-Vorpommern, Thüringen, Sachsen-Anhalt — all under 4% EV share) have the *most* charge points per EV (93-111 per 1,000 EVs). The states with the strongest EV adoption (Hamburg 8.3%, Baden-Württemberg 6.9%, Hessen 6.9%) fall in the bottom half of that same ratio (46-89 per 1,000 EVs).

**Saarland is the clearest outlier**, with the lowest infrastructure ratio nationally (46 charge points per 1,000 EVs) despite mid-table EV adoption (5.0%).

**Fast charging coverage varies more by state policy than by demand**: Sachsen-Anhalt and Saarland lead (>65% of locations offer DC fast charging), while Berlin trails badly (21.5%) despite having the second-highest raw charge-point density per capita — Berlin's network favors AC/slower charging.

**National EV adoption has accelerated**, from 1.9% of the registered fleet in early 2023 to 3.0% by the most recent KBA quarter, with the growth rate visibly steepening in the last two reported quarters.

## Charts

- `chart_infra_ratio_by_state.png` — charge points per 1,000 EVs, ranked, with national median
- `chart_density_vs_adoption.png` — per-capita infrastructure density vs. EV adoption rate, scatter by state
- `chart_fast_charging_share.png` — DC fast-charging coverage by state
- `chart_national_ev_growth.png` — national EV fleet share over time

## Caveats

- KBA registration data is published with a lag; the latest available quarter here is 2025 Q1, while the charging register snapshot is from September 2026. The infrastructure side is therefore somewhat ahead in time of the registration side — a limitation of public data cadence, not the analysis.
- Population estimates are derived indirectly from vehicle density figures rather than pulled from a dedicated population dataset, since KBA doesn't publish population directly; Destatis population figures would be a cleaner join in a future iteration.
- DC fast charging is defined here as ≥43kW nominal power, a standard industry threshold, but the register does not label "fast" vs "slow" directly.

## Tools

Python, pandas, matplotlib. Structured as a Bronze/Silver/Gold pipeline consistent with dbt/BigQuery modeling conventions, matching the approach used in the [German Motorcycle Market Analysis](https://github.com/KiranDarshak/germany-motorcycle-market-analysis) project.
