# Core DAX measure catalogue

Adjust table names only if Power BI changes them during import. Put measures in a dedicated `_Measures` table and use display folders such as `Districts`, `Features`, `Elections`, `Clusters` and `UX`.

## District and feature measures

```DAX
District Count =
DISTINCTCOUNT ( dim_district[district_id] )

Average Feature Value =
AVERAGE ( fact_district_features[value] )

Germany Feature Average =
CALCULATE (
    [Average Feature Value],
    REMOVEFILTERS ( dim_district ),
    REMOVEFILTERS ( dim_cluster )
)

Difference from Germany =
[Average Feature Value] - [Germany Feature Average]

Difference from Germany % =
DIVIDE ( [Difference from Germany], [Germany Feature Average] )

Cluster Mean Z Score =
AVERAGE ( cluster_profiles[mean_z_score] )
```

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
VAR CurrentYear = MAX ( dim_election[election_year] )
VAR PreviousYear =
    MAXX (
        FILTER (
            ALL ( dim_election[election_year] ),
            dim_election[election_year] < CurrentYear
        ),
        dim_election[election_year]
    )
RETURN
    CALCULATE (
        [Second Vote Share],
        REMOVEFILTERS ( dim_election ),
        dim_election[election_year] = PreviousYear
    )

Vote Share Change pp =
100 * ( [Second Vote Share] - [Previous Election Vote Share] )
```

## District-level Regionalatlas election measures

The district source contains percentages rather than vote counts. These measures describe the average district and are not vote-weighted.

```DAX
Mean District Vote Share % =
AVERAGE ( fact_district_election_results[second_vote_share_percent] )

Mean District Turnout % =
AVERAGE ( fact_district_election_turnout[turnout_percent] )

Previous District Vote Share % =
VAR CurrentYear = MAX ( dim_election[election_year] )
VAR PreviousYear =
    MAXX (
        FILTER (
            ALL ( dim_election[election_year] ),
            dim_election[election_year] < CurrentYear
                && dim_election[election_year] >= 2017
        ),
        dim_election[election_year]
    )
RETURN
    CALCULATE (
        [Mean District Vote Share %],
        REMOVEFILTERS ( dim_election ),
        dim_election[election_year] = PreviousYear
    )

District Vote Share Change pp =
[Mean District Vote Share %] - [Previous District Vote Share %]
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

- `Second Vote Share`: percentage, one decimal place.
- `Vote Share Change pp`: `+0.0;-0.0;0.0` with “pp” in the visual subtitle.
- District percentages: decimal number with one decimal place because the stored value already uses 0–100 scale.
- Income and GDP: euro with thousands separator and zero decimals.
- Rates and shares: never use Sum as the implicit aggregation.
