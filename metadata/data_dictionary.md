# Analytical data dictionary

## `dim_state.csv`

One row per German federal state. `state_code` is the two-digit federal-state portion of the German official municipality key; `nuts1_code` supports later Eurostat joins and geographic mapping.

## `fact_state_indicators.csv`

Long-form table at state × indicator × year grain. `value` uses a dot decimal separator and `unit` is explicit, making it safe to import into Power Query. Population is currently expressed in thousands because that is the unit published in the source.

## `fact_election_party_results.csv`

One row per state × party for second votes in the final 2025 Bundestag election results. Previous-result fields are supplied by the source and refer to the comparable previous election result.

## `fact_election_turnout.csv`

Two rows per state: eligible voters and actual voters. `share_percent` is populated for voters and blank for eligible voters. A Power BI turnout measure can therefore use the published percentage or divide voters by eligible voters.

