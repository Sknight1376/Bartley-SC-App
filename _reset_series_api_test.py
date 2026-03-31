import argparse
import os
import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

DEFAULT_DB_URL = "postgresql://dwh:DBTTEST@localhost:5432/dwh"
DEFAULT_SERIES = "Series_API_Test"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset a test series by deleting old races and creating fresh upcoming races."
    )
    parser.add_argument(
        "--series-name",
        default=DEFAULT_SERIES,
        help=f"Series name in RACINGAPP.SERIESCONTROL (default: {DEFAULT_SERIES})",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DB_URL),
        help="Database URL (default: DATABASE_URL env var or local postgres)",
    )
    parser.add_argument(
        "--days-ahead",
        type=int,
        default=1,
        help="Days from now for first race start time (default: 1)",
    )
    parser.add_argument(
        "--race-count",
        type=int,
        default=1,
        help="Number of not_started races to create (default: 1)",
    )
    parser.add_argument(
        "--spacing-minutes",
        type=int,
        default=60,
        help="Minutes between created races (default: 60)",
    )
    parser.add_argument(
        "--cleanup-scope",
        choices=["series", "club"],
        default="club",
        help="Delete old races for this series only, or for entire club (default: club)",
    )
    return parser.parse_args()


def find_series(conn, series_name: str):
    row = conn.execute(
        text(
            'SELECT key, club, name FROM "RACINGAPP"."SERIESCONTROL" '
            'WHERE LOWER(name) = LOWER(:n) ORDER BY key DESC LIMIT 1'
        ),
        {"n": series_name},
    ).fetchone()
    if row is None:
        print(f"ERROR: No SERIESCONTROL row found with name {series_name}")
        sys.exit(1)
    return row.key, row.club, row.name


def cleanup_races(conn, club: int, series_id: int, scope: str):
    if scope == "series":
        race_filter = 'WHERE r.series = :series_id'
        race_filter_simple = 'WHERE series = :series_id'
        params = {"series_id": series_id}
    else:
        race_filter = 'WHERE r.club = :club'
        race_filter_simple = 'WHERE club = :club'
        params = {"club": club}

    deleted_laps = conn.execute(
        text(
            'DELETE FROM "RACINGAPP"."LAP" WHERE race_entry_id IN ('
            '  SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re '
            '  JOIN "RACINGAPP"."RACE" r ON re.race_id = r.key '
            f'  {race_filter}'
            ')'
        ),
        params,
    ).rowcount

    deleted_entries = conn.execute(
        text(
            'DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id IN ('
            '  SELECT key FROM "RACINGAPP"."RACE" '
            f'  {race_filter_simple}'
            ')'
        ),
        params,
    ).rowcount

    deleted_races = conn.execute(
        text(
            'DELETE FROM "RACINGAPP"."RACE" '
            f'  {race_filter_simple}'
        ),
        params,
    ).rowcount

    return deleted_laps or 0, deleted_entries or 0, deleted_races or 0


def create_races(conn, club: int, series_id: int, race_count: int, start_time: datetime, spacing_minutes: int):
    keys = []
    for race_no in range(1, race_count + 1):
        started_at = start_time + timedelta(minutes=spacing_minutes * (race_no - 1))
        new_race = conn.execute(
            text(
                'INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at, ended_at) '
                "VALUES (:club, :series, :race_no, 'not_started', :started_at, NULL) "
                'RETURNING key'
            ),
            {
                "club": club,
                "series": series_id,
                "race_no": race_no,
                "started_at": started_at,
            },
        ).fetchone()
        keys.append(new_race.key)
    return keys


def main():
    args = parse_args()

    if args.race_count < 1:
        print("ERROR: --race-count must be >= 1")
        sys.exit(1)
    if args.spacing_minutes < 1:
        print("ERROR: --spacing-minutes must be >= 1")
        sys.exit(1)

    engine = create_engine(args.db_url)

    with engine.begin() as conn:
        series_id, club, series_name = find_series(conn, args.series_name)
        deleted_laps, deleted_entries, deleted_races = cleanup_races(
            conn, club, series_id, args.cleanup_scope
        )
        start_time = datetime.utcnow() + timedelta(days=args.days_ahead)
        new_race_keys = create_races(
            conn,
            club,
            series_id,
            args.race_count,
            start_time,
            args.spacing_minutes,
        )

    print(
        "SUCCESS"
        f" | series={series_name}"
        f" | club={club}"
        f" | series_id={series_id}"
        f" | cleanup_scope={args.cleanup_scope}"
        f" | deleted_laps={deleted_laps}"
        f" | deleted_entries={deleted_entries}"
        f" | deleted_races={deleted_races}"
        f" | new_race_keys={new_race_keys}"
    )


if __name__ == "__main__":
    main()
