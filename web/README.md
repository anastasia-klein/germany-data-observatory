# Web dashboard

[Open the public dashboard](https://anastasia-klein.github.io/germany-data-observatory/).

[Open the eight-page edition without Volt](https://anastasia-klein.github.io/germany-data-observatory/without-volt/).
Both editions share the same styles, Trebuchet MS font, charts, data and filters.
The second entry point excludes Volt from navigation and routing, including direct
`#volt` links, and omits its explanatory text from Methodology.

Nine interactive pages, including Volt, built from the same validated snapshot as
the Power BI reports. The app uses browser-native HTML, CSS and SVG: no paid map
service, runtime server, account, analytics tracker or external JavaScript CDN.

```sh
python3 src/build_web_data.py
node --test web/tests/*.test.mjs
python3 -m http.server 8765 --directory web
```

Open `http://localhost:8765/`. Direct `file://` access is not supported because
browsers restrict loading the data files. Python builds the snapshot; it does not
run on GitHub Pages. The static app performs filtering and calculations locally.

The Pages workflow validates the snapshot and publishes only the app and its data,
not the rest of the repository. Page names and filter selections are encoded in
the URL fragment, so links can open a specific view without server-side routing.

## Analytical parity

- District election summaries are unweighted means; other-party shares complete
  the party mix to 100%.
- Change uses districts with a complete party series over the selected period.
- Portrait uses the national district median (ties included) and **raw-scale**
  mean differences divided by the population SD.
- Explorer uses the model transformations and population SD, raw percentiles,
  and five nearest neighbours in PC1–PC4.
- Volt aggregates official state vote counts over valid second votes. It is not
  mixed into the district-level cluster analysis.
- Maps use locally packaged BKG geometry, joined on string district/state IDs.

Tests reconcile the headline findings, cluster profiles, Berlin peers, median
selection, missing-data behaviour, colour bands and Volt vote totals. Browser QA
is separate from these analytical tests. Data are a fixed snapshot, not a live feed.

Source and boundary attribution is available on the Methodology page. The
original Power BI projects remain unchanged.
