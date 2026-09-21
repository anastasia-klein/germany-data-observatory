# Data sources

## Included in the first collection

| Dataset | Publisher | Coverage used | Raw file | License |
|---|---|---|---|---|
| Final results of the 2025 Bundestag election (`kerg2`) | Federal Returning Officer (Bundeswahlleiterin) | 16 states; second-vote party results and turnout | `data/raw/bundeswahlleiterin/btw25_kerg2.csv` | Data Licence Germany – Attribution – Version 2.0 |
| Structural data for the 2025 Bundestag election | Federal Returning Officer; underlying data mainly from the German regional statistics database and the Federal Employment Agency | 16 states; demographic, economic and labour-market indicators | `data/raw/bundeswahlleiterin/btw2025_strukturdaten.csv` | Data Licence Germany – Attribution – Version 2.0 |

Official landing pages:

- [2025 election results](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html)
- [Open-data description](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/opendata.html)
- [2025 structural data](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/strukturdaten.html)

The files are stored unchanged in `data/raw`. The download script records the source URL, retrieval timestamp, byte count and SHA-256 checksum in `data/raw/manifest.json` on each refresh.

## Next collection candidates

1. Destatis GENESIS table `12411-0011` for population by state, sex and reference date. This adds a proper demographic time series.
2. Eurostat regional datasets for European context after the Germany-first model is stable.
3. Historical Bundestag results to support election-over-election analysis beyond the previous-period fields in the 2025 file.

These are intentionally not mixed into the first collection before their classifications and revisions have been assessed.

