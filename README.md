# Germany Data Observatory 🇩🇪

A reproducible data-engineering and BI portfolio project built from official public data about Germany. The project is designed to demonstrate data acquisition, validation, transformation, dimensional modelling, analytics engineering and Power BI skills—not just the finished dashboard.

## Current milestone: data foundation

The first end-to-end data slice is complete. It combines final Bundestag election results from 2005 through 2025 with structural indicators for all 16 German federal states.

| Domain | Included data |
|---|---|
| Demographics | Population, nationality groups, 2018–2025 foreign-population trend, population density, age groups, natural change and net migration |
| Economy and society | GDP and disposable income per capita, employees subject to social insurance, SGB II recipients and unemployment |
| Elections | Eligible voters, turnout and second-vote party results by state for 2005, 2009, 2013, 2017, 2021 and 2025 |

The repository currently contains nine unchanged official source-data files, one GENESIS metadata snapshot and six analysis-ready CSV tables. The processing is deterministic, uses only the Python standard library, and is covered by data-quality and source-reconciliation tests.

## Architecture

```text
Official public data tables
        ↓
data/raw (immutable source copies + checksum manifest)
        ↓
Python transformations and validation
        ↓
data/processed (Power BI-ready star-schema tables)
        ↓
Power BI semantic model and report (next milestone)
```

## Analytical model

```text
                           ┌──────────────────────────────┐
                           │ dim_state                    │
                           │ state_code (PK)              │
                           │ state_name                   │
                           │ nuts1_code                   │
                           └──────────────┬───────────────┘
                                          │ 1
             ┌───────────┬────────────┼────────────┬────────────┐
             │ *         │ *          │ *          │ *          │ *
     state indicators  nationality  foreign-pop.  turnout   party results
                                      trend
```

`state_code` is the stable two-digit federal-state key. `nuts1_code` is included for future Eurostat joins and mapping.

## Repository structure

```text
data/
├── raw/                    # unchanged source files and download manifest
└── processed/              # clean dimensional and fact tables
metadata/
├── data_dictionary.md
└── sources.md
powerbi/                    # future Power BI project
src/
├── download_data.py        # reproducible acquisition
├── download_genesis.py     # token-safe optional GENESIS API acquisition
└── transform_data.py       # deterministic transformations
tests/
├── test_genesis.py         # credential-handling and API-client checks
└── test_pipeline.py        # state coverage and completeness checks
```

## Reproduce the data pipeline

Requirements: Python 3.9+ and an internet connection. No third-party Python packages are required.

```bash
make all
```

Or run the stages separately:

```bash
make download
make transform
make test
```

The download step overwrites raw source copies intentionally and writes retrieval timestamps, sizes and SHA-256 hashes to `data/raw/manifest.json`. Review source changes before committing a refresh.

### Optional GENESIS API source

The public HTML sources above make the main pipeline reproducible without an account. A separate client is included for the richer GENESIS population cube `12411LJ001` (state × age × sex × reference date).

```bash
cp .env.example .env
# Add your personal token to .env, then:
make check-genesis
make download-genesis-metadata
make download-genesis
```

`.env` is ignored by Git. The token is sent only in the API request header and is never written to downloaded files, the manifest or logs. `make download-genesis` first refreshes the cube metadata and then requests the raw CSV; it does not change the six processed tables yet.

As of 21 September 2026, authentication and metadata retrieval work, but Destatis returns status `8081` (“data access is currently unavailable”) for this cube’s values. The existing public Destatis datasets remain usable, and the command can be rerun when the service is available.

## Data quality checks

The tests currently verify that:

- the state dimension contains exactly 16 unique German states and NUTS 1 codes;
- every selected structural indicator covers all 16 states and has a value;
- both election fact tables cover all 16 states;
- every election contains exactly the expected eligible-voter and voter records;
- state-level turnout and selected party totals reconcile to the official national controls for all six elections;
- every Destatis year and population group covers all 16 states;
- state totals reconcile to Destatis’s published Germany totals, allowing only documented source rounding.

The same checks run in GitHub Actions on every push and pull request. The workflow also confirms that committed processed data match the transformation code.

## Sources and licensing

The datasets come from the [Federal Returning Officer](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html) and [Destatis](https://www.destatis.de/EN/Home/_node.html). Source details, provenance, methodological boundaries and planned additions are documented in [`metadata/sources.md`](metadata/sources.md).

Source data are published under the Data Licence Germany – Attribution – Version 2.0. Repository code is licensed under the MIT License. The source-data license and attribution continue to apply to the raw and derived data.

## Roadmap

- [x] Select a coherent first data slice
- [x] Store raw source files separately
- [x] Build reproducible ingestion and transformation scripts
- [x] Create state dimension and analytical fact tables
- [x] Add initial validation tests and metadata
- [x] Add a Destatis regional demographic time series
- [x] Add historical Bundestag results for 2005–2021
- [ ] Build the Power BI semantic model and 15–20 meaningful DAX measures
- [ ] Create Germany in Numbers, Regional Differences and Elections report pages
- [ ] Publish the interactive public dashboard

## Scope

This MVP is descriptive. It does not make causal claims or predict election outcomes. Automatic scheduling is deliberately postponed until the manual refresh workflow and Power BI model are stable.
