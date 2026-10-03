# Core DAX measure catalogue

Adjust table names only if Power BI changes them during import. Put measures in a dedicated `_Measures` table and use display folders such as `Districts`, `Features`, `Elections`, `Clusters` and `UX`.

## Semantic-model preparation

Before creating measures:

1. Confirm that every relationship in `model_relationships.md` is active and that only the district-to-cluster-assignment relationship uses cross-filter direction **Both**.
2. Disable **Auto date/time** for the current file; `dim_election` is the model's election-time dimension.
3. Set key, year and order columns to **Don't summarize**. Also use **Don't summarize** for generic fact columns named `value`: they mix indicators or units and have no universally valid aggregation. This setting only changes drag-and-drop behaviour; explicit measures can still use `SUM`, `AVERAGE` or another appropriate calculation. Hide raw value columns after their explicit measures are available.
4. Configure **Sort by column**:
   - `dim_election[election_name]` by `dim_election[election_year]`;
   - `dim_party[party_name]` by `dim_party[party_display_order]`;
   - `dim_party_group[party_group_name]` by `dim_party_group[party_display_order]`;
   - `dim_cluster[cluster_name]` by `dim_cluster[cluster_id]`.
5. Create a calculated table using **Modeling → New table**:

```DAX
_Measures = DATATABLE ( "Placeholder", STRING, { { "" } } )
```

Hide `_Measures[Placeholder]`. Set every new measure's home table to `_Measures` and group measures into display folders.

## District and feature measures

```DAX
District Count =
DISTINCTCOUNT ( dim_district[district_id] )

Average Feature Value =
AVERAGE ( fact_district_features[value] )

Germany Feature Average =
VAR CurValue = [Average Feature Value]
VAR NationalAverage =
    CALCULATE (
        [Average Feature Value],
        REMOVEFILTERS ( dim_district ),
        REMOVEFILTERS ( dim_cluster ),
        REMOVEFILTERS ( fact_cluster_assignment )
    )
RETURN
    IF ( NOT ISBLANK ( CurValue ), NationalAverage )

Difference from Germany =
VAR CurValue = [Average Feature Value]
RETURN
    IF (
        NOT ISBLANK ( CurValue ),
        CurValue - [Germany Feature Average]
    )

Difference from Germany % =
VAR CurValue = [Average Feature Value]
RETURN
    IF (
        NOT ISBLANK ( CurValue ),
        DIVIDE ( [Difference from Germany], [Germany Feature Average] )
    )

Cluster Mean Z Score =
AVERAGE ( cluster_profiles[mean_z_score] )
```

## Overview measures

These measures support the fixed headline KPIs and the four-cluster comparison on the Overview page.

```DAX
Observed Indicator Count =
CALCULATE (
    DISTINCTCOUNT ( dim_district_feature[feature_id] ),
    REMOVEFILTERS ( dim_district_feature )
)

Model Feature Count =
CALCULATE (
    DISTINCTCOUNT ( dim_district_feature[feature_id] ),
    REMOVEFILTERS ( dim_district_feature ),
    dim_district_feature[included_in_clustering] = TRUE ()
)

Cluster Count =
CALCULATE (
    DISTINCTCOUNT ( dim_cluster[cluster_id] ),
    REMOVEFILTERS ( dim_cluster )
)

Population Aged 65+ % =
CALCULATE (
    [Average Feature Value],
    REMOVEFILTERS ( dim_district_feature ),
    dim_district_feature[feature_id] = "age_65_plus_share"
)

Unemployment Rate % =
CALCULATE (
    [Average Feature Value],
    REMOVEFILTERS ( dim_district_feature ),
    dim_district_feature[feature_id] = "unemployment_rate"
)

Disposable Income per Capita =
CALCULATE (
    [Average Feature Value],
    REMOVEFILTERS ( dim_district_feature ),
    dim_district_feature[feature_id] = "disposable_income_per_capita"
)

2025 Turnout % =
CALCULATE (
    [Mean District Turnout %],
    REMOVEFILTERS ( dim_election ),
    dim_election[election_year] = 2025
)
```

Format the count measures as whole numbers. `Population Aged 65+ %`, `Unemployment Rate %` and `2025 Turnout %` use the source's 0–100 scale, so format them as decimal numbers with one decimal place, not as Percentage. Format `Disposable Income per Capita` as EUR currency with a thousands separator and zero decimals.

## State-level election measures

These measures use vote counts from `fact_election_party_results` and therefore produce a properly weighted share over the selected states.

```DAX
Second Votes =
SUM ( fact_election_party_results[votes] )

Valid Second Votes =
CALCULATE (
    [Second Votes],
    REMOVEFILTERS ( dim_party ),
    REMOVEFILTERS ( fact_election_party_results[party_id] ),
    REMOVEFILTERS ( fact_election_party_results[party] ),
    REMOVEFILTERS ( fact_election_party_results[source_party] )
)

Second Vote Share =
DIVIDE ( [Second Votes], [Valid Second Votes] )

Previous Election Vote Share =
VAR CurYear = MAX ( dim_election[election_year] )
VAR PrevYear =
    MAXX (
        FILTER (
            ALL ( dim_election[election_year] ),
            dim_election[election_year] < CurYear
        ),
        dim_election[election_year]
    )
VAR PrevShare =
    CALCULATE (
        [Second Vote Share],
        REMOVEFILTERS ( dim_election ),
        dim_election[election_year] = PrevYear
    )
RETURN
    IF (
        HASONEVALUE ( dim_election[election_year] ),
        PrevShare
    )

Vote Share Change pp =
VAR PrevShare = [Previous Election Vote Share]
RETURN
    IF (
        NOT ISBLANK ( PrevShare ),
        100 * ( [Second Vote Share] - PrevShare )
    )

Eligible Voters =
CALCULATE (
    SUM ( fact_election_turnout[value] ),
    fact_election_turnout[measure] = "eligible_voters"
)

Voters =
CALCULATE (
    SUM ( fact_election_turnout[value] ),
    fact_election_turnout[measure] = "voters"
)

Turnout =
DIVIDE ( [Voters], [Eligible Voters] )
```

## District-level Regionalatlas election measures

The district source contains percentages rather than vote counts. These measures describe the average district and are not vote-weighted.

```DAX
Mean District Vote Share % =
AVERAGE ( fact_district_election_results[second_vote_share_percent] )

Mean District Turnout % =
AVERAGE ( fact_district_election_turnout[turnout_percent] )

Previous District Vote Share % =
VAR CurYear = MAX ( dim_election[election_year] )
VAR PrevYear =
    MAXX (
        FILTER (
            ALL ( dim_election[election_year] ),
            dim_election[election_year] < CurYear
                && dim_election[election_year] >= 2017
        ),
        dim_election[election_year]
    )
VAR PrevShare =
    CALCULATE (
        [Mean District Vote Share %],
        REMOVEFILTERS ( dim_election ),
        dim_election[election_year] = PrevYear
    )
RETURN
    IF (
        HASONEVALUE ( dim_election[election_year] ),
        PrevShare
    )

District Vote Share Change pp =
VAR PrevShare = [Previous District Vote Share %]
RETURN
    IF (
        NOT ISBLANK ( PrevShare ),
        [Mean District Vote Share %] - PrevShare
    )
```

## UX and colour measures

```DAX
Selected Party =
COALESCE (
    SELECTEDVALUE ( dim_party_group[party_group_name] ),
    SELECTEDVALUE ( dim_party[party_name] ),
    "All parties"
)

Party Colour =
SWITCH (
    [Selected Party],
    "CDU/CSU", "#171717",
    "CDU", "#171717",
    "CSU", "#008AC5",
    "SPD", "#E3000F",
    "GRÜNE", "#1AA037",
    "FDP", "#FFED00",
    "Die Linke", "#BE3075",
    "AfD", "#009EE0",
    "Volt", "#502379",
    "#8C8C8C"
)

Selected Geography Label =
VAR District = SELECTEDVALUE ( dim_district[district_name] )
VAR State = SELECTEDVALUE ( dim_state[state_name] )
RETURN
    COALESCE ( District, State, "Germany" )

Party Map Title =
[Selected Party] & " support in " & [Selected Geography Label]
```

## Mandatory formatting

- `Second Vote Share` and `Previous Election Vote Share`: percentage, one decimal place.
- `Turnout`: percentage, one decimal place. `Eligible Voters` and `Voters`: whole number with a thousands separator.
- `Vote Share Change pp`: keep the measure as a decimal number, choose model-level **Format → Custom**, and enter `+0.0;-0.0;0.0`. The three sections format positive, negative and zero values respectively. Do not choose Percentage: the measure already returns percentage points. Put `pp` or `percentage points` in the visual subtitle/axis title; alternatively use `+0.0" pp";-0.0" pp";0.0" pp"` when the unit must appear beside every value.
- District percentages: decimal number with one decimal place because the stored value already uses 0–100 scale.
- `Average Feature Value` serves indicators with different units, so do not give it a fixed euro or percentage format. When dedicated `Disposable Income per Capita` and `GDP per Capita` measures are added for KPI cards, format those measures as EUR currency with a thousands separator and zero decimals.
- Rates and shares: never use Sum as the implicit aggregation.
