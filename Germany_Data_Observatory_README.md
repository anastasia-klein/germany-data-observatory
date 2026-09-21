# Germany Data Observatory 🇩🇪

## Project goal

**Germany Data Observatory** is a personal data analytics project based
on open public data about Germany.

The project has two goals:

1.  explore demographic, social, economic and electoral data about
    Germany;
2.  learn and demonstrate practical skills in **Power BI, data modelling
    and DAX**.

The project is designed as a public portfolio project and should be
reproducible, understandable and easy to extend with additional data
sources.

## MVP scope

The first version focuses on:

-   **Demographics** --- population, age structure, migration-related
    indicators and regional differences;
-   **Employment and social conditions** --- employment, unemployment
    and selected socioeconomic indicators;
-   **Regional differences** --- comparison of the 16 German federal
    states;
-   **Federal elections** --- electoral participation and selected
    election results.

The **German music landscape is explicitly outside the MVP scope** and
may only be considered as a separate future extension.

## Initial data sources

The initial sources are planned to include:

-   **Destatis / GENESIS** --- German official statistics;
-   **Bundeswahlleiterin** --- official federal election data;
-   **Eurostat** --- selected indicators that provide useful European or
    international context.

Only publicly available data will be used.

The exact datasets and indicators will be selected after inspecting the
available source data.

## Data architecture

The project is intentionally structured so that new sources can be added
later without rebuilding the whole project.

``` text
Public data sources
    ├── Destatis / GENESIS
    ├── Bundeswahlleiterin
    └── Eurostat
             ↓
      Raw / source data
             ↓
      Data preparation
             ↓
 Standardized analytical data
             ↓
      Power BI data model
             ↓
    Interactive Power BI report
             ↓
       Publish to web
```

### Data preparation layer

The source data may require preliminary processing before they can be
used consistently.

Depending on the source, this layer may include:

-   converting file formats;
-   standardizing column names;
-   standardizing geographic identifiers;
-   standardizing indicator names;
-   harmonizing units;
-   handling missing values;
-   converting dates and periods;
-   source-specific transformations;
-   documenting definitions and limitations.

The MVP does **not** require an LLM for data standardization.
Transformations should be deterministic and reproducible.

The exact preprocessing approach will be chosen after inspecting the
real source datasets. Depending on the data, this may be done with
Python, Power Query or a combination of both.

## Updating data

Automatic updating is **out of scope for the MVP**.

The first version should support a simple manual workflow:

``` text
Retrieve source data
        ↓
Prepare / transform data
        ↓
Update processed dataset
        ↓
Refresh Power BI
        ↓
Publish updated report
```

The architecture should nevertheless make future automation possible.

Possible future improvements include:

-   automated downloads through APIs;
-   scheduled data updates;
-   GitHub Actions;
-   automated data validation;
-   automatic Power BI dataset refresh.

## Power BI learning goals

A major purpose of the project is to learn Power BI through a real
dataset rather than through isolated tutorials.

The project should provide practical experience with:

-   Power Query;
-   data cleaning and transformation;
-   dimensional modelling;
-   fact and dimension tables;
-   relationships;
-   filter context;
-   DAX measures;
-   calculated columns where appropriate;
-   time intelligence;
-   geographic analysis;
-   slicers and cross-filtering;
-   drill-down and drill-through;
-   tooltips;
-   report/page design.

The target is approximately **15--20 meaningful DAX measures**, rather
than a large number of artificial measures.

## Geographic visualization

A central visualisation will show the **16 German federal states
(Bundesländer)**.

The map should allow an indicator to be selected and use color intensity
to represent its value.

For example:

-   unemployment rate;
-   population density;
-   population growth;
-   median age;
-   electoral participation.

The exact indicator set will be determined after the source data have
been inspected.

## Planned Power BI report

### 1. Germany in Numbers

A national overview containing selected key indicators.

Possible elements:

-   population;
-   demographic structure;
-   employment/unemployment;
-   selected social indicators;
-   changes over time.

### 2. Regional Differences

Focus on differences between the 16 Bundesländer.

Possible elements:

-   interactive Germany map;
-   indicator selector;
-   comparison over time;
-   regional ranking or comparison views where appropriate;
-   detailed tooltip information.

### 3. Elections

A descriptive overview of federal election data.

Possible elements:

-   voter turnout;
-   election results by region;
-   changes between elections;
-   regional patterns.

The page should remain descriptive and should not attempt to predict
future election outcomes.

## Repository structure

A possible repository structure:

``` text
Germany-Data-Observatory/
│
├── README.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
│
├── src/
│   ├── ingestion/
│   └── transformation/
│
├── metadata/
│   ├── data_dictionary.md
│   └── sources.md
│
├── powerbi/
│   └── GermanyData.pbip
│
├── tests/
│
└── .gitignore
```

The exact structure can be adjusted after the first datasets have been
inspected.

## Public dashboard

The Power BI report can be published using **Power BI Publish to web**.

This is suitable for the project because the underlying data are public.

The published report should remain interactive, allowing users to:

-   use slicers;
-   filter regions;
-   change indicators;
-   interact with maps;
-   explore different report pages;
-   use tooltips and drill-downs.

Only public, non-sensitive data should be included in the published
model.

## Future extensions

The project is deliberately designed so that additional data sources and
presentation layers can be added later.

Possible extensions include:

-   additional Destatis datasets;
-   more detailed social indicators;
-   additional election datasets;
-   migration and integration indicators;
-   European comparisons;
-   additional geographic levels;
-   automated data updates;
-   automated data-quality checks;
-   an alternative web dashboard;
-   a data API or analytical data mart;
-   optional LLM-assisted data/entity matching.

These extensions are **not part of the MVP**.

## Project principles

The project follows several principles:

1.  **Use public and documented sources.**
2.  **Keep source data separate from transformed data.**
3.  **Make transformations reproducible.**
4.  **Prefer deterministic data preparation over opaque
    transformations.**
5.  **Keep the analytical model extensible.**
6.  **Document indicator definitions, sources and limitations.**
7.  **Separate descriptive analysis from causal claims.**
8.  **Keep the MVP small enough to finish.**
9.  **Start with a manual workflow and automate only after it works.**
10. **Use the project to learn Power BI and DAX through a real
    analytical problem.**

## Current status

The project is currently in the **planning and data exploration** phase.

The next steps are:

1.  select the first concrete datasets;
2.  inspect their structure and formats;
3.  identify common dimensions and geographic identifiers;
4.  determine the required preprocessing;
5.  define the standardized analytical tables;
6.  build the Power BI data model;
7.  create DAX measures;
8.  build the report;
9.  publish the interactive dashboard;
10. document the project and update workflow.
