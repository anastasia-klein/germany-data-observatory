# Power BI semantic model relationships

This model contains two analytical grains:

- district-level indicators, clusters and the 2017–2025 district election series;
- state-level demographic indicators and the 2005–2025 election series, including Volt.

Keep both grains in one semantic model, but never connect fact tables directly to one another.

## Before creating relationships

1. Finish all Power Query loads and select **Close & Apply**.
2. Open **Model view**.
3. Open **Manage relationships** and review any automatically detected relationships.
4. Remove auto-detected relationships that are not in the specification below. In particular, do not relate tables on `year`, `election_date`, party labels, state names, units or source fields.
5. Confirm that all `state_code`, `district_id`, `election_id`, `party_id`, `party_group_id`, `cluster_id` and `feature_id` columns are text.

All relationships below should be active.

## State and district geography

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_state[state_code]` | `dim_district[state_code]` | One to many | Single |
| `dim_state[state_code]` | `fact_election_party_results[state_code]` | One to many | Single |
| `dim_state[state_code]` | `fact_election_turnout[state_code]` | One to many | Single |
| `dim_state[state_code]` | `fact_state_indicators[state_code]` | One to many | Single |
| `dim_state[state_code]` | `fact_foreign_population[state_code]` | One to many | Single |
| `dim_state[state_code]` | `fact_population_nationality[state_code]` | One to many | Single |

The filter direction must run from `dim_state` to the other table.

## District indicators and cluster assignment

| One side | Related table | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_district[district_id]` | `fact_district_features[district_id]` | One to many | Single |
| `dim_district_feature[feature_id]` | `fact_district_features[feature_id]` | One to many | Single |
| `dim_district[district_id]` | `fact_cluster_assignment[district_id]` | One to one | **Both** |
| `dim_cluster[cluster_id]` | `fact_cluster_assignment[cluster_id]` | One to many | Single |

The one-to-one bidirectional district-assignment relationship is deliberate. It lets a `dim_cluster` slicer filter `fact_cluster_assignment`, then `dim_district`, then every district-level fact. Do not make other relationships bidirectional to imitate this behaviour.

## District elections

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_district[district_id]` | `fact_district_election_results[district_id]` | One to many | Single |
| `dim_election[election_id]` | `fact_district_election_results[election_id]` | One to many | Single |
| `dim_party_group[party_group_id]` | `fact_district_election_results[party_group_id]` | One to many | Single |
| `dim_district[district_id]` | `fact_district_election_turnout[district_id]` | One to many | Single |
| `dim_election[election_id]` | `fact_district_election_turnout[election_id]` | One to many | Single |

Use `dim_election[election_year]` in slicers and axes. Hide the repeated `election_year` columns in fact tables after validation.

## Cluster profiles and cluster election summaries

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_cluster[cluster_id]` | `cluster_profiles[cluster_id]` | One to many | Single |
| `dim_district_feature[feature_id]` | `cluster_profiles[feature_id]` | One to many | Single |
| `dim_cluster[cluster_id]` | `cluster_election_results[cluster_id]` | One to many | Single |
| `dim_election[election_id]` | `cluster_election_results[election_id]` | One to many | Single |
| `dim_party_group[party_group_id]` | `cluster_election_results[party_group_id]` | One to many | Single |

`cluster_election_results` contains unweighted means across districts. Keep its measures explicitly labelled as such.

## PCA model

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_district[district_id]` | `district_pca[district_id]` | One to many | Single |
| `dim_district_feature[feature_id]` | `pca_loadings[feature_id]` | One to many | Single |

Although the current analytical tables contain one row per key, explicitly choose one-to-many so the filter can remain single-direction and the dimension stays on the `1` side. Do not connect `pca_explained_variance` to `district_pca` by text component names: it is a disconnected methodology table.

## State election facts

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `dim_election[election_id]` | `fact_election_party_results[election_id]` | One to many | Single |
| `dim_party[party_id]` | `fact_election_party_results[party_id]` | One to many | Single |
| `dim_election[election_id]` | `fact_election_turnout[election_id]` | One to many | Single |

Together with the `dim_state` relationships above, these form the state-level election star.

Do not connect `dim_party` to `dim_party_group`. `dim_party` preserves the official long state-level party list, including Volt; `dim_party_group` contains the six harmonised district-level party groups available from Regionalatlas.

## Intentionally disconnected tables

- `pca_explained_variance`
- `clustering_diagnostics`

These small tables provide methodology KPIs and do not share a safe analytical key with the fact tables.

## Recommended model layouts

Create three model layouts so the semantic model remains readable:

1. **District model** — `dim_state`, `dim_district`, `dim_district_feature`, `dim_cluster`, `dim_election`, `dim_party_group` and all district/cluster/PCA facts.
2. **State trends** — `dim_state`, `dim_election`, `dim_party` and the five state-level facts.
3. **Methodology** — `dim_district_feature`, `dim_cluster`, `cluster_profiles`, `pca_loadings`, `pca_explained_variance` and `clustering_diagnostics`.

Place dimensions along the top and fact tables below them. Relationship lines should normally point down from the `1` side to the `*` side.

### Create a layout in Power BI Desktop

1. Open **Model view**.
2. At the bottom of the model canvas, find the **All tables** tab.
3. Select the **+** button beside it to create a separate diagram.
4. Rename the new tab. Depending on the Desktop version, double-click the tab name or right-click it and select **Rename**.
5. Drag the required tables from the **Data** pane onto the empty diagram.
6. Arrange dimensions along the top and facts beneath them. Existing relationships appear automatically; a layout never creates a second copy of a table or relationship.

Use these table sets:

**District model**

- `dim_state`
- `dim_district`
- `dim_district_feature`
- `dim_cluster`
- `dim_election`
- `dim_party_group`
- `fact_cluster_assignment`
- `fact_district_features`
- `fact_district_election_results`
- `fact_district_election_turnout`
- `cluster_profiles`
- `cluster_election_results`
- `district_pca`

**State trends**

- `dim_state`
- `dim_election`
- `dim_party`
- `fact_election_party_results`
- `fact_election_turnout`
- `fact_state_indicators`
- `fact_foreign_population`
- `fact_population_nationality`

**Methodology**

- `dim_district_feature`
- `dim_cluster`
- `fact_cluster_assignment`
- `cluster_profiles`
- `district_pca`
- `pca_loadings`
- `pca_explained_variance`
- `clustering_diagnostics`

The same table can appear in several layouts. Moving or removing a table card from a layout changes only that diagram. Editing a relationship, hiding a field or deleting a table changes the shared semantic model everywhere.

## Validation

Build a temporary table visual for each test and remove it afterwards:

1. `dim_cluster[cluster_name]` plus a district-count measure: the four rows must total 400 districts.
2. Select one cluster: a table using `dim_district[district_name]` must reduce to that cluster's districts.
3. `dim_state[state_name]` plus state election votes: all 16 states must appear.
4. `dim_election[election_year]` plus state vote share: years 2005, 2009, 2013, 2017, 2021 and 2025 must appear.
5. Filter `dim_party[party_name]` to Volt: only 2021 and 2025 should contain results.
6. A district election visual using `dim_party_group` must contain 2017, 2021 and 2025 only.

If Power BI reports an ambiguous relationship path, stop rather than making another relationship bidirectional. The intended model contains only the district-assignment `Both` relationship.
