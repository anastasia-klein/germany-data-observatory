# Analytical data dictionary

## `dim_state.csv`

One row per German federal state. `state_code` is the two-digit federal-state portion of the German official municipality key; `nuts1_code` supports later Eurostat joins and geographic mapping.

## `dim_election.csv`

One row per Bundestag election. `election_id` is the stable primary key used by both election fact tables. The dimension contains the election date and year, Bundestag number, display name, result status, result version and raw source filename. `BTW2021` is explicitly marked `final_after_berlin_repeat_2024`; the other five elections use `official_final`.

## `dim_party.csv`

One row per normalized party label observed in the election facts. `party_id` is a deterministic, text-safe primary key derived from `party_name`. `first_election_year`, `last_election_year` and `election_count` describe coverage in this dataset, not the legal lifetime of the party. Report-focus parties, including Volt, receive stable colour and display-order attributes; all other parties use a neutral fallback. The dimension currently contains 81 parties.

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

## District analytical layer

### `dim_district.csv`

One row per current Kreis or kreisfreie Stadt. `district_id` is the five-digit AGS key, `state_code` is its two-digit state prefix and `district_type` distinguishes urban, rural and special district associations. The current boundary reference year is 2024.

### `dim_district_feature.csv` and `fact_district_features.csv`

The feature dimension documents 14 Regionalatlas indicators, including unit, reference year, source table, clustering inclusion, transform and any exclusion reason. The fact table has one row per district × feature and 5,600 complete observations.

### `fact_cluster_assignment.csv`, `dim_cluster.csv` and `cluster_profiles.csv`

The assignment table links every district to one cluster. The cluster dimension contains neutral names, counts and a short machine-generated profile. Profiles provide both the mean raw value and standardized mean z-score for each of the 11 model features.

### `district_pca.csv`, `pca_loadings.csv` and `pca_explained_variance.csv`

PCA scores support a Power BI scatter plot, while loadings and cumulative explained variance make the dimensionality reduction auditable. Component signs are mathematically arbitrary and should not be interpreted as positive or negative ratings.

### `clustering_diagnostics.csv` and `clustering_model_metadata.json`

Diagnostics compare candidate cluster counts using silhouette, Calinski–Harabasz, Davies–Bouldin and minimum cluster size. Metadata records the chosen method, features, transforms, PCA coverage and robustness comparisons.

### `dim_party_group.csv`, `fact_district_election_results.csv` and `fact_district_election_turnout.csv`

District-level Regionalatlas election indicators for 2017, 2021 and 2025. The party grouping is deliberately separate from `dim_party.csv`: Regionalatlas combines CDU and CSU, while the detailed Federal Returning Officer files contain legally distinct party labels. Results are percentages, not vote counts. `value_status = not_available` preserves source exceptions such as the six Saarland district values for GRÜNE in 2021; these are null rather than zero.

### `cluster_election_results.csv`

Unweighted mean second-vote share by cluster × election × party group. It describes the average district and must not be used as a vote-weighted national aggregation.
