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

The structural data reveal four distinct groups, formed **without using election results**. Their names describe relative demographic and economic profiles, not rankings:

| Cluster | Districts | Distinguishing characteristics |
|---|---:|---|
| Stable & affluent regions | 234 (58.5%) | Higher disposable income, lower unemployment and more children. |
| Ageing & shrinking periphery | 64 (16.0%) | Older populations, lower population growth and fewer children. |
| Urban pressure centres | 67 (16.8%) | High population density and unemployment, with lower disposable income. |
| Dynamic metropolitan hubs | 35 (8.8%) | Higher GDP per capita, workplace density and foreign-population share. |

These groups provide a useful lens for comparing electoral geography:

- **Different places, different party strengths.** In 2025, AfD had the highest mean share among the six comparable party groups in the ageing periphery (36.6%). CDU/CSU led in the other three clusters, reaching 33.8% in stable regions. GRÜNE’s strongest cluster was metropolitan hubs (17.6%); Die Linke’s was urban pressure centres (11.5%).
- **A broad shift between 2021 and 2025.** AfD gained vote share in all 400 districts, with its largest cluster gain in the ageing periphery. SPD and FDP lost share in every district. SPD’s mean district share fell from 25.7% to 15.7%.
- **Recovery was not a return to 2017.** CDU/CSU’s mean district share rose from 25.0% in 2021 to 29.4% in 2025, still below 34.3% in 2017. Die Linke also recovered from 2021 without regaining its 2017 mean.
- **Higher turnout, persistent gaps.** Mean district turnout rose from 75.8% in 2017 to 82.4% in 2025, but structural differences remained: 2025 cluster means ranged from 79.3% in urban pressure centres to 84.0% in stable regions.

Stable regions contain more than half of all districts, so a large district count alone does not demonstrate disproportionate party support. The dashboard combines counts, shares and structural comparisons to make these differences visible.

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
