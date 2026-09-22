# District clustering methodology

## Analytical question

Group Germany's 400 Kreise and kreisfreie Städte by demographic and socio-economic structure, then compare electoral profiles across the resulting groups. Election results are joined only after cluster assignment and cannot influence the clusters.

## Data preparation

The official Regionalatlas ArcGIS service supplies all district rows on 2024 boundaries (`typ = 3`). The feature catalogue records the source dataset, reference year, unit, transform and model inclusion flag. All 14 collected indicators have complete coverage for 400 districts.

Eleven features enter the model:

- population density, annual population change and migration balance;
- foreign-population share and the shares aged under 18 and 65+;
- workplace density and manufacturing-employment share;
- unemployment, disposable income per capita and GDP per capita.

Population density, workplace density and GDP per capita receive a `log1p` transform because their distributions are strongly right-skewed. All model features are standardized to mean zero and unit variance. Natural balance, services-employment share and minimum-security rate remain available for reporting but are excluded from clustering because each correlates above 0.90 in absolute value with a retained feature.

## PCA and clustering

Principal component analysis retains the minimum number of components needed to explain at least 80% of total standardized variance. The current run retains four components and explains 82.4%.

Ward hierarchical agglomerative clustering is evaluated for `k = 3…8`. The selected solution maximizes the silhouette score among candidates whose smallest cluster contains at least 20 districts. The current run selects three clusters with 64, 234 and 102 districts.

Cluster numbers are neutral identifiers, not rankings. They are ordered by the mean first principal-component score only to make reruns deterministic. `cluster_profiles.csv` contains both mean z-scores and mean values; these should be used to assign human-readable analytical names in the report.

## Robustness

The primary PCA solution is compared with clustering on the full standardized feature space and with RobustScaler plus PCA. Adjusted Rand Index values are written to `clustering_model_metadata.json`; both current comparisons are approximately 0.81. This indicates substantial, though not perfect, agreement and should be disclosed in the report rather than presenting the typology as a natural or unique truth.

## Electoral comparison

Regionalatlas supplies district-level second-vote shares for six party groups and turnout for 2017, 2021 and 2025. `cluster_election_results.csv` reports unweighted means across districts. These are suitable for comparing a typical district, not for reconstructing national vote totals; weighted aggregation would require district vote counts.

## Interpretation limits

The model is descriptive, sensitive to feature choice, transformations, dates and territorial definitions. Mixed reference years reflect the latest available official year per indicator. Clusters do not establish causal relationships and must not be used to infer individual voting behaviour from district averages.
