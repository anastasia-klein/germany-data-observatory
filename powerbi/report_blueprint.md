# Power BI report blueprint

## Report promise

**Germany Data Observatory** explains how Germany's districts differ, where political parties are stronger, how those patterns changed, and which observed characteristics are associated with each party's territorial support.

The report must keep three evidence levels visibly separate:

1. **Election result** — what share of votes a party received in a territory.
2. **Territorial context** — what the district is like demographically and economically.
3. **Individual voter profile** — what surveyed people who chose a party report about themselves.

District aggregates support the first two levels. They do not identify the characteristics of individual voters. A future GLES survey layer is required for level three. Until it is added, use “districts where the party is stronger” rather than “people who vote for the party”.

## Audience and language

- Primary audience: non-technical readers and potential employers evaluating data engineering, analytics and BI skills.
- Report UI: English, with German official terms in tooltips where useful.
- Reading time: a two-minute overview plus optional deep dives.
- Default state: Bundestagswahl 2025, all Germany, no party selected.

## Story arc

### Act 1 — Germany is not one statistical profile

Introduce the 400 districts and the dimensions on which they differ: age, demographic change, migration, employment, income, GDP and urbanisation.

### Act 2 — Four structural Germanys emerge

Explain the four non-political clusters. Show that the model separates an ageing and shrinking periphery, stable and affluent regions, urban areas under socioeconomic pressure, and dynamic metropolitan hubs.

### Act 3 — Politics follows territory, but territory does not determine people

Add election results only after the structural clusters are fixed. Compare party support by cluster and show feature relationships as descriptive associations, not causal explanations.

### Act 4 — The pattern changes over time

Show 2017, 2021 and 2025 at district level and the longer 2005–2025 state series. Separate genuine temporal movement from differences in geographic grain.

### Act 5 — Smaller parties matter too

Use Volt as a focused case study. Show its state-level growth from 164,300 second votes in 2021 to 355,262 in 2025, while explaining why a district-cluster profile is not yet available.

## Navigation

Use a persistent top navigation bar:

`Overview | Indicators | Cluster Atlas | Party Landscape | Party Portrait | Change | Volt | District Explorer | Methodology`

Keep `Methodology` visually quieter but always available. Use a Home button and Back button on drill-through pages. Synchronise Election, Party, State and Cluster slicers only where their meaning is consistent.

## Canvas and layout system

- Canvas: 16:9, 1280 × 720.
- Content grid: 12 columns, 24 px outer margin, 16 px gutters.
- Header: 64 px.
- Footer/source line: 24 px.
- Primary visual area: 616 px high.
- Use at most one dominant visual, two supporting visuals and three small KPI cards per page.
- Keep visual titles as conclusions or questions, not chart-type labels.
- Use direct labels where possible and reserve tooltips for definitions, sources and exact values.

## Visual design system

### Design direction

Use an editorial “German data magazine” aesthetic rather than a conventional corporate dashboard:

- deep graphite page shell;
- warm ivory analytical surfaces;
- restrained gloss through soft highlights, subtle shadows and generous spacing;
- black-red-gold as navigation and structural accents;
- party colours only when party is the encoded category;
- cluster colours only on structural pages.

Do not place red, yellow and black series together merely as decoration. Readers must never confuse national branding with data encoding.

### Core palette

| Role | Colour |
|---|---|
| Graphite shell | `#111113` |
| Ivory surface | `#F4F1EA` |
| Primary text | `#171717` |
| Secondary text | `#66615A` |
| German red accent | `#DD0000` |
| German gold accent | `#FFCC00` |
| Divider | `#D8D2C8` |

Use a thin red-to-gold line in the header and a small black-red-gold mark beside the report title. Avoid flag backgrounds, large flag graphics and decorative eagles.

### Party palette

| Party group | Colour | Accessibility note |
|---|---|---|
| CDU/CSU | `#171717` | use on ivory; use light label on the mark |
| SPD | `#E3000F` | white label on filled marks |
| GRÜNE | `#1AA037` | white label on filled marks |
| FDP | `#FFED00` | always use dark label and dark outline |
| Die Linke | `#BE3075` | white label on filled marks |
| AfD | `#009EE0` | dark label when the mark is pale |
| Volt | `#502379` | white label on filled marks |
| Other parties | `#8C8C8C` | group only when the analytical question allows it |

Store party colour as data or return it from a DAX colour measure. Do not rely on legend order to assign colours.

### Cluster palette and names

Cluster colours are intentionally different in tone from the party palette and are used only on cluster-focused visuals.

| ID | Report name | Colour |
|---|---|---|
| `cluster_1` | Ageing & shrinking periphery | `#B56A42` |
| `cluster_2` | Stable & affluent regions | `#49796B` |
| `cluster_3` | Urban pressure centres | `#6E6B7E` |
| `cluster_4` | Dynamic metropolitan hubs | `#D3A62C` |

These are descriptive names, not rankings. Keep the neutral cluster ID in tooltips and methodology.

### Typography

- Font: Segoe UI for reliable Power BI Service rendering.
- Page title: 26–30 pt, semibold.
- Section title: 16–18 pt.
- KPI: 28–36 pt.
- Visual title: 13–15 pt.
- Body and axes: 10–12 pt; never smaller than 10 pt.
- Use sentence case. Avoid all-caps except tiny navigation labels.

## Page 1 — Overview: “Germany’s electoral landscape begins with place”

### Reader question

What is being analysed, and what is the main result?

### Layout

- Columns 1–8: district cluster map.
- Columns 9–12: three compact cluster-story cards and selected-context text.
- Bottom row: four-cluster comparison across age 65+, unemployment, disposable income and 2025 turnout.
- Header KPIs: 400 districts; 14 observed indicators; 11 model features; 4 clusters.

### Visuals

1. Azure Maps reference layer or Shape Map coloured by cluster.
2. Dot plot comparing the four clusters on four selected indicators.
3. Dynamic narrative title based on selected geography.

### Interaction

Selecting a district filters the cluster cards. Selecting a cluster highlights its districts without removing the national context. Default tooltip shows district, state, cluster and the four headline indicators.

### Takeaway

Germany contains four distinct structural district profiles before any election variable is considered.

## Page 2 — Indicators: “What makes districts different?”

### Reader question

Which variables are available, how are they distributed, and which ones enter the model?

### Layout

- Left two columns: feature-group selector and included/excluded toggle.
- Centre six columns: selected-feature distribution by cluster.
- Right four columns: definition, unit, reference year, source and transformation.
- Bottom full width: ranked district table for the selected feature.

### Visuals

1. Field-parameter-driven histogram or binned column chart.
2. Small-multiple box plots by cluster; use Deneb only if custom visuals are acceptable, otherwise use jittered dot plots.
3. Ranked bar chart of top and bottom districts.
4. Metadata card populated from `dim_district_feature`.

### Guardrails

Never sum rates, percentages, income or GDP per capita. Display the source year beside every selected indicator because the feature mart contains mixed latest years.

## Page 3 — Cluster Atlas: “Four structural Germanys”

### Reader question

Where are the clusters, and what distinguishes them?

### Layout

- Columns 1–7: large district map.
- Columns 8–12: selected-cluster identity panel.
- Bottom left: heatmap of cluster mean z-scores.
- Bottom right: composition by state and district type.

### Visuals

1. Cluster choropleth.
2. Heatmap: feature × cluster, using `mean_z_score` with a centred divergent scale.
3. 100% stacked bar: urban/rural/special district share.
4. Ranked bar: states contributing the largest number of districts.
5. Drill-through button to District Explorer.

### Mandatory annotations

- “Clusters use demographic and socioeconomic indicators only.”
- “Cluster names are descriptive, not value judgments.”
- Display `k = 4`, silhouette 0.301 and PCA coverage 82.4% in the methodology tooltip, not as headline KPIs.

## Page 4 — Party Landscape: “Where is each party stronger?”

### Reader question

How does the selected party’s territorial support vary across Germany and clusters?

### Layout

- Header: party button slicer, election-year slicer and geography-grain label.
- Columns 1–7: party vote-share map.
- Columns 8–12: vote-share distribution by cluster.
- Bottom: actual vote share against the strongest associated district characteristic.

### Visuals

1. Choropleth using the selected party colour as a sequential tint, not a rainbow scale.
2. Dot-and-whisker or box plot of district vote shares by cluster.
3. Scatter plot selected feature × party vote share, coloured by cluster.
4. Ranked top/bottom territories.

### Party-specific default feature

| Party | Default contextual relationship for 2025 |
|---|---|
| AfD | age 65+ share |
| CDU/CSU | unemployment rate or disposable income |
| GRÜNE | age 65+ share or population density |
| Die Linke | unemployment rate |
| FDP | disposable income |
| SPD | no single dominant feature; show a multi-feature message |

Label every relationship “district-level association”. Never use “AfD voters are older” or similar individual-level wording.

## Page 5 — Party Portrait: “Territory is not a person”

### Reader question

What can the data responsibly say about a party’s support base?

### Two-layer design

The upper half is available now:

- territorial profile of districts where the selected party is above its national median;
- comparison against all districts on age, density, unemployment, income, demographic change and foreign-population share;
- model performance and feature importance for predicting district vote share.

The lower half is reserved for GLES:

- age group;
- gender;
- education;
- employment status;
- subjective economic situation;
- urban/rural residence;
- political self-placement and issue priorities, where licensing and sample size permit.

### Visuals

1. Dumbbell chart: high-support districts versus all districts.
2. Feature-importance bar chart with out-of-state validation performance.
3. Actual versus expected district vote-share scatter with a 45-degree reference line.
4. Survey profile small multiples after GLES is integrated.

### Language contract

- Current layer: “territorial context of support”.
- GLES layer: “survey profile of respondents reporting a vote for …”.
- Never combine both into one synthetic “typical voter” avatar.
- Display unweighted base size for every survey-party profile, especially Volt.

## Page 6 — Change: “How did the political geography move?”

### Reader question

Which party–cluster relationships strengthened, weakened or remained stable?

### Layout

- Top: party selector and 2017/2021/2025 range.
- Left: vote-share trend by cluster.
- Right: start-to-end change in percentage points.
- Bottom left: turnout trend.
- Bottom right: map toggle between level and change.

### Visuals

1. Small-multiple line charts, one party per panel or one selected party across clusters.
2. Diverging bar for 2017→2025 change.
3. Turnout slope chart.
4. Change choropleth when comparable geography is available.

### Story anchors

- AfD increased most strongly in the ageing and shrinking cluster.
- GRÜNE remained strongest in dynamic metropolitan hubs.
- Turnout increased across all clusters in 2025.
- SPD’s territorial result is weakly explained by the current structural feature set; present this as a finding, not a model failure.

## Page 7 — Volt Spotlight: “Growth from a small base”

### Current evidence

Volt is present in the state-level Federal Returning Officer facts for 2021 and 2025:

- 2021: 164,300 second votes;
- 2025: 355,262 second votes;
- strongest 2025 state share in Hamburg: approximately 1.49%;
- next highest: Bremen approximately 1.10%, Berlin approximately 0.94%.

### Layout

- Hero: national vote count and change.
- Left: state choropleth for selected year.
- Right: state ranking with 2021 and 2025 dots.
- Bottom: “where Volt grew” slope chart and a transparent coverage note.

### Visuals

1. State-level map using Volt purple.
2. Dumbbell chart for 2021 versus 2025 state vote share.
3. Vote-count and vote-share KPIs.
4. Future constituency map after the Wahlkreis fact layer is added.

### Scope warning

Do not assign Volt a district-cluster profile from state averages. For comparable fine-grained analysis, add a separate `dim_constituency` and constituency election fact table from Federal Returning Officer open data. Constituencies and Kreise are different geographies and must not be joined by name.

## Page 8 — District Explorer: “One district in context”

### Reader question

How does one selected district compare with its cluster and Germany?

### Layout

- Header: searchable district slicer, state and cluster label.
- Left: selected district location map.
- Centre: six dumbbells — district, cluster average, Germany average.
- Right: percentile rank and nearest structural peers.
- Bottom: election result timeline and party mix.

### Visuals

1. Selected district map.
2. Dumbbell feature comparison.
3. PCA peer scatter using PC1 and PC2.
4. Election trend.
5. Table of five nearest districts in PCA space.

## Page 9 — Methodology: “What the report can and cannot claim”

### Sections

1. Source lineage: official source → raw immutable file → transformation → analytical fact → report.
2. Feature selection and excluded correlated indicators.
3. Standardisation, transformations, PCA and cluster selection.
4. Missing values and documented election exceptions.
5. Geographic-grain matrix.
6. Ecological fallacy and non-causal interpretation.
7. Refresh timestamp, source years and repository link.

### Visuals

1. Compact pipeline diagram.
2. Candidate-k diagnostic chart.
3. PCA explained-variance chart.
4. Data coverage matrix by geography and year.

## Geographic-grain matrix

| Analysis | Geography | Years | Parties |
|---|---|---|---|
| Structural features and clusters | Kreis / kreisfreie Stadt | latest available 2022–2025 | none |
| Cluster political profile | Kreis / kreisfreie Stadt | 2017, 2021, 2025 | CDU/CSU, SPD, FDP, GRÜNE, Die Linke, AfD |
| Long election history | Bundesland | 2005–2025 | all published parties |
| Volt current layer | Bundesland | 2021, 2025 | Volt |
| Future all-party detailed layer | Wahlkreis | 2021 comparable boundaries, 2025 | all published parties including Volt |
| Future individual profile | survey respondent | election-specific | subject to GLES sample and licence |

## Required additions before final publication

### Priority 0 — needed for the first PBIP

1. Add official district geometry and validate all 400 AGS matches.
2. Create a four-cluster semantic layer and business display names.
3. Add party colour and display-order dimensions.
4. Create a Date/Election dimension suitable for time-intelligence-like comparisons.
5. Implement the core DAX catalogue.

### Priority 1 — needed for the full political story

1. Add constituency-level 2025 results for every party, including Volt.
2. Add 2021 results converted to the 2025 constituency boundaries.
3. Keep constituency and district facts in separate stars connected only through shared Election and Party dimensions.
4. Build out-of-state validated party-context models and store predictions, residuals and feature importance as processed outputs.

### Priority 2 — needed for an actual voter profile

1. Obtain the GLES 2025 post-election cross-section under its access and reuse terms.
2. Keep licensed respondent-level raw data outside the public repository.
3. Publish only disclosure-safe aggregates if the licence permits it.
4. Suppress or clearly flag party profiles with small unweighted sample sizes; this is likely important for Volt.

## Build order inside Power BI Desktop

1. Save immediately as PBIP and enable the enhanced PBIR report format if available.
2. Import the supplied JSON theme.
3. Create a `DataRoot` text parameter and connect only to `data/processed`.
4. Set AGS, state code, party ID and election ID to Text before loading.
5. Build and validate the star-schema relationships.
6. Hide technical keys and raw helper columns from report view.
7. Create a dedicated Measures table and implement measures in display folders.
8. Build Methodology first to validate metadata and grain.
9. Build Overview and Cluster Atlas.
10. Build Party Landscape and Change.
11. Add Volt using the state star; do not force it into the district star.
12. Add drill-through and tooltip pages.
13. Test every page at default state, one selected party, one district, one state and blank selection.
14. Run Performance Analyzer, remove unused interactions and verify accessible reading order.

## Definition of done

- A non-technical reader can state the four structural district types after viewing Overview and Cluster Atlas.
- Every party chart indicates geography and year.
- Every “profile” statement says whether it describes territories or surveyed people.
- Volt appears with honest state-level coverage and no fabricated district profile.
- Party colours are stable across every page.
- The black-red-gold motif remains structural and never changes numerical meaning.
- All report sources and measures are traceable to repository files.
