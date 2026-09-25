# Power BI implementation guide

The full page architecture, storytelling, visual design system, party colours, Volt scope and build sequence are defined in [`report_blueprint.md`](report_blueprint.md). Import [`germany_observatory_glossy.json`](germany_observatory_glossy.json) as the starting report theme and use [`core_dax_measures.md`](core_dax_measures.md) for the semantic-model measures.

## Before opening Power BI

1. Run `make transform-districts` and `make test`.
2. Review `clustering_diagnostics.csv`, `cluster_profiles.csv` and the methodology note.
3. Keep `data/raw` out of Power BI; import only `data/processed`.
4. Create the report as a Power BI Project (`.pbip`) in this directory so the semantic model and report definition remain reviewable in Git.

## Import and relationships

Create a text parameter named `DataRoot` pointing to the repository's `data/processed` directory. Use it in every CSV query instead of embedding separate absolute paths.

Build these one-to-many, single-direction relationships:

- `dim_state[state_code]` → `dim_district[state_code]`;
- `dim_district[district_id]` → district features, cluster assignment, election results, turnout and PCA scores;
- `dim_district_feature[feature_id]` → district features and cluster profiles;
- `dim_cluster[cluster_id]` → cluster assignment, profiles and cluster election results;
- `dim_election[election_id]` → district election results, turnout and cluster election results;
- `dim_party_group[party_group_id]` → district and cluster election results.

Do not connect `dim_party_group` to `dim_party`; the source classifications are different. Mark all key columns as text so leading zeros in AGS and state codes are preserved.

## Recommended pages

1. **Overview** — district count, selected cluster, population density, unemployment, income and a district map.
2. **Cluster map** — Germany by cluster with state, type and cluster slicers.
3. **Cluster profiles** — small multiples or a heatmap of `mean_z_score`; show raw units in tooltips.
4. **PCA explorer** — PC1 versus PC2 scatter, cluster colour, district tooltip and loadings explanation.
5. **Elections after clustering** — party-group vote-share trend and turnout by cluster; label the result as an unweighted district mean.
6. **District explorer** — one selected district compared with its cluster and Germany median.
7. **Methodology and quality** — sources, mixed reference years, excluded correlated features, chosen `k`, PCA variance and robustness scores.

## Core measures

Create explicit measures rather than relying on implicit sums. At minimum include district count, average feature value, cluster average, Germany average, difference from Germany, second-vote share, turnout, election-to-election change and selected-district rank. Use averages for rates and shares; never sum them.

Keep the state-level census nationality facts and AZR foreign-population series separate because their statistical concepts differ.
