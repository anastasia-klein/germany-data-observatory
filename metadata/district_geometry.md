# District geometry

The map layer covers the 400 German Kreise and kreisfreie Städte used by the district analytical model. It is keyed by the five-character AGS field `district_id`, so Power BI can join shapes directly to `dim_district[district_id]` without name-based geocoding.

## Source and licence

- Publisher: Federal Agency for Cartography and Geodesy (Bundesamt für Kartographie und Geodäsie, BKG)
- Product: Verwaltungsgebiete 1:250 000 (VG250), reference date 1 January 2024
- WFS layer: `vg250:vg250_krs`
- WFS endpoint: `https://sgx.geodatenzentrum.de/wfs_vg250`
- Product page: `https://gdz.bkg.bund.de/index.php/default/open-data/verwaltungsgebiete-1-250-000-stand-01-01-vg250-01-01.html`
- Licence: Data Licence Germany – Attribution – Version 2.0 (`https://www.govdata.de/dl-de/by-2-0`)
- Required attribution: `© GeoBasis-DE / BKG (2026) dl-de/by-2-0`

The retrieval year in the attribution is 2026; the administrative reference year remains 2024. The report Methodology page and any public publication of the map must retain the attribution.

## Transformation

`src/build_district_geometry.py` performs the following reproducible steps:

1. download the Kreis layer as EPSG:4326 GeoJSON;
2. retain `gf = 4` (land areas), removing 33 separate maritime parts;
3. keep only `ags` and `gen`, renamed to `district_id` and `district_name`;
4. require exactly 400 unique AGS keys and an exact key match to `dim_district.csv`;
5. clean and simplify the geometry to 12% with weighted-area simplification and `keep-shapes` in mapshaper 0.6.113;
6. write both GeoJSON and Power BI-friendly TopoJSON.

Committed outputs:

- `data/processed/germany_districts_2024.topojson` — preferred input for the Power BI Shape map;
- `data/processed/germany_districts_2024.geojson` — interoperable GIS and web-map version.

Rebuild after installing mapshaper 0.6.113:

```bash
make download-geometry
```

The geometry is deliberately versioned separately from annual observations. Do not replace it merely because a newer boundary release exists: first assess territorial changes, update `geography_year`, rebuild the analytical tables and confirm the 400-key contract.
