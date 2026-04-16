#!/usr/bin/env python3
import argparse
import html
import os
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, text

DEFAULT_DB_URL = os.getenv("DATABASE_URL", "postgresql://dwh:DBTTEST@localhost:5432/dwh")
DEFAULT_INDEX_URL = "https://www.sailwave.com/results/Bartley"
DEFAULT_CLUB_NAME = "Bartley Sailing Club"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import recent Sailwave Bartley results into the app database.")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="Database URL")
    parser.add_argument("--index-url", default=DEFAULT_INDEX_URL, help="Sailwave index URL")
    parser.add_argument("--club-name", default=DEFAULT_CLUB_NAME, help="Club name in CLUBCONTROL")
    parser.add_argument("--year", type=int, default=2026, help="Only import result files starting with this year")
    parser.add_argument("--limit", type=int, default=8, help="Maximum number of result pages to import")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report only, without writing to DB")
    return parser.parse_args()


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def strip_tags(raw: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", raw, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def prettify_filename(stem: str) -> str:
    value = re.sub(r"([0-9])([A-Z])", r"\1 \2", stem)
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    value = value.replace("_", " ")
    return re.sub(r"\s+", " ", value).strip()


def parse_time_to_seconds(raw: str):
    value = (raw or "").strip().replace(" ", "")
    if not value or value in {"-", "DNF", "DNC", "RET", "OCS", "DNS", "DSQ"}:
        return None

    if re.fullmatch(r"\d+\.\d+\.\d+", value):
        hh, mm, ss = [int(p) for p in value.split(".")]
        return hh * 3600 + mm * 60 + ss

    if re.fullmatch(r"\d+\.\d+", value):
        mm, ss = [int(p) for p in value.split(".")]
        return mm * 60 + ss

    if re.fullmatch(r"\d+:\d+:\d+", value):
        hh, mm, ss = [int(p) for p in value.split(":")]
        return hh * 3600 + mm * 60 + ss

    if value.isdigit():
        return int(value)

    return None


def parse_result_page(url: str):
    page_html = fetch_text(url)
    stem = os.path.basename(urlparse(url).path).rsplit(".", 1)[0]
    series_name = prettify_filename(stem)

    race_pattern = re.compile(
        r'<h3 class="racetitle"[^>]*>Race\s*(\d+).*?(\d{4}-\d{2}-\d{2}).*?at.*?(\d{2}:\d{2}).*?</h3>.*?<table class="racetable".*?<tbody>(.*?)</tbody>',
        re.I | re.S,
    )
    row_pattern = re.compile(r'<tr class="[^"]*racerow[^"]*">(.*?)</tr>', re.I | re.S)
    cell_pattern = re.compile(r'<t[dh][^>]*>(.*?)</t[dh]>', re.I | re.S)

    races = []
    for match in race_pattern.finditer(page_html):
        race_no = int(match.group(1))
        race_date = match.group(2)
        race_time = match.group(3)
        tbody = match.group(4)

        started_at = datetime.strptime(f"{race_date} {race_time}", "%Y-%m-%d %H:%M")
        rows = []
        for row_html in row_pattern.findall(tbody):
            cells = [strip_tags(cell) for cell in cell_pattern.findall(row_html)]
            if len(cells) < 10:
                continue

            rank_raw = cells[0]
            m = re.match(r"(\d+)", rank_raw)
            if not m:
                continue

            position = int(m.group(1))
            helm = cells[1]
            crew = cells[2]
            boat = cells[3]
            sail_no = cells[4] or "UNKNOWN"
            rating = cells[5]
            elapsed_sec = parse_time_to_seconds(cells[8])
            corrected_sec = parse_time_to_seconds(cells[9])
            if not helm or not boat or elapsed_sec is None:
                continue

            try:
                handicap = int(float(rating)) if rating else None
            except ValueError:
                handicap = None

            display_name = helm if not crew else f"{helm} / {crew}"
            rows.append(
                {
                    "position": position,
                    "helm": helm,
                    "crew": crew or None,
                    "sailor_display": display_name,
                    "boat": boat,
                    "sail_number": sail_no,
                    "handicap": handicap,
                    "elapsed_sec": elapsed_sec,
                    "corrected_sec": corrected_sec,
                }
            )

        if rows:
            races.append({"race_no": race_no, "started_at": started_at, "rows": rows})

    return series_name, races


def get_club_id(conn, club_name: str) -> int:
    club_id = conn.execute(
        text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE LOWER(name) = LOWER(:name) LIMIT 1'),
        {"name": club_name},
    ).scalar()
    if club_id is None:
        raise RuntimeError(f"Club not found: {club_name}")
    return int(club_id)


def get_or_create_series(conn, club_id: int, series_name: str, year: int) -> int:
    existing = conn.execute(
        text(
            'SELECT key FROM "RACINGAPP"."SERIESCONTROL" '
            'WHERE LOWER(name) = LOWER(:name) AND club = :club '
            'ORDER BY key DESC LIMIT 1'
        ),
        {"name": series_name, "club": str(club_id)},
    ).scalar()
    if existing is not None:
        return int(existing)

    return int(
        conn.execute(
            text(
                'INSERT INTO "RACINGAPP"."SERIESCONTROL" (key, year, name, club) '
                "VALUES (nextval('key'), :year, :name, :club) RETURNING key"
            ),
            {"year": str(year), "name": series_name, "club": str(club_id)},
        ).scalar()
    )


def get_or_create_handicap(conn, boat_name: str, handicap: int | None):
    existing = conn.execute(
        text(
            'SELECT key, handicap FROM "RACINGAPP"."HANDICAPCONTROL" '
            'WHERE LOWER(boat) = LOWER(:boat) ORDER BY date DESC, key DESC LIMIT 1'
        ),
        {"boat": boat_name},
    ).mappings().first()
    if existing:
        return int(existing["key"]), int(existing["handicap"])

    resolved_handicap = int(handicap or 1000)
    new_key = conn.execute(
        text(
            'INSERT INTO "RACINGAPP"."HANDICAPCONTROL" (key, date, boat, handicap) '
            "VALUES (nextval('key'), :date, :boat, :handicap) RETURNING key"
        ),
        {"date": date.today(), "boat": boat_name, "handicap": resolved_handicap},
    ).scalar()
    return int(new_key), resolved_handicap


def split_name(full_name: str):
    parts = [p for p in full_name.strip().split(" ") if p]
    if not parts:
        return "Unknown", None
    first = parts[0].title()
    last = " ".join(parts[1:]).title() if len(parts) > 1 else None
    return first, last


def get_or_create_sailor(conn, club_id: int, full_name: str) -> int:
    normalized = re.sub(r"\s+", " ", full_name).strip().title()
    existing = conn.execute(
        text(
            'SELECT key FROM "RACINGAPP"."SAILORCONTROL" '
            'WHERE club = :club AND LOWER(fullname) = LOWER(:name) ORDER BY key DESC LIMIT 1'
        ),
        {"club": club_id, "name": normalized},
    ).scalar()
    if existing is not None:
        return int(existing)

    first, last = split_name(normalized)
    new_key = conn.execute(
        text(
            'INSERT INTO "RACINGAPP"."SAILORCONTROL" (key, fullname, firstname, lastname, club) '
            "VALUES (nextval('key'), :fullname, :firstname, :lastname, :club) RETURNING key"
        ),
        {"fullname": normalized, "firstname": first, "lastname": last, "club": club_id},
    ).scalar()
    return int(new_key)


def get_or_create_boat(conn, sailor_id: int, handicap_key: int, sail_number: str) -> int:
    existing = conn.execute(
        text(
            'SELECT key FROM "RACINGAPP"."BOATCONTROL" '
            'WHERE sailor = :sailor AND sail_number = :sail_number ORDER BY key DESC LIMIT 1'
        ),
        {"sailor": sailor_id, "sail_number": sail_number},
    ).scalar()
    if existing is not None:
        return int(existing)

    new_key = conn.execute(
        text(
            'INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number) '
            "VALUES (nextval('key'), :boat, :sailor, :sail_number) RETURNING key"
        ),
        {"boat": handicap_key, "sailor": sailor_id, "sail_number": sail_number},
    ).scalar()
    return int(new_key)


def delete_existing_race(conn, club_id: int, series_id: int, race_no: int, started_at: datetime):
    existing_race_id = conn.execute(
        text(
            'SELECT key FROM "RACINGAPP"."RACE" '
            'WHERE club = :club AND series = :series AND race_no = :race_no AND started_at = :started_at '
            'ORDER BY key DESC LIMIT 1'
        ),
        {"club": club_id, "series": series_id, "race_no": race_no, "started_at": started_at},
    ).scalar()
    if existing_race_id is None:
        return

    conn.execute(
        text('DELETE FROM "RACINGAPP"."LAP" WHERE race_entry_id IN (SELECT key FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id)'),
        {"race_id": existing_race_id},
    )
    conn.execute(text('DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id'), {"race_id": existing_race_id})
    conn.execute(text('DELETE FROM "RACINGAPP"."RACE" WHERE key = :race_id'), {"race_id": existing_race_id})


def insert_completed_race(conn, club_id: int, series_id: int, race_no: int, started_at: datetime, rows: list[dict]):
    max_elapsed = max((row["elapsed_sec"] for row in rows if row.get("elapsed_sec") is not None), default=0)
    ended_at = started_at + timedelta(seconds=max_elapsed or 0)

    delete_existing_race(conn, club_id, series_id, race_no, started_at)

    race_id = conn.execute(
        text(
            'INSERT INTO "RACINGAPP"."RACE" '
            '(key, club, series, race_no, status, started_at, ended_at, results_status, results_locked_at, source_mode) '
            "VALUES (nextval('key'), :club, :series, :race_no, 'finished', :started_at, :ended_at, 'locked', CURRENT_TIMESTAMP, 'retrospective') RETURNING key"
        ),
        {"club": club_id, "series": series_id, "race_no": race_no, "started_at": started_at, "ended_at": ended_at},
    ).scalar()

    for row in rows:
        handicap_key, resolved_handicap = get_or_create_handicap(conn, row["boat"], row.get("handicap"))
        helm_id = get_or_create_sailor(conn, club_id, row["helm"])
        if row.get("crew"):
            get_or_create_sailor(conn, club_id, row["crew"])
        boatkey = get_or_create_boat(conn, helm_id, handicap_key, row["sail_number"])

        entry_id = conn.execute(
            text(
                'INSERT INTO "RACINGAPP"."RACE_ENTRY" '
                '(key, race_id, boatkey, sailor, boat, sail_number, handicap, source) '
                "VALUES (nextval('key'), :race_id, :boatkey, :sailor, :boat, :sail_number, :handicap, 'sailwave') RETURNING key"
            ),
            {
                "race_id": race_id,
                "boatkey": boatkey,
                "sailor": row["sailor_display"],
                "boat": row["boat"],
                "sail_number": row["sail_number"],
                "handicap": resolved_handicap,
            },
        ).scalar()

        conn.execute(
            text(
                'INSERT INTO "RACINGAPP"."LAP" '
                '(key, race_entry_id, lap_number, is_finish, elapsed_sec, corrected_sec, position, source) '
                "VALUES (nextval('key'), :race_entry_id, 1, TRUE, :elapsed_sec, :corrected_sec, :position, 'sailwave')"
            ),
            {
                "race_entry_id": entry_id,
                "elapsed_sec": row.get("elapsed_sec") or 0,
                "corrected_sec": row.get("corrected_sec"),
                "position": row.get("position"),
            },
        )

    return int(race_id)


def find_recent_result_urls(index_url: str, year: int, limit: int):
    page_html = fetch_text(index_url)
    hrefs = re.findall(r'href="([^"]+\.htm)"', page_html, flags=re.I)

    results = []
    seen = set()
    for href in hrefs:
        absolute = urljoin(index_url + "/", href)
        filename = os.path.basename(urlparse(absolute).path)
        stem = filename.rsplit('.', 1)[0]
        if absolute in seen:
            continue
        if not stem.startswith(str(year)):
            continue
        lowered = stem.lower()
        if any(skip in lowered for skip in ["fleet", "overall"]):
            continue
        if not any(key in lowered for key in ["handicap", "pursuit", "sunday", "wednesday", "saturday"]):
            continue
        seen.add(absolute)
        results.append(absolute)
        if len(results) >= limit:
            break

    return results


def main():
    args = parse_args()
    engine = create_engine(args.db_url)

    urls = find_recent_result_urls(args.index_url, args.year, args.limit)
    if not urls:
        print("No matching Sailwave result pages found.")
        return

    print(f"Found {len(urls)} result page(s) to import")
    for u in urls:
        print(f" - {u}")

    if args.dry_run:
        for u in urls:
            series_name, races = parse_result_page(u)
            print(f"DRY RUN | {series_name} | races={len(races)} | entries={[len(r['rows']) for r in races]}")
        return

    imported_races = 0
    imported_entries = 0

    with engine.begin() as conn:
        club_id = get_club_id(conn, args.club_name)

        for url in urls:
            series_name, races = parse_result_page(url)
            if not races:
                print(f"SKIP | {url} | no completed race tables found")
                continue

            year_match = re.match(r"(\d{4})", series_name)
            series_year = int(year_match.group(1)) if year_match else args.year
            series_id = get_or_create_series(conn, club_id, series_name, series_year)

            for race in races:
                race_id = insert_completed_race(
                    conn,
                    club_id,
                    series_id,
                    race["race_no"],
                    race["started_at"],
                    race["rows"],
                )
                imported_races += 1
                imported_entries += len(race["rows"])
                print(
                    f"IMPORTED | series={series_name} | race_id={race_id} | race_no={race['race_no']} | "
                    f"started_at={race['started_at']} | entries={len(race['rows'])}"
                )

    print(f"SUCCESS | imported_races={imported_races} | imported_entries={imported_entries}")


if __name__ == "__main__":
    main()
