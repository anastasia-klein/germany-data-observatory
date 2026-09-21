#!/usr/bin/env python3
"""Turn raw election and structural CSVs into Power BI-ready tables."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "bundeswahlleiterin"
PROCESSED_DIR = ROOT / "data" / "processed"


@dataclass(frozen=True)
class State:
    code: str
    name: str
    nuts1: str


STATES = (
    State("01", "Schleswig-Holstein", "DEF"),
    State("02", "Hamburg", "DE6"),
    State("03", "Niedersachsen", "DE9"),
    State("04", "Bremen", "DE5"),
    State("05", "Nordrhein-Westfalen", "DEA"),
    State("06", "Hessen", "DE7"),
    State("07", "Rheinland-Pfalz", "DEB"),
    State("08", "Baden-Württemberg", "DE1"),
    State("09", "Bayern", "DE2"),
    State("10", "Saarland", "DEC"),
    State("11", "Berlin", "DE3"),
    State("12", "Brandenburg", "DE4"),
    State("13", "Mecklenburg-Vorpommern", "DE8"),
    State("14", "Sachsen", "DED"),
    State("15", "Sachsen-Anhalt", "DEE"),
    State("16", "Thüringen", "DEG"),
)
STATE_BY_NAME = {state.name: state for state in STATES}

# A focused first set that maps directly to the proposed dashboard pages.
INDICATORS = {
    "Fläche am 31.12.2023 (km²)": ("area_km2", 2023, "km2"),
    "Bevölkerung am 31.12.2023 - Insgesamt (in 1000)": ("population_thousands", 2023, "thousand_people"),
    "Bevölkerung am 31.12.2023 - Ausländer/-innen (%)": ("foreign_population_share", 2023, "percent"),
    "Bevölkerungsdichte am 31.12.2023 (EW je km²)": ("population_density", 2023, "people_per_km2"),
    "Zu- (+) bzw. Abnahme (-) der Bevölkerung 2023 - Geburtensaldo (je 1000 EW)": ("natural_population_change", 2023, "per_1000_people"),
    "Zu- (+) bzw. Abnahme (-) der Bevölkerung 2022 - Wanderungssaldo (je 1000 EW)": ("net_migration", 2022, "per_1000_people"),
    "Alter von ... bis ... Jahren am 31.12.2023 - unter 18 (%)": ("age_under_18_share", 2023, "percent"),
    "Alter von ... bis ... Jahren am 31.12.2023 - 60-74 (%)": ("age_60_74_share", 2023, "percent"),
    "Alter von ... bis ... Jahren am 31.12.2023 - 75 und mehr (%)": ("age_75_plus_share", 2023, "percent"),
    "Verfügbares Einkommen der privaten Haushalte 2021 (EUR je EW)": ("disposable_income_per_capita", 2021, "eur_per_person"),
    "Bruttoinlandsprodukt 2021 (EUR je EW)": ("gdp_per_capita", 2021, "eur_per_person"),
    "Sozialversicherungspflichtig Beschäftigte am 30.06.2023 - insgesamt (je 1000 EW)": ("employees_subject_to_social_insurance", 2023, "per_1000_people"),
    "Empfänger/-innen von Leistungen nach SGB II  August 2024 -  insgesamt (je 1000 EW)": ("social_benefit_recipients", 2024, "per_1000_people"),
    "Arbeitslosenquote November 2024 - insgesamt": ("unemployment_rate", 2024, "percent"),
}


def read_csv_from_header(path: Path, first_header_cell: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.reader(source, delimiter=";"))
    header_index = next(i for i, row in enumerate(rows) if row and row[0] == first_header_cell)
    header = rows[header_index]
    return [dict(zip(header, row)) for row in rows[header_index + 1 :] if any(row)]


def number(value: str) -> str:
    cleaned = (value or "").strip().replace(".", "").replace(",", ".")
    if cleaned in {"", "-", "."}:
        return ""
    return cleaned


def write_csv(filename: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path = PROCESSED_DIR / filename
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def transform_dimensions() -> None:
    write_csv(
        "dim_state.csv",
        ["state_code", "state_name", "nuts1_code"],
        [
            {"state_code": state.code, "state_name": state.name, "nuts1_code": state.nuts1}
            for state in STATES
        ],
    )


def transform_structural_data() -> None:
    raw_rows = read_csv_from_header(RAW_DIR / "btw2025_strukturdaten.csv", "Land")
    state_rows = [row for row in raw_rows if row.get("Wahlkreis-Name") == "Land insgesamt"]
    output = []
    for row in state_rows:
        state = STATE_BY_NAME[row["Land"]]
        for source_column, (indicator, year, unit) in INDICATORS.items():
            output.append(
                {
                    "state_code": state.code,
                    "year": year,
                    "indicator": indicator,
                    "value": number(row[source_column]),
                    "unit": unit,
                    "source": "Bundeswahlleiterin structural data 2025",
                }
            )
    write_csv(
        "fact_state_indicators.csv",
        ["state_code", "year", "indicator", "value", "unit", "source"],
        output,
    )


def transform_election_data() -> None:
    rows = read_csv_from_header(RAW_DIR / "btw25_kerg2.csv", "Wahlart")
    state_rows = [row for row in rows if row.get("Gebietsart") == "Land"]
    party_rows = []
    turnout_rows = []
    for row in state_rows:
        common = {
            "election_date": "2025-02-23",
            "state_code": row["Gebietsnummer"].zfill(2),
        }
        if row.get("Gruppenart") == "Partei" and row.get("Stimme") == "2":
            party_rows.append(
                common
                | {
                    "party": row["Gruppenname"],
                    "votes": number(row["Anzahl"]),
                    "vote_share_percent": number(row["Prozent"]),
                    "previous_votes": number(row["VorpAnzahl"]),
                    "previous_vote_share_percent": number(row["VorpProzent"]),
                    "change_percentage_points": number(row["DiffProzentPkt"]),
                }
            )
        elif row.get("Gruppenname") in {"Wahlberechtigte", "Wählende"}:
            turnout_rows.append(
                common
                | {
                    "measure": "eligible_voters" if row["Gruppenname"] == "Wahlberechtigte" else "voters",
                    "value": number(row["Anzahl"]),
                    "share_percent": number(row["Prozent"]),
                }
            )
    write_csv(
        "fact_election_party_results.csv",
        [
            "election_date",
            "state_code",
            "party",
            "votes",
            "vote_share_percent",
            "previous_votes",
            "previous_vote_share_percent",
            "change_percentage_points",
        ],
        party_rows,
    )
    write_csv(
        "fact_election_turnout.csv",
        ["election_date", "state_code", "measure", "value", "share_percent"],
        turnout_rows,
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    transform_dimensions()
    transform_structural_data()
    transform_election_data()
    print(f"Wrote analytical tables to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()

