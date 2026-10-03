# Power Query setup for `data/processed`

This setup keeps every CSV query dependent on one Power BI parameter. When the repository moves, only `DataRoot` needs to change.

## 1. Create the `DataRoot` parameter

In Power BI Desktop open **Home → Transform data → Manage parameters → New parameter** and enter:

| Setting | Value |
|---|---|
| Name | `DataRoot` |
| Type | Text |
| Suggested values | Any value |
| Required | Yes |
| Current value | the absolute Windows path to `germany-data-observatory\data\processed` |

Example:

```text
C:\Users\Anastasia\Documents\GitHub\germany-data-observatory\data\processed
```

Do not add a file name. A final backslash is optional.

## 2. Create the shared CSV loader

In Power Query choose **Home → New source → Blank query**, rename it to `fnLoadProcessedCsv`, open **Advanced Editor**, and replace its contents with:

```powerquery
(FileName as text, ColumnTypes as list) as table =>
let
    Files = Folder.Contents(DataRoot),
    MatchingFiles = Table.SelectRows(Files, each [Name] = FileName),
    Content =
        if Table.RowCount(MatchingFiles) = 1 then
            MatchingFiles{0}[Content]
        else
            error Error.Record(
                "Processed file not found",
                "Expected exactly one file named " & FileName,
                [DataRoot = DataRoot, Matches = Table.RowCount(MatchingFiles)]
            ),
    Csv = Csv.Document(
        Content,
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, ColumnTypes, "en-US")
in
    Typed
```

Disable load for the function: right-click `fnLoadProcessedCsv` and clear **Enable load**.

## 3. Create dimension queries

For every query below, create a blank query, give it the heading shown, and paste the expression into **Advanced Editor**.

### `dim_state`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_state.csv", {
        {"state_code", type text},
        {"state_name", type text},
        {"nuts1_code", type text}
    })
in
    Source
```

### `dim_district`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_district.csv", {
        {"district_id", type text},
        {"district_name", type text},
        {"district_name_official", type text},
        {"district_type", type text},
        {"state_code", type text},
        {"state_name", type text},
        {"geography_year", Int64.Type}
    })
in
    Source
```

### `dim_district_feature`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_district_feature.csv", {
        {"feature_id", type text},
        {"feature_name", type text},
        {"unit", type text},
        {"reference_year", Int64.Type},
        {"source_dataset", type text},
        {"included_in_clustering", type logical},
        {"transform", type text},
        {"exclusion_reason", type text}
    })
in
    Source
```

### `dim_cluster`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_cluster.csv", {
        {"cluster_id", type text},
        {"cluster_name", type text},
        {"cluster_short_name", type text},
        {"cluster_color_hex", type text},
        {"district_count", Int64.Type},
        {"profile_summary", type text}
    })
in
    Source
```

### `dim_election`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_election.csv", {
        {"election_id", type text},
        {"election_date", type date},
        {"election_year", Int64.Type},
        {"bundestag_number", Int64.Type},
        {"election_name", type text},
        {"result_status", type text},
        {"result_version", type text},
        {"source_file", type text}
    })
in
    Source
```

### `dim_party_group`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_party_group.csv", {
        {"party_group_id", type text},
        {"party_group_name", type text},
        {"party_color_hex", type text},
        {"party_display_order", Int64.Type}
    })
in
    Source
```

### `dim_party`

```powerquery
let
    Source = fnLoadProcessedCsv("dim_party.csv", {
        {"party_id", type text},
        {"party_name", type text},
        {"first_election_year", Int64.Type},
        {"last_election_year", Int64.Type},
        {"election_count", Int64.Type},
        {"party_color_hex", type text},
        {"party_display_order", Int64.Type},
        {"is_report_focus", type logical}
    })
in
    Source
```

## 4. Create district-level fact queries

### `fact_district_features`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_district_features.csv", {
        {"district_id", type text},
        {"feature_id", type text},
        {"value", type number},
        {"reference_year", Int64.Type},
        {"unit", type text},
        {"source_dataset", type text}
    })
in
    Source
```

### `fact_cluster_assignment`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_cluster_assignment.csv", {
        {"district_id", type text},
        {"cluster_id", type text}
    })
in
    Source
```

### `fact_district_election_results`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_district_election_results.csv", {
        {"district_id", type text},
        {"election_id", type text},
        {"election_year", Int64.Type},
        {"party_group_id", type text},
        {"second_vote_share_percent", type number},
        {"value_status", type text},
        {"source_dataset", type text}
    })
in
    Source
```

### `fact_district_election_turnout`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_district_election_turnout.csv", {
        {"district_id", type text},
        {"election_id", type text},
        {"election_year", Int64.Type},
        {"turnout_percent", type number},
        {"source_dataset", type text}
    })
in
    Source
```

## 5. Create cluster and PCA queries

### `cluster_profiles`

```powerquery
let
    Source = fnLoadProcessedCsv("cluster_profiles.csv", {
        {"cluster_id", type text},
        {"feature_id", type text},
        {"mean_z_score", type number},
        {"mean_raw_value", type number}
    })
in
    Source
```

### `cluster_election_results`

```powerquery
let
    Source = fnLoadProcessedCsv("cluster_election_results.csv", {
        {"cluster_id", type text},
        {"election_id", type text},
        {"election_year", Int64.Type},
        {"party_group_id", type text},
        {"unweighted_mean_second_vote_share_percent", type number}
    })
in
    Source
```

### `district_pca`

```powerquery
let
    Source = fnLoadProcessedCsv("district_pca.csv", {
        {"district_id", type text},
        {"pc1", type number},
        {"pc2", type number},
        {"pc3", type number},
        {"pc4", type number}
    })
in
    Source
```

### `pca_loadings`

```powerquery
let
    Source = fnLoadProcessedCsv("pca_loadings.csv", {
        {"feature_id", type text},
        {"pc1", type number},
        {"pc2", type number},
        {"pc3", type number},
        {"pc4", type number}
    })
in
    Source
```

### `pca_explained_variance`

```powerquery
let
    Source = fnLoadProcessedCsv("pca_explained_variance.csv", {
        {"component", type text},
        {"explained_variance_ratio", type number},
        {"cumulative_explained_variance_ratio", type number}
    })
in
    Source
```

### `clustering_diagnostics`

```powerquery
let
    Source = fnLoadProcessedCsv("clustering_diagnostics.csv", {
        {"k", Int64.Type},
        {"silhouette_score", type number},
        {"calinski_harabasz_score", type number},
        {"davies_bouldin_score", type number},
        {"minimum_cluster_size", Int64.Type},
        {"passes_minimum_size", type logical},
        {"selected", type logical}
    })
in
    Source
```

## 6. Create state-level fact queries

### `fact_election_party_results`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_election_party_results.csv", {
        {"election_id", type text},
        {"election_date", type date},
        {"state_code", type text},
        {"party_id", type text},
        {"party", type text},
        {"source_party", type text},
        {"votes", Int64.Type},
        {"vote_share_percent", type number},
        {"previous_votes", Int64.Type},
        {"previous_vote_share_percent", type number},
        {"change_percentage_points", type number}
    })
in
    Source
```

### `fact_election_turnout`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_election_turnout.csv", {
        {"election_id", type text},
        {"election_date", type date},
        {"state_code", type text},
        {"measure", type text},
        {"value", Int64.Type},
        {"share_percent", type number}
    })
in
    Source
```

### `fact_state_indicators`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_state_indicators.csv", {
        {"state_code", type text},
        {"year", Int64.Type},
        {"indicator", type text},
        {"value", type number},
        {"unit", type text},
        {"source", type text}
    })
in
    Source
```

### `fact_foreign_population`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_foreign_population.csv", {
        {"year", Int64.Type},
        {"state_code", type text},
        {"foreign_population_count", Int64.Type},
        {"source_register", type text}
    })
in
    Source
```

### `fact_population_nationality`

```powerquery
let
    Source = fnLoadProcessedCsv("fact_population_nationality.csv", {
        {"reference_date", type date},
        {"state_code", type text},
        {"population_group", type text},
        {"population_count", Int64.Type},
        {"share_percent", type number},
        {"share_of", type text}
    })
in
    Source
```

## 7. Validation before loading

The expected row counts are:

| Query | Rows |
|---|---:|
| `dim_state` | 16 |
| `dim_district` | 400 |
| `dim_district_feature` | 14 |
| `dim_cluster` | 4 |
| `dim_election` | 6 |
| `dim_party_group` | 6 |
| `dim_party` | 81 |
| `fact_district_features` | 5,600 |
| `fact_cluster_assignment` | 400 |
| `fact_district_election_results` | 7,200 |
| `fact_district_election_turnout` | 1,200 |
| `cluster_profiles` | 44 |
| `cluster_election_results` | 72 |
| `district_pca` | 400 |
| `pca_loadings` | 11 |
| `pca_explained_variance` | 4 |
| `clustering_diagnostics` | 6 |
| `fact_election_party_results` | 1,449 |
| `fact_election_turnout` | 192 |
| `fact_state_indicators` | 224 |
| `fact_foreign_population` | 128 |
| `fact_population_nationality` | 64 |

Verify especially that `state_code` and `district_id` show the **ABC** text-type icon and retain leading zeros such as `01` and `01001`.

Finally select **Home → Close & Apply**. Do not create relationships in Power Query; create and validate them in Model view after all tables load.
