# Power BI next steps: model cleanup and Overview page

Follow this sequence after the `_Model QA` page passes.

## 1. Preserve the QA page

- Rename it `_Model QA` if needed.
- Right-click the page tab and select **Hide page**.
- Do not delete it; it is a regression-check page for later data refreshes.

## 2. Clean the field list

Hide technical columns from report view without deleting them. At minimum hide:

- primary and foreign key columns in fact tables;
- repeated `election_year` and `election_date` columns in fact tables;
- `party`, `source_party`, `source_dataset`, `source_file` and other lineage columns from the normal report field list;
- sort columns such as `party_display_order`;
- the `_Measures[Placeholder]` column.

Keep the descriptive dimension attributes visible. Use `dim_state[state_name]`, `dim_election[election_year]`, `dim_party[party_name]`, `dim_party_group[party_group_name]`, `dim_cluster[cluster_name]` and `dim_district_feature[feature_name]` in report visuals rather than their fact-table duplicates.

Do not hide raw PCA fields or state-indicator fields until their report pages and dedicated measures are complete.

## 3. Add Overview measures

Create the measures from the **Overview measures** section in `core_dax_measures.md` and place them in these display folders:

- `Overview\Counts`: `Observed Indicator Count`, `Model Feature Count`, `Cluster Count`;
- `Overview\Indicators`: `Population Aged 65+ %`, `Unemployment Rate %`, `Disposable Income per Capita`, `2025 Turnout %`.

`District Count` can remain in `Districts` and be reused on the Overview page.

## 4. Import the report theme

In Power BI Desktop select **View → Themes → Browse for themes** and open `powerbi/germany_observatory_glossy.json`.

Confirm that the theme name is **Germany Data Observatory - Editorial Gloss**. The theme defines the palette; page composition, surfaces and navigation still need to be built manually.

## 5. Create the report pages

Create and order these blank pages:

1. `Overview`
2. `Indicators`
3. `Cluster Atlas`
4. `Party Landscape`
5. `Party Portrait`
6. `Change`
7. `Volt`
8. `District Explorer`
9. `Methodology`

Keep `_Model QA` last and hidden.

For every public page use **Canvas settings → Page size → 16:9**. Use a 1280 × 720 design reference.

## 6. Build the reusable page shell

On `Overview`:

- set the canvas background to graphite `#111113` with 0% transparency;
- reserve the top 64 px for the header;
- use warm ivory `#F4F1EA` rounded rectangles as visual containers;
- leave 24 px outer margins and approximately 16 px gaps;
- add a thin red `#DD0000` to gold `#FFCC00` accent line below the header;
- use Segoe UI and sentence case.

### Exact Power BI controls

Click an empty part of the page so no visual is selected, then open **Format page**:

- **Canvas settings → Type**: `16:9`;
- **Canvas settings → Size**: `1280 × 720 (HD)`;
- **Canvas background → Color**: `#111113`;
- **Canvas background → Transparency**: `0%`;
- **Wallpaper → Color**: `#111113` and **Transparency**: `0%` so the area outside the canvas does not flash white in editing or presentation views.

Enable **View → Gridlines**, **Snap objects to grid** and **Selection pane**. Exact position and size for any selected object are under **Format visual/shape → General → Properties**. `Horizontal`/`X` and `Vertical`/`Y` are pixel distances from the top-left canvas corner.

Use this coordinate system:

- header area: `X 0`, `Y 0`, `W 1280`, `H 64`;
- accent line: `Y 62`, `H 2`;
- content begins at `X 24`, `Y 80`;
- right content edge: `X 1256`;
- outer margin: 24 px;
- gap between neighboring containers: 16 px.

For a 12-column grid, each column is 88 px wide. Column start positions are `24, 128, 232, 336, 440, 544, 648, 752, 856, 960, 1064, 1168`. A visual spanning columns 1–8 uses `X 24`, `W 816`; columns 9–12 use `X 856`, `W 400`.

For an ivory container, either insert **Insert → Shapes → Rounded rectangle**, or style the visual itself. Set **Fill/Background** to `#F4F1EA` at 0% transparency, turn the outline off or use a 1 px `#D8D2C8` border, use a 10–12 px corner radius, and add a subtle outside shadow. Put standalone container shapes behind their visuals using **View → Selection pane → Send backward**.

Power BI does not need a gradient for the accent line. Create two borderless rectangle shapes: red `#DD0000` at `X 0`, `Y 62`, `W 640`, `H 2`, and gold `#FFCC00` at `X 640`, `Y 62`, `W 640`, `H 2`.

Set the report font through **Design → Customize theme → Text → Font family → Segoe UI** when this control is available. Otherwise select each visual and use **Format visual → General → Title** plus the visual-specific Axis, Legend, Data labels and Values cards. Sentence case is a writing rule, not a Power BI switch: use `Structural clusters`, not `STRUCTURAL CLUSTERS` or `Structural Clusters`.

Add the title **Germany Data Observatory** and subtitle **Demographic structure, territorial clusters and federal elections**.

Once the other pages exist, add **Insert → Buttons → Navigator → Page navigator**. Keep the navigation compact; the full nine-item navigation may use two groups or a menu button if it does not fit at 1280 px.

Group the shell objects in the Selection pane. After the shell is stable, duplicate the page to reuse it as the starting point for other pages.

## 7. Build the Overview content

### Header KPI row

Add four Card visuals:

- `District Count` — expected default 400;
- `Observed Indicator Count` — expected 14;
- `Model Feature Count` — expected 11;
- `Cluster Count` — expected 4.

Use short labels: **Districts**, **Observed indicators**, **Model features**, **Structural clusters**.

### Main analytical area

Reserve columns 1–8 for the district cluster map. Use the reviewed BKG geometry in `data/processed/germany_districts_2024.topojson`; its `district_id` region key matches all 400 rows of `dim_district` exactly.

Add the map in Power BI Desktop or the Power BI service:

1. Add a **Shape map** visual. If it is absent in Desktop, enable **File → Options and settings → Options → Preview features → Shape map visual**, then restart Desktop.
2. In **Build visual**, add `dim_district[district_id]` to **Location** and `dim_cluster[cluster_name]` to **Legend**. Add `dim_district[district_name]`, `[District Count]` and the selected profile measures to **Tooltips**.
3. Open **Format visual → Map settings**. Set **Map type** to **Custom map**, choose **Add a map type**, and open `data/processed/germany_districts_2024.topojson`.
4. Choose `district_id` as the region key if Power BI asks. Use **View map type key** to confirm that the values look like `01001`, `01002`, … and preserve leading zeroes.
5. In **Colors**, assign the four colors from `dim_cluster[cluster_color_hex]` manually if conditional formatting is unavailable for the legend.
6. Add the attribution `© GeoBasis-DE / BKG (2026) dl-de/by-2-0` in a small text box below the map, with links documented in `metadata/district_geometry.md`.

Do not use `district_name` as Location: names are less stable than AGS and can be interpreted ambiguously by geocoding services.

In columns 9–12 add a cluster selector using `dim_cluster[cluster_name]` and a small cluster identity panel showing:

- cluster name;
- district count;
- profile summary;
- cluster colour.

### Bottom comparison

Create a Matrix for the first functional version:

- Rows: `dim_cluster[cluster_name]`;
- Values: `Population Aged 65+ %`, `Unemployment Rate %`, `Disposable Income per Capita`, `2025 Turnout %`.

Turn off totals. This matrix validates the four measures and can later be replaced with a more editorial dot plot or small-multiple visual.

## 8. Configure interactions

- The cluster selector should filter the district count, district map and cluster comparison.
- The fixed counts `Observed Indicator Count`, `Model Feature Count` and `Cluster Count` intentionally ignore feature/cluster filters.
- Keep Germany context available in tooltips and comparison measures.
- Do not sync party slicers to Overview because this page establishes the non-political structural context.

## 9. Save and version

Save and close Power BI Desktop so PBIP files are fully written. Review the Git diff and commit the `.pbip`, `.Report` and `.SemanticModel` directories together. Local `.pbi` cache files and `.env` must remain ignored.

## Completion criteria

The phase is complete when:

- the public report has nine ordered pages plus hidden `_Model QA`;
- the theme and page shell are applied;
- four KPI cards return 400, 14, 11 and 4;
- the cluster comparison shows four clusters and four correctly formatted indicators;
- the Shape map renders 400 districts and responds to the cluster selector;
- the PBIP project is saved inside the repository and its source files are ready for Git.
