# Germany Data Observatory 🇩🇪

A reproducible data-engineering and BI portfolio project built from official public data about Germany. The project is designed to demonstrate data acquisition, validation, transformation, dimensional modelling, analytics engineering and Power BI skills—not just the finished dashboard.

## Current milestone: district clustering layer

The data foundation now covers both Germany's 16 federal states and all 400 Kreise/kreisfreie Städte. A reproducible analytical pipeline prepares district features, runs PCA and Ward hierarchical clustering without political variables, and joins election results only after the clusters are fixed.

| Domain | Included data |
|---|---|
| Demographics | Population, nationality groups, 2018–2025 foreign-population trend, population density, age groups, natural change and net migration |
| Economy and society | GDP and disposable income per capita, employees subject to social insurance, SGB II recipients and unemployment |
| Elections | Eligible voters, turnout and second-vote party results by state for 2005, 2009, 2013, 2017, 2021 and 2025 |
| District typology | 14 official Regionalatlas indicators, 11 clustering features, PCA scores, cluster diagnostics and profiles for 400 districts |
| District elections | Turnout and six party-group second-vote shares for 2017, 2021 and 2025, joined after clustering |

The processing is deterministic and covered by data-quality, source-reconciliation and model-integrity tests. State transformations use the Python standard library; the district analysis uses pinned versions of pandas, NumPy, SciPy and scikit-learn.

## Architecture

```text
Official public data tables
        ↓
data/raw (immutable source copies + checksum manifest)
        ↓
Python transformations, validation and clustering
        ↓
data/processed (Power BI-ready star-schema tables)
        ↓
Power BI semantic model and report (next milestone)
```

## Analytical model

```text
dim_state ─────┬── state indicators
               ├── population by nationality
               ├── foreign-population trend
               ├── election turnout ───── dim_election
               └── party results ───────── dim_election
                         └───────────────── dim_party

dim_state ─── dim_district ──┬── district features ── dim_district_feature
                             ├── cluster assignment ── dim_cluster
                             ├── PCA scores
                             ├── election turnout ──── dim_election
                             └── party-group results ─ dim_party_group
```

`state_code`, `election_id` and `party_id` are the stable dimension keys used by the fact tables. `nuts1_code` supports future Eurostat joins and mapping. Election CSVs retain readable names and dates alongside the keys so they also remain understandable outside a BI model.

## Repository structure

```text
data/
├── raw/                    # unchanged source files and download manifest
└── processed/              # clean dimensional and fact tables
metadata/
├── data_dictionary.md
├── district_clustering_methodology.md
└── sources.md
powerbi/                    # PBIP implementation guide and future project
src/
├── download_data.py        # reproducible acquisition
├── download_district_data.py
├── download_genesis.py     # token-safe optional GENESIS API acquisition
├── transform_data.py       # deterministic state transformations
└── build_district_analysis.py
tests/
├── test_district_analysis.py
├── test_genesis.py         # credential-handling and API-client checks
└── test_pipeline.py        # state coverage and completeness checks
```

## Reproduce the data pipeline

Requirements: Python 3.9+ and an internet connection.

```bash
python -m pip install -r requirements.txt
make all
```

Or run the stages separately:

```bash
make download
make download-districts
make transform
make transform-districts
make test
```

The download step overwrites raw source copies intentionally and writes retrieval timestamps, sizes and SHA-256 hashes to `data/raw/manifest.json`. Review source changes before committing a refresh.

The current cluster solution selects `k = 3`: 64, 234 and 102 districts. Four principal components explain 82.4% of the standardized feature variance. See [`metadata/district_clustering_methodology.md`](metadata/district_clustering_methodology.md) for feature decisions, model selection, robustness checks and interpretation limits.

### Optional GENESIS API source

The public HTML sources above make the main pipeline reproducible without an account. A separate client is included for the richer GENESIS population cube `12411LJ001` (state × age × sex × reference date).

```bash
cp .env.example .env
# Add your personal token to .env, then:
make check-genesis
make download-genesis-metadata
make download-genesis
```

`.env` is ignored by Git. The token is sent only in the API request header and is never written to downloaded files, the manifest or logs. `make download-genesis` first refreshes the cube metadata and then requests the raw CSV; it does not change the eight processed tables yet.

As of 21 September 2026, authentication and metadata retrieval work, but Destatis returns status `8081` (“data access is currently unavailable”) for this cube’s values. The existing public Destatis datasets remain usable, and the command can be rerun when the service is available.

## Data quality checks

The tests currently verify that:

- the state dimension contains exactly 16 unique German states and NUTS 1 codes;
- election and party dimension keys are unique and every election fact has valid foreign keys;
- every selected structural indicator covers all 16 states and has a value;
- both election fact tables cover all 16 states;
- every election contains exactly the expected eligible-voter and voter records;
- state-level turnout and selected party totals reconcile to the official national controls for all six elections;
- every Destatis year and population group covers all 16 states;
- state totals reconcile to Destatis’s published Germany totals, allowing only documented source rounding.
- all district sources contain 400 unique AGS keys and every selected feature is complete;
- political variables are absent from the clustering feature catalogue;
- the selected cluster count obeys the minimum-size rule and maximizes eligible silhouette score;
- PCA reaches the 80% variance target and alternative scaling/model specifications remain substantially consistent;
- district election tables cover all 400 districts for 2017, 2021 and 2025.

The same checks run in GitHub Actions on every push and pull request. The workflow also confirms that committed processed data match the transformation code.

## Sources and licensing

The datasets come from the [Federal Returning Officer](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html) and [Destatis](https://www.destatis.de/EN/Home/_node.html). Source details, provenance, methodological boundaries and planned additions are documented in [`metadata/sources.md`](metadata/sources.md).

Source data are published under the Data Licence Germany – Attribution – Version 2.0. Repository code is licensed under the MIT License. The source-data license and attribution continue to apply to the raw and derived data.

## Roadmap

- [x] Select a coherent first data slice
- [x] Store raw source files separately
- [x] Build reproducible ingestion and transformation scripts
- [x] Create state, election and party dimensions and analytical fact tables
- [x] Add initial validation tests and metadata
- [x] Add a Destatis regional demographic time series
- [x] Add historical Bundestag results for 2005–2021
- [x] Build a 400-district feature mart from official Regionalatlas data
- [x] Add reproducible PCA, hierarchical clustering, diagnostics and robustness checks
- [x] Join district election indicators only after cluster assignment
- [ ] Build the Power BI semantic model and 15–20 meaningful DAX measures
- [ ] Create overview, cluster map, profiles, PCA explorer and election-comparison pages
- [ ] Publish the interactive public dashboard

## Scope

This MVP is descriptive. It does not make causal claims or predict election outcomes. Automatic scheduling is deliberately postponed until the manual refresh workflow and Power BI model are stable.
