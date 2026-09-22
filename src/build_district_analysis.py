#!/usr/bin/env python3
"""Build Kreis-level BI tables and a reproducible non-political cluster model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import RobustScaler, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "district_sources.json"
RAW_DIR = ROOT / "data" / "raw" / "regionalatlas"
OUT = ROOT / "data" / "processed"

STATE_NAMES = {
    "01": "Schleswig-Holstein", "02": "Hamburg", "03": "Niedersachsen",
    "04": "Bremen", "05": "Nordrhein-Westfalen", "06": "Hessen",
    "07": "Rheinland-Pfalz", "08": "Baden-Württemberg", "09": "Bayern",
    "10": "Saarland", "11": "Berlin", "12": "Brandenburg",
    "13": "Mecklenburg-Vorpommern", "14": "Sachsen",
    "15": "Sachsen-Anhalt", "16": "Thüringen",
}

FEATURE_METADATA = {
    "population_density": ("Population density", "people_per_km2"),
    "population_change_per_10000": ("Annual population change", "per_10000_people"),
    "foreign_population_share": ("Foreign population share", "percent"),
    "natural_balance_per_10000": ("Birth/death balance", "per_10000_people"),
    "migration_balance_per_10000": ("Migration balance", "per_10000_people"),
    "age_under_18_share": ("Population aged 0–17", "percent"),
    "age_65_plus_share": ("Population aged 65+", "percent"),
    "workplace_density": ("Workplace density", "employed_per_1000_working_age"),
    "manufacturing_employment_share": ("Manufacturing employment share", "percent"),
    "services_employment_share": ("Services employment share", "percent"),
    "unemployment_rate": ("Unemployment rate", "percent"),
    "disposable_income_per_capita": ("Disposable income per capita", "eur_per_person"),
    "gdp_per_capita": ("GDP per capita", "eur_per_person"),
    "minimum_security_rate": ("Minimum-security benefit rate", "percent"),
}

PARTIES = {
    "ai0501": ("party_group_cdu_csu", "CDU/CSU"),
    "ai0502": ("party_group_spd", "SPD"),
    "ai0503": ("party_group_fdp", "FDP"),
    "ai0504": ("party_group_greens", "GRÜNE"),
    "ai0505": ("party_group_left", "Die Linke"),
    "ai0507": ("party_group_afd", "AfD"),
}


def raw_rows(dataset: str, year: int) -> pd.DataFrame:
    filename = f"{dataset.lower().replace('-', '_')}_{year}.json"
    payload = json.loads((RAW_DIR / filename).read_text(encoding="utf-8"))
    frame = pd.DataFrame(feature["attributes"] for feature in payload["features"])
    frame["ags"] = frame["ags"].astype(str).str.zfill(5)
    # Regionalatlas geometry uses state-like IDs for these two city states.
    frame["ags"] = frame["ags"].replace({"00002": "02000", "00011": "11000"})
    if len(frame) != 400 or frame["ags"].nunique() != 400:
        raise ValueError(f"{filename} does not contain 400 unique district keys")
    return frame.sort_values("ags").reset_index(drop=True)


def district_type(name: str) -> str:
    value = name.lower()
    if "kreisfreie stadt" in value or "stadtkreis" in value or value in {"hamburg", "berlin"}:
        return "urban_district"
    if any(label in value for label in ("region hannover", "regionalverband", "städteregion")):
        return "special_district_association"
    return "rural_district"


def transform(series: pd.Series, method: str) -> pd.Series:
    if method == "identity":
        return series.astype(float)
    if method == "log1p":
        if (series < 0).any():
            raise ValueError(f"log1p cannot be applied to negative values in {series.name}")
        return np.log1p(series.astype(float))
    raise ValueError(f"Unknown transform: {method}")


def stable_cluster_ids(labels: np.ndarray, pc1: np.ndarray) -> np.ndarray:
    order = sorted(np.unique(labels), key=lambda label: float(pc1[labels == label].mean()))
    mapping = {old: new for new, old in enumerate(order, start=1)}
    return np.array([mapping[label] for label in labels])


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources = config["sources"]
    OUT.mkdir(parents=True, exist_ok=True)

    first = raw_rows(sources[0]["dataset"], sources[0]["year"])
    names = first["gen2"].str.strip().str.replace(r"^\s+", "", regex=True)
    districts = pd.DataFrame({
        "district_id": first["ags"],
        "district_name": first["gen"].str.strip(),
        "district_name_official": names,
        "district_type": names.map(district_type),
        "state_code": first["ags"].str[:2],
    })
    districts["state_name"] = districts["state_code"].map(STATE_NAMES)
    districts["geography_year"] = config["geography_year"]
    districts.to_csv(OUT / "dim_district.csv", index=False)

    feature_wide = districts[["district_id"]].copy().set_index("district_id")
    catalog_rows = []
    for source in (item for item in sources if item["use_for_clustering"]):
        frame = raw_rows(source["dataset"], source["year"]).set_index("ags")
        for raw_field, feature in source["fields"].items():
            feature_wide[feature] = pd.to_numeric(frame[raw_field], errors="coerce")
            title, unit = FEATURE_METADATA[feature]
            catalog_rows.append({
                "feature_id": feature,
                "feature_name": title,
                "unit": unit,
                "reference_year": source["year"],
                "source_dataset": source["dataset"],
                "included_in_clustering": feature in config["clustering"]["selected_features"],
                "transform": config["clustering"]["selected_features"].get(feature, "not_used"),
                "exclusion_reason": config["clustering"]["excluded_correlated_features"].get(feature, ""),
            })
    if feature_wide.isna().any().any():
        raise ValueError(f"Missing district features: {feature_wide.isna().sum().to_dict()}")

    catalog = pd.DataFrame(catalog_rows).sort_values("feature_id")
    catalog.to_csv(OUT / "dim_district_feature.csv", index=False)
    long_features = (
        feature_wide.reset_index()
        .melt(id_vars="district_id", var_name="feature_id", value_name="value")
        .merge(catalog[["feature_id", "reference_year", "unit", "source_dataset"]], on="feature_id")
        .sort_values(["district_id", "feature_id"])
    )
    long_features.to_csv(OUT / "fact_district_features.csv", index=False)

    selected = list(config["clustering"]["selected_features"])
    transformed = pd.DataFrame(index=feature_wide.index)
    for feature, method in config["clustering"]["selected_features"].items():
        transformed[feature] = transform(feature_wide[feature], method)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(transformed)
    pca = PCA(n_components=config["clustering"]["pca_variance_target"], svd_solver="full")
    scores = pca.fit_transform(scaled)

    diagnostics = []
    candidate_labels = {}
    for k in config["clustering"]["candidate_k"]:
        labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(scores)
        sizes = pd.Series(labels).value_counts()
        diagnostics.append({
            "k": k,
            "silhouette_score": silhouette_score(scores, labels),
            "calinski_harabasz_score": calinski_harabasz_score(scores, labels),
            "davies_bouldin_score": davies_bouldin_score(scores, labels),
            "minimum_cluster_size": int(sizes.min()),
            "passes_minimum_size": bool(sizes.min() >= config["clustering"]["minimum_cluster_size"]),
        })
        candidate_labels[k] = labels
    diagnostic_frame = pd.DataFrame(diagnostics)
    eligible = diagnostic_frame[diagnostic_frame["passes_minimum_size"]]
    if eligible.empty:
        eligible = diagnostic_frame
    chosen_k = int(eligible.sort_values(["silhouette_score", "k"], ascending=[False, True]).iloc[0]["k"])
    labels = stable_cluster_ids(candidate_labels[chosen_k], scores[:, 0])
    diagnostic_frame["selected"] = diagnostic_frame["k"].eq(chosen_k)
    diagnostic_frame.to_csv(OUT / "clustering_diagnostics.csv", index=False, float_format="%.10f")

    assignments = pd.DataFrame({"district_id": transformed.index, "cluster_id": labels})
    assignments["cluster_id"] = assignments["cluster_id"].map(lambda value: f"cluster_{value}")
    assignments.to_csv(OUT / "fact_cluster_assignment.csv", index=False)

    score_columns = [f"pc{number}" for number in range(1, scores.shape[1] + 1)]
    score_frame = pd.DataFrame(scores, columns=score_columns)
    score_frame.insert(0, "district_id", transformed.index)
    score_frame.to_csv(OUT / "district_pca.csv", index=False, float_format="%.10f")

    loadings = pd.DataFrame(
        pca.components_.T,
        index=selected,
        columns=score_columns,
    ).rename_axis("feature_id").reset_index()
    loadings.to_csv(OUT / "pca_loadings.csv", index=False, float_format="%.10f")
    pd.DataFrame({
        "component": score_columns,
        "explained_variance_ratio": pca.explained_variance_ratio_,
        "cumulative_explained_variance_ratio": np.cumsum(pca.explained_variance_ratio_),
    }).to_csv(OUT / "pca_explained_variance.csv", index=False, float_format="%.10f")

    zscores = pd.DataFrame(scaled, index=transformed.index, columns=selected)
    zscores["cluster_id"] = assignments.set_index("district_id")["cluster_id"]
    profiles = zscores.groupby("cluster_id").mean().reset_index().melt(
        id_vars="cluster_id", var_name="feature_id", value_name="mean_z_score"
    )
    raw_profiles = feature_wide[selected].copy()
    raw_profiles["cluster_id"] = assignments.set_index("district_id")["cluster_id"]
    raw_profiles = raw_profiles.groupby("cluster_id").mean().reset_index().melt(
        id_vars="cluster_id", var_name="feature_id", value_name="mean_raw_value"
    )
    profiles = profiles.merge(raw_profiles, on=["cluster_id", "feature_id"])
    profiles.to_csv(OUT / "cluster_profiles.csv", index=False, float_format="%.10f")

    cluster_rows = []
    for cluster_id, group in profiles.groupby("cluster_id"):
        top = group.reindex(group["mean_z_score"].abs().sort_values(ascending=False).index).head(3)
        summary = "; ".join(
            f"{row.feature_id} {'high' if row.mean_z_score > 0 else 'low'}"
            for row in top.itertuples()
        )
        cluster_rows.append({
            "cluster_id": cluster_id,
            "cluster_name": cluster_id.replace("_", " ").title(),
            "district_count": int((assignments["cluster_id"] == cluster_id).sum()),
            "profile_summary": summary,
        })
    pd.DataFrame(cluster_rows).sort_values("cluster_id").to_csv(OUT / "dim_cluster.csv", index=False)

    party_dimension = pd.DataFrame(
        [{"party_group_id": identifier, "party_group_name": name} for identifier, name in PARTIES.values()]
    )
    party_dimension.to_csv(OUT / "dim_party_group.csv", index=False)
    election_rows, turnout_rows = [], []
    for source in (item for item in sources if item["dataset"] == "AI005"):
        frame = raw_rows(source["dataset"], source["year"])
        election_id = f"BTW{source['year']}"
        for row in frame.itertuples(index=False):
            for raw_field, (party_group_id, _) in PARTIES.items():
                value = getattr(row, raw_field)
                unavailable = pd.isna(value) or value < 0 or value > 100
                election_rows.append({
                    "district_id": row.ags,
                    "election_id": election_id,
                    "election_year": source["year"],
                    "party_group_id": party_group_id,
                    "second_vote_share_percent": np.nan if unavailable else value,
                    "value_status": "not_available" if unavailable else "reported",
                    "source_dataset": source["dataset"],
                })
            turnout_rows.append({
                "district_id": row.ags,
                "election_id": election_id,
                "election_year": source["year"],
                "turnout_percent": row.ai0506,
                "source_dataset": source["dataset"],
            })
    election_fact = pd.DataFrame(election_rows)
    turnout_fact = pd.DataFrame(turnout_rows)
    election_fact.to_csv(OUT / "fact_district_election_results.csv", index=False)
    turnout_fact.to_csv(OUT / "fact_district_election_turnout.csv", index=False)

    election_cluster = election_fact.merge(assignments, on="district_id").groupby(
        ["cluster_id", "election_id", "election_year", "party_group_id"], as_index=False
    )["second_vote_share_percent"].mean()
    election_cluster.rename(
        columns={"second_vote_share_percent": "unweighted_mean_second_vote_share_percent"}
    ).to_csv(OUT / "cluster_election_results.csv", index=False, float_format="%.10f")

    raw_labels = AgglomerativeClustering(n_clusters=chosen_k, linkage="ward").fit_predict(scaled)
    robust_scaled = RobustScaler().fit_transform(transformed)
    robust_scores = PCA(n_components=scores.shape[1]).fit_transform(robust_scaled)
    robust_labels = AgglomerativeClustering(n_clusters=chosen_k, linkage="ward").fit_predict(robust_scores)
    metadata = {
        "algorithm": "Ward hierarchical agglomerative clustering",
        "chosen_k": chosen_k,
        "selection_rule": "Highest silhouette among candidates meeting the minimum cluster-size rule",
        "minimum_cluster_size": config["clustering"]["minimum_cluster_size"],
        "features": selected,
        "excluded_political_features": True,
        "scaler": "StandardScaler",
        "feature_transforms": config["clustering"]["selected_features"],
        "pca_components": scores.shape[1],
        "pca_explained_variance": round(float(pca.explained_variance_ratio_.sum()), 10),
        "robustness_adjusted_rand": {
            "direct_scaled_vs_primary": round(float(adjusted_rand_score(labels, raw_labels)), 10),
            "robust_scaled_pca_vs_primary": round(float(adjusted_rand_score(labels, robust_labels)), 10),
        },
        "linkage_matrix_rows": int(linkage(scores, method="ward").shape[0]),
    }
    (OUT / "clustering_model_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Built district model: 400 districts, {len(selected)} clustering features, "
        f"{scores.shape[1]} PCs, k={chosen_k}"
    )


if __name__ == "__main__":
    main()
