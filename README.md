# Germany Data Observatory 🇩🇪

[**Explore the interactive Power BI report →**](https://app.powerbi.com/view?r=eyJrIjoiNTI4ZDRmYTAtNjM3Yy00YTIzLTkwNTAtMGViNmRhMjBlNWU2IiwidCI6IjM5YTFiNjM3LTFmODktNGQzOS1iZjNlLWFiNzczZGRmOGJhZSJ9)

A pet project exploring how Germany’s regional structures relate to federal election results. It combines official public data, a reproducible Python pipeline and an interactive Power BI dashboard.

## Explore the report

Compare **400 districts**, their demographic and economic profiles, and voting patterns in **2017, 2021 and 2025**:

- **Overview & Indicators** — see regional patterns and compare district values.
- **Cluster Atlas** — explore four groups of structurally similar districts.
- **Party Landscape, Party Portrait & Change** — compare party support, territorial context and election-to-election changes.
- **District Explorer** — inspect a district, its election history and its five nearest structural peers.
- **Methodology** — read the sources, modelling choices, main findings and limitations.

## What stands out

From 2021 to 2025, AfD gained vote share in all 400 districts, while SPD and FDP lost share in every district. AfD’s largest cluster gain was in the ageing periphery. Mean district turnout rose from **75.8% in 2017 to 82.4% in 2025**, while structural turnout gaps persisted.

These are comparisons of places, not individual voters. Election summaries use **unweighted district means**, not national vote-weighted results.

## How it works

Official source snapshots → validated district tables → PCA and fixed structural clusters → Power BI.

The model collects **14 structural indicators** and uses **11** for clustering. Four principal components explain **82.4%** of standardized variance; Ward clustering produces four groups. **No electoral variables enter the clustering**—election results are joined afterwards.

Structural indicators have mixed reference years (2022–2025). The report describes associations, not causes or voter flows. See the [full methodology](metadata/district_clustering_methodology.md).

## Run locally

Requires Python 3.9+. Downloading source data also requires an internet connection.

```bash
python -m pip install -r requirements.txt
make all
```

To rebuild and test from the checked-in source snapshots:

```bash
make test
```

Open [GermanyDataObservatory.pbip](powerbi/GermanyDataObservatory.pbip) in Power BI Desktop on Windows.

Source snapshots and checksums live in `data/raw/`; report-ready tables in `data/processed/`; pipeline code in `src/`. GitHub Actions checks data coverage, official-total reconciliation, model integrity and report definitions.

## Sources & licences

Data come from [Regionalatlas](https://regionalatlas.statistikportal.de/), [Destatis](https://www.destatis.de/EN/Home/_node.html) and the [Federal Returning Officer](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html). District boundaries: © GeoBasis-DE / BKG (2026), dl-de/by-2-0.

Code is MIT-licensed. Source and derived data retain their source attribution and licence requirements. See the [source catalogue](metadata/sources.md) and [data dictionary](metadata/data_dictionary.md).
