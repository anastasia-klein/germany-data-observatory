# Data sources

## Included in the first collection

| Dataset | Publisher | Coverage used | Raw file | License |
|---|---|---|---|---|
| Final results of the 2025 Bundestag election (`kerg2`) | Federal Returning Officer (Bundeswahlleiterin) | 16 states; second-vote party results and turnout | `data/raw/bundeswahlleiterin/btw25_kerg2.csv` | Data Licence Germany – Attribution – Version 2.0 |
| Structural data for the 2025 Bundestag election | Federal Returning Officer; underlying data mainly from the German regional statistics database and the Federal Employment Agency | 16 states; demographic, economic and labour-market indicators | `data/raw/bundeswahlleiterin/btw2025_strukturdaten.csv` | Data Licence Germany – Attribution – Version 2.0 |
| Population by nationality and state, 31 December 2025 | Federal Statistical Office (Destatis), population projection based on the 2022 census | 16 states; total, German, non-German and EU-country population | `data/raw/destatis/population_by_nationality_2025.html` | Data Licence Germany – Attribution – Version 2.0 |
| Foreign population by state, 2018–2025 | Federal Statistical Office (Destatis), Central Register of Foreigners (AZR) | 16 states; annual foreign-population count | `data/raw/destatis/foreign_population_by_state_2018_2025.html` | Data Licence Germany – Attribution – Version 2.0 |
| GENESIS cube metadata `12411LJ001` | Federal Statistical Office (Destatis), GENESIS-Online API | Population stock by state, age, sex and reference date; metadata only | `data/raw/destatis/genesis_12411LJ001_metadata.json` | Data Licence Germany – Attribution – Version 2.0 |

Official landing pages:

- [2025 election results](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html)
- [Open-data description](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/opendata.html)
- [2025 structural data](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/strukturdaten.html)
- [Population by nationality and state](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Bevoelkerungsstand/Tabellen/bevoelkerung-nichtdeutsch-laender-basis-2022.html)
- [Foreign population by state and year](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Migration-Integration/Tabellen/auslaendische-bevoelkerung-bundeslaender-jahre.html)
- [GENESIS-Online](https://genesis.destatis.de/datenbank/online/)
- [GENESIS web-service documentation](https://genesis.destatis.de/datenbank/online/docs/GENESIS-Webservices_Introduction.pdf)

The files are stored unchanged in `data/raw`. The download scripts record the source URL, retrieval timestamp, byte count and SHA-256 checksum in `data/raw/manifest.json` on each refresh. Destatis tables are retained as source HTML because these public pages do not require an account and can therefore be reproduced without storing an API credential. The optional GENESIS client reads its token from a git-ignored environment file and never persists it.

## GENESIS API status

The API client targets cube `12411LJ001`, the underlying population-stock dataset with the dimensions `DLAND` (state), `ALT103` (age), `GES` (sex) and `STAG` (reference date). On 21 September 2026, token authentication and `metadata/cube` succeeded, while `data/cubefile` returned GENESIS status `8081`: access to the data was temporarily unavailable. This is kept separate from the production transformation until a raw values file can be retrieved and validated. The public HTML sources above continue to supply the current analysis-ready demographic tables.

## Methodological boundary

The two Destatis population sources describe different statistical concepts:

- the 2025 nationality table is based on the population projection from the 2022 census;
- the 2018–2025 time series comes from the Central Register of Foreigners (AZR).

The number of non-German residents from the census-based population statistics is therefore not expected to equal the number of foreign residents in the AZR. The processed tables remain separate so Power BI does not silently combine these measures.

## Next collection candidates

1. Retry Destatis GENESIS cube `12411LJ001`, validate its age/sex totals and add a state-year population fact table after the values endpoint is available.
2. Eurostat regional datasets for European context after the Germany-first model is stable.
3. Historical Bundestag results to support election-over-election analysis beyond the previous-period fields in the 2025 file.

These are intentionally not mixed into the first collection before their classifications and revisions have been assessed.
