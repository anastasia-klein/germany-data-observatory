# Analytical data dictionary

## `dim_state.csv`

One row per German federal state. `state_code` is the two-digit federal-state portion of the German official municipality key; `nuts1_code` supports later Eurostat joins and geographic mapping.

## `dim_election.csv`

One row per Bundestag election. `election_id` is the stable primary key used by both election fact tables. The dimension contains the election date and year, Bundestag number, display name, result status, result version and raw source filename. `BTW2021` is explicitly marked `final_after_berlin_repeat_2024`; the other five elections use `official_final`.

## `dim_party.csv`

One row per normalized party label observed in the election facts. `party_id` is a deterministic, text-safe primary key derived from `party_name`. `first_election_year`, `last_election_year` and `election_count` describe coverage in this dataset, not the legal lifetime of the party. The dimension currently contains 81 parties.

## `fact_state_indicators.csv`

Long-form table at state × indicator × year grain. `value` uses a dot decimal separator and `unit` is explicit, making it safe to import into Power Query. Population is currently expressed in thousands because that is the unit published in the source.

## `fact_election_party_results.csv`

One row per election × state × party for second votes in the final 2005, 2009, 2013, 2017, 2021 and 2025 Bundestag election results. `election_id` and `party_id` are foreign keys to their dimensions. `party` is a stable analytical label retained to keep the CSV self-describing; `source_party` retains the original label. Previous-result fields are supplied by the source and refer to its comparable previous election result. The 2021 records contain the current official result after the 2024 repeat election in parts of Berlin.

## `fact_election_turnout.csv`

Two rows per election × state: eligible voters and actual voters. `election_id` is the foreign key to `dim_election.csv`. `share_percent` is populated for voters and blank for eligible voters. A Power BI turnout measure can therefore use the published percentage or divide voters by eligible voters.

## `fact_population_nationality.csv`

One row per state × population group for 31 December 2025. The four groups are `total`, `german`, `non_german` and `eu_member_country`. `share_of` identifies the denominator of a published percentage: non-German share uses total population, while the EU-country share uses the non-German population.

Source concept: population projection based on the 2022 census.

## `fact_foreign_population.csv`

One row per state × year from 2018 through 2025. Counts come from the Central Register of Foreigners (AZR). Some published state values are rounded to five people, so the sum of states may differ from the published Germany control by a few people.

Do not treat `foreign_population_count` as interchangeable with the census-based `non_german` group in `fact_population_nationality.csv`. The definitions and source systems differ.
