#!/usr/bin/env python3
"""Turn raw election and structural CSVs into Power BI-ready tables."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "bundeswahlleiterin"
DESTATIS_RAW_DIR = ROOT / "data" / "raw" / "destatis"
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

ELECTION_FILES = (
    ("2005-09-18", "btw2005_kerg.csv", "wide"),
    ("2009-09-27", "btw2009_kerg.csv", "wide"),
    ("2013-09-22", "btw2013_kerg.csv", "wide"),
    ("2017-09-24", "btw2017_kerg2.csv", "flat"),
    ("2021-09-26", "btw2021-w_kerg2.csv", "flat"),
    ("2025-02-23", "btw25_kerg2.csv", "flat"),
)

PARTY_ALIASES = {
    "DIE LINKE": "Die Linke",
    "Die Linke.": "Die Linke",
    "BÜNDNIS 90/DIE GRÜNEN": "GRÜNE",
    "Die Tierschutzpartei": "Tierschutzpartei",
    "ödp": "ÖDP",
}

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


def percentage(numerator: str, denominator: str) -> str:
    if not numerator or not denominator or int(denominator) == 0:
        return ""
    value = int(numerator) / int(denominator) * 100
    return f"{value:.6f}".rstrip("0").rstrip(".")


def party_name(source_name: str) -> str:
    return PARTY_ALIASES.get(source_name, source_name)


def integer(value: str) -> int:
    return int(
        (value or "")
        .replace("\xa0", "")
        .replace("\u202f", "")
        .replace(" ", "")
        .replace(".", "")
        .strip()
    )


class TableParser(HTMLParser):
    """Extract HTML tables without adding a third-party dependency."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[dict[str, object]] = []
        self.table: Optional[dict[str, object]] = None
        self.row: Optional[list[str]] = None
        self.cell: Optional[list[str]] = None
        self.caption: Optional[list[str]] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            self.table = {"caption": "", "rows": []}
        elif self.table is not None and tag == "caption":
            self.caption = []
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.row is not None and tag in {"th", "td"}:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        if self.caption is not None:
            self.caption.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if self.row:
                self.table["rows"].append(self.row)
            self.row = None
        elif tag == "caption" and self.caption is not None and self.table is not None:
            self.table["caption"] = " ".join("".join(self.caption).split())
            self.caption = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def html_table(path: Path, caption_text: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8"))
    matches = [table for table in parser.tables if caption_text in str(table["caption"])]
    if len(matches) != 1:
        raise ValueError(f"Expected one table containing {caption_text!r} in {path}; found {len(matches)}")
    return matches[0]["rows"]


def write_csv(filename: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path = PROCESSED_DIR / filename
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
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


def transform_flat_election(path: Path, election_date: str) -> tuple[list[dict], list[dict]]:
    rows = read_csv_from_header(path, "Wahlart")
    state_rows = [row for row in rows if row.get("Gebietsart") == "Land"]
    party_rows = []
    turnout_rows = []
    for row in state_rows:
        common = {
            "election_date": election_date,
            "state_code": row["Gebietsnummer"].zfill(2),
        }
        if (
            row.get("Gruppenart") == "Partei"
            and row.get("Stimme") == "2"
            and number(row.get("Anzahl", ""))
        ):
            party_rows.append(
                common
                | {
                    "party": party_name(row["Gruppenname"]),
                    "source_party": row["Gruppenname"],
                    "votes": number(row["Anzahl"]),
                    "vote_share_percent": number(row["Prozent"]),
                    "previous_votes": number(row["VorpAnzahl"]),
                    "previous_vote_share_percent": number(row["VorpProzent"]),
                    "change_percentage_points": number(row["DiffProzentPkt"]),
                }
            )
        elif row.get("Gruppenname") in {"Wahlberechtigte", "Wähler", "Wählende"}:
            turnout_rows.append(
                common
                | {
                    "measure": "eligible_voters" if row["Gruppenname"] == "Wahlberechtigte" else "voters",
                    "value": number(row["Anzahl"]),
                    "share_percent": number(row["Prozent"]),
                }
            )
    return party_rows, turnout_rows


def transform_wide_election(path: Path, election_date: str) -> tuple[list[dict], list[dict]]:
    with path.open(encoding="latin-1", newline="") as source:
        rows = list(csv.reader(source, delimiter=";"))
    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "Nr")
    header = rows[header_index]
    state_rows = [
        row
        for row in rows[header_index + 3 :]
        if len(row) == len(header) and row[0] in {f"9{value:02d}" for value in range(1, 17)}
    ]
    party_rows = []
    turnout_rows = []
    for row in state_rows:
        state_code = row[0][1:]
        eligible_voters = number(row[3])
        voters = number(row[7])
        valid_second_votes = number(row[17])
        previous_valid_second_votes = number(row[18])
        turnout_rows.extend(
            [
                {
                    "election_date": election_date,
                    "state_code": state_code,
                    "measure": "eligible_voters",
                    "value": eligible_voters,
                    "share_percent": "",
                },
                {
                    "election_date": election_date,
                    "state_code": state_code,
                    "measure": "voters",
                    "value": voters,
                    "share_percent": percentage(voters, eligible_voters),
                },
            ]
        )
        for column in range(19, len(header), 4):
            source_party = header[column].strip()
            votes = number(row[column + 2]) if column + 2 < len(row) else ""
            if not source_party or source_party == "Übrige" or not votes:
                continue
            previous_votes = number(row[column + 3]) if column + 3 < len(row) else ""
            current_share = percentage(votes, valid_second_votes)
            previous_share = percentage(previous_votes, previous_valid_second_votes)
            change = ""
            if current_share and previous_share:
                change = f"{float(current_share) - float(previous_share):.6f}".rstrip("0").rstrip(".")
            party_rows.append(
                {
                    "election_date": election_date,
                    "state_code": state_code,
                    "party": party_name(source_party),
                    "source_party": source_party,
                    "votes": votes,
                    "vote_share_percent": current_share,
                    "previous_votes": previous_votes,
                    "previous_vote_share_percent": previous_share,
                    "change_percentage_points": change,
                }
            )
    return party_rows, turnout_rows


def transform_election_data() -> None:
    party_rows = []
    turnout_rows = []
    for election_date, filename, source_format in ELECTION_FILES:
        transformer = transform_flat_election if source_format == "flat" else transform_wide_election
        election_parties, election_turnout = transformer(RAW_DIR / filename, election_date)
        party_rows.extend(election_parties)
        turnout_rows.extend(election_turnout)
    write_csv(
        "fact_election_party_results.csv",
        [
            "election_date",
            "state_code",
            "party",
            "source_party",
            "votes",
            "vote_share_percent",
            "previous_votes",
            "previous_vote_share_percent",
            "change_percentage_points",
        ],
        sorted(party_rows, key=lambda row: (row["election_date"], row["state_code"], row["party"])),
    )
    write_csv(
        "fact_election_turnout.csv",
        ["election_date", "state_code", "measure", "value", "share_percent"],
        sorted(turnout_rows, key=lambda row: (row["election_date"], row["state_code"], row["measure"])),
    )


def transform_destatis_data() -> None:
    nationality_rows = html_table(
        DESTATIS_RAW_DIR / "population_by_nationality_2025.html",
        "Bevölkerung am 31.12.2025 nach Nationalität",
    )
    nationality_output = []
    for row in nationality_rows:
        if not row or row[0] not in STATE_BY_NAME:
            continue
        if len(row) != 7:
            raise ValueError(f"Unexpected Destatis nationality row: {row}")
        state = STATE_BY_NAME[row[0]]
        groups = (
            ("total", row[1], "", ""),
            ("german", row[2], "", ""),
            ("non_german", row[3], number(row[4]), "total_population"),
            ("eu_member_country", row[5], number(row[6]), "non_german_population"),
        )
        for population_group, count, share, share_of in groups:
            nationality_output.append(
                {
                    "reference_date": "2025-12-31",
                    "state_code": state.code,
                    "population_group": population_group,
                    "population_count": integer(count),
                    "share_percent": share,
                    "share_of": share_of,
                }
            )
    write_csv(
        "fact_population_nationality.csv",
        [
            "reference_date",
            "state_code",
            "population_group",
            "population_count",
            "share_percent",
            "share_of",
        ],
        sorted(
            nationality_output,
            key=lambda row: (row["state_code"], row["population_group"]),
        ),
    )

    foreign_rows = html_table(
        DESTATIS_RAW_DIR / "foreign_population_by_state_2018_2025.html",
        "Ausländische Bevölkerung 2018 bis 2025",
    )
    foreign_output = []
    years = list(range(2025, 2017, -1))
    for row in foreign_rows:
        if not row or row[0] not in STATE_BY_NAME:
            continue
        if len(row) != 9:
            raise ValueError(f"Unexpected Destatis foreign-population row: {row}")
        state = STATE_BY_NAME[row[0]]
        for year, value in zip(years, row[1:]):
            foreign_output.append(
                {
                    "year": year,
                    "state_code": state.code,
                    "foreign_population_count": integer(value),
                    "source_register": "Central Register of Foreigners (AZR)",
                }
            )
    write_csv(
        "fact_foreign_population.csv",
        ["year", "state_code", "foreign_population_count", "source_register"],
        sorted(foreign_output, key=lambda row: (row["state_code"], row["year"])),
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    transform_dimensions()
    transform_structural_data()
    transform_election_data()
    transform_destatis_data()
    print(f"Wrote analytical tables to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
