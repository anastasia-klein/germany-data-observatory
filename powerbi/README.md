# Power BI workspace

Create the future `.pbip` project in this directory. Load the six CSV files from `data/processed` and relate each fact table to `dim_state` on `state_code` (one-to-many, single-direction filtering).

Keep the census-based nationality table and AZR foreign-population trend as separate facts. Measures should name the source concept explicitly when both appear on the same report page.
