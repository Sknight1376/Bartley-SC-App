from datetime import date, datetime, timedelta

from sqlalchemy import text


def fetch_series_rules(conn, series_id):
    return conn.execute(
        text('''
            SELECT key, weekday, start_time, cadence_weeks, races_per_day,
                   target_race_count, extra_start_times, valid_from, valid_to, is_active
            FROM "RACINGAPP"."SERIES_RULE"
            WHERE series = :series_id
            ORDER BY valid_from ASC, weekday ASC, start_time ASC, key ASC
        '''),
        {"series_id": series_id}
    ).mappings().all()


def set_series_year(conn, series_id, club_id, year):
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."SERIESCONTROL"
            SET year = :year
            WHERE key = :series_id
              AND club = :club_id
        '''),
        {"year": str(year), "series_id": series_id, "club_id": club_id}
    )


def insert_series_rule(conn, series_id, values):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SERIES_RULE"
                (key, series, weekday, start_time, cadence_weeks, races_per_day,
                 target_race_count, extra_start_times, valid_from, valid_to, is_active)
            VALUES
                (nextval('key'), :series, :weekday, :start_time, :cadence_weeks, :races_per_day,
                 :target_race_count, :extra_start_times, :valid_from, :valid_to, :is_active)
            RETURNING key
        '''),
        {
            "series": series_id,
            "weekday": values["weekday"],
            "start_time": values["start_time"],
            "cadence_weeks": values["cadence_weeks"],
            "races_per_day": values["races_per_day"],
            "target_race_count": values["target_race_count"],
            "extra_start_times": values["extra_start_times"],
            "valid_from": values["valid_from"],
            "valid_to": values["valid_to"],
            "is_active": values["is_active"],
        }
    ).scalar()


def find_series_by_name_year(conn, club_id, name, year):
    return conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE club = :club_id
              AND LOWER(name) = LOWER(:name)
              AND year = :year
            LIMIT 1
        '''),
        {"club_id": club_id, "name": name, "year": year}
    ).scalar()


def insert_series(conn, year, name, club_id):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SERIESCONTROL" (key, year, name, club)
            VALUES (nextval('key'), :year, :name, :club)
            RETURNING key
        '''),
        {"year": year, "name": name, "club": club_id}
    ).scalar()


def list_series_manage_rows(conn, club_id):
    return conn.execute(
        text('''
            SELECT s.key,
                   s.year,
                   s.name,
                   COALESCE(sr.rule_count, 0) AS rule_count,
                   COALESCE(ss.discard_rule_count, 0) AS discard_rule_count,
                   COALESCE(r.total_races, 0) AS total_races,
                   r.next_race_at,
                   r.last_race_at
            FROM "RACINGAPP"."SERIESCONTROL" s
            LEFT JOIN (
                SELECT series,
                       COUNT(*) FILTER (WHERE COALESCE(is_active, TRUE)) AS rule_count
                FROM "RACINGAPP"."SERIES_RULE"
                GROUP BY series
            ) sr ON sr.series = s.key
            LEFT JOIN (
                SELECT series,
                       COUNT(*) AS discard_rule_count
                FROM "RACINGAPP"."SERIES_SCORING_DISCARD"
                GROUP BY series
            ) ss ON ss.series = s.key
            LEFT JOIN (
                SELECT series,
                       COUNT(*) AS total_races,
                       MIN(started_at) FILTER (WHERE started_at >= NOW()) AS next_race_at,
                       MAX(started_at) AS last_race_at
                FROM "RACINGAPP"."RACE"
                GROUP BY series
            ) r ON r.series = s.key
            WHERE s.club = :club_id
            ORDER BY s.year DESC NULLS LAST, s.name ASC
        '''),
        {"club_id": club_id}
    ).mappings().all()


def get_series_by_id(conn, series_id, club_id):
    return conn.execute(
        text('''
            SELECT key, year, name
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE key = :series_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"series_id": series_id, "club_id": club_id}
    ).mappings().first()


def get_series_year(conn, series_id, club_id):
    return conn.execute(
        text('''
            SELECT year
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE key = :series_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"series_id": series_id, "club_id": club_id}
    ).scalar()


def update_series(conn, series_id, club_id, year, name):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SERIESCONTROL"
            SET year = :year,
                name = :name
            WHERE key = :series_id
              AND club = :club_id
        '''),
        {"series_id": series_id, "club_id": club_id, "year": year, "name": name}
    )


def get_max_race_no_for_series(conn, series_id):
    return conn.execute(
        text('SELECT COALESCE(MAX(race_no), 0) FROM "RACINGAPP"."RACE" WHERE series = :series_id'),
        {"series_id": series_id}
    ).scalar() or 0


def insert_race(conn, club_id, series_id, race_no, started_at):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE" (key, club, series, race_no, status, started_at, ended_at)
            VALUES (nextval('key'), :club, :series, :race_no, 'not_started', :started_at, NULL)
        '''),
        {"club": club_id, "series": series_id, "race_no": race_no, "started_at": started_at}
    )


def update_series_rule(conn, rule_id, series_id, values):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SERIES_RULE"
            SET weekday = :weekday,
                start_time = :start_time,
                cadence_weeks = :cadence_weeks,
                races_per_day = :races_per_day,
                target_race_count = :target_race_count,
                extra_start_times = :extra_start_times,
                valid_from = :valid_from,
                valid_to = :valid_to,
                is_active = :is_active
            WHERE key = :rule_id
              AND series = :series_id
        '''),
        {
            "rule_id": rule_id,
            "series_id": series_id,
            "weekday": values["weekday"],
            "start_time": values["start_time"],
            "cadence_weeks": values["cadence_weeks"],
            "races_per_day": values["races_per_day"],
            "target_race_count": values["target_race_count"],
            "extra_start_times": values["extra_start_times"],
            "valid_from": values["valid_from"],
            "valid_to": values["valid_to"],
            "is_active": values["is_active"],
        }
    )


def delete_series_rule(conn, rule_id, series_id):
    return conn.execute(
        text('''
            DELETE FROM "RACINGAPP"."SERIES_RULE"
            WHERE key = :rule_id
              AND series = :series_id
        '''),
        {"rule_id": rule_id, "series_id": series_id}
    )


def list_series_exceptions(conn, series_id):
    return conn.execute(
        text('''
            SELECT key, COALESCE(exception_date, DATE(original_start_at)) AS exception_date, note, is_active
            FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE series = :series_id
              AND exception_type = 'cancel'
            ORDER BY COALESCE(exception_date, DATE(original_start_at)) ASC, key ASC
        '''),
        {"series_id": series_id}
    ).mappings().all()


def insert_series_exception(conn, series_id, exception_date, original_start_at, note, is_active):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SERIES_EXCEPTION"
                (key, series, exception_type, exception_date, original_start_at, override_start_at, note, is_active)
            VALUES
                (nextval('key'), :series, 'cancel', :exception_date, :original_start_at, NULL, :note, :is_active)
            RETURNING key
        '''),
        {
            "series": series_id,
            "exception_date": exception_date,
            "original_start_at": original_start_at,
            "note": note,
            "is_active": is_active,
        }
    ).scalar()


def update_series_exception(conn, exception_id, series_id, exception_date, original_start_at, note, is_active):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SERIES_EXCEPTION"
            SET exception_date = :exception_date,
                original_start_at = :original_start_at,
                note = :note,
                is_active = :is_active
            WHERE key = :exception_id
              AND series = :series_id
              AND exception_type = 'cancel'
        '''),
        {
            "exception_id": exception_id,
            "series_id": series_id,
            "exception_date": exception_date,
            "original_start_at": original_start_at,
            "note": note,
            "is_active": is_active,
        }
    )


def delete_series_exception(conn, exception_id, series_id):
    return conn.execute(
        text('''
            DELETE FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE key = :exception_id
              AND series = :series_id
              AND exception_type = 'cancel'
        '''),
        {"exception_id": exception_id, "series_id": series_id}
    )


def get_series_scoring(conn, series_id):
    return conn.execute(
        text('''
            SELECT scoring_system, races_to_count, discard_after_races, discards_allowed
            FROM "RACINGAPP"."SERIES_SCORING"
            WHERE series = :series
        '''),
        {"series": series_id}
    ).mappings().first()


def list_series_scoring_discard_rules(conn, series_id):
    return conn.execute(
        text('''
            SELECT discard_count, after_races
            FROM "RACINGAPP"."SERIES_SCORING_DISCARD"
            WHERE series = :series
            ORDER BY discard_count ASC
        '''),
        {"series": series_id}
    ).mappings().all()


def upsert_series_scoring_low_point(conn, series_id):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SERIES_SCORING"
                (series, scoring_system, races_to_count, discard_after_races, discards_allowed, updated_at)
            VALUES
                (:series, 'low_point', NULL, NULL, 0, CURRENT_TIMESTAMP)
            ON CONFLICT (series)
            DO UPDATE SET
                scoring_system = 'low_point',
                races_to_count = NULL,
                discard_after_races = NULL,
                discards_allowed = 0,
                updated_at = CURRENT_TIMESTAMP
        '''),
        {"series": series_id}
    )


def delete_series_scoring_discard_rules(conn, series_id):
    conn.execute(
        text('DELETE FROM "RACINGAPP"."SERIES_SCORING_DISCARD" WHERE series = :series'),
        {"series": series_id}
    )


def insert_series_scoring_discard_rule(conn, series_id, discard_count, after_races):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SERIES_SCORING_DISCARD"
                (key, series, discard_count, after_races, created_at, updated_at)
            VALUES
                (nextval('key'), :series, :discard_count, :after_races, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        '''),
        {"series": series_id, "discard_count": discard_count, "after_races": after_races}
    )


def list_series_races(conn, series_id):
    return conn.execute(
        text('''
            SELECT key, race_no, status, started_at
            FROM "RACINGAPP"."RACE"
            WHERE series = :series_id
            ORDER BY started_at ASC, race_no ASC
        '''),
        {"series_id": series_id}
    ).mappings().all()


def ensure_series_schedule_tables(conn):
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_RULE" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
            start_time TIME NOT NULL,
            cadence_weeks INTEGER NOT NULL DEFAULT 1 CHECK (cadence_weeks > 0),
            races_per_day INTEGER NOT NULL DEFAULT 1 CHECK (races_per_day > 0),
            target_race_count INTEGER NULL,
            extra_start_times TEXT NULL,
            slot_gap_minutes INTEGER NOT NULL DEFAULT 10 CHECK (slot_gap_minutes > 0),
            valid_from DATE NOT NULL,
            valid_to DATE NULL,
            anchor_date DATE NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_EXCEPTION" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            exception_type VARCHAR(16) NOT NULL CHECK (exception_type IN ('cancel', 'move', 'add')),
            exception_date DATE NULL,
            original_start_at TIMESTAMP NULL,
            override_start_at TIMESTAMP NULL,
            note TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_SCORING" (
            series BIGINT PRIMARY KEY REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            scoring_system VARCHAR(32) NOT NULL DEFAULT 'low_point',
            races_to_count INTEGER NULL,
            discard_after_races INTEGER NULL,
            discards_allowed INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_SCORING_DISCARD" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            discard_count INTEGER NOT NULL CHECK (discard_count > 0),
            after_races INTEGER NOT NULL CHECK (after_races > 0),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series, discard_count)
        )
    '''))

    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_RULE"
        ADD COLUMN IF NOT EXISTS extra_start_times TEXT NULL
    '''))
    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_RULE"
        ADD COLUMN IF NOT EXISTS target_race_count INTEGER NULL
    '''))
    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_EXCEPTION"
        ADD COLUMN IF NOT EXISTS exception_date DATE NULL
    '''))

    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_rule_series
            ON "RACINGAPP"."SERIES_RULE" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_exception_series
            ON "RACINGAPP"."SERIES_EXCEPTION" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_scoring_discard_series
            ON "RACINGAPP"."SERIES_SCORING_DISCARD" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_race_series_started
            ON "RACINGAPP"."RACE" (series, started_at)
    '''))


def check_series_access(conn, series_id, club_id):
    return conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE key = :series_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"series_id": series_id, "club_id": club_id}
    ).scalar()


def recompute_series_rule_end_dates(conn, series_id):
    rules = conn.execute(
        text('''
            SELECT key, weekday, cadence_weeks, races_per_day, target_race_count, valid_from
            FROM "RACINGAPP"."SERIES_RULE"
            WHERE series = :series_id
              AND is_active = TRUE
              AND target_race_count IS NOT NULL
              AND target_race_count > 0
        '''),
        {"series_id": series_id}
    ).mappings().all()

    exception_rows = conn.execute(
        text('''
            SELECT COALESCE(exception_date, DATE(original_start_at)) AS exception_date
            FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE series = :series_id
              AND is_active = TRUE
              AND exception_type = 'cancel'
        '''),
        {"series_id": series_id}
    ).mappings().all()

    excluded_dates = [r["exception_date"] for r in exception_rows if r.get("exception_date")]

    def _calculate_rule_end_date_with_exceptions(valid_from, weekday, cadence_weeks, races_per_day, target_race_count, excluded):
        if target_race_count is None or target_race_count <= 0:
            return None

        excluded_set = set(excluded or [])
        days_to_add = (weekday - valid_from.weekday()) % 7
        current = valid_from + timedelta(days=days_to_add)
        remaining = int(target_race_count)

        while True:
            if current not in excluded_set:
                remaining -= min(races_per_day, remaining)
                if remaining <= 0:
                    return current
            current = current + timedelta(days=7 * cadence_weeks)

    for rule in rules:
        new_valid_to = _calculate_rule_end_date_with_exceptions(
            valid_from=rule["valid_from"],
            weekday=int(rule["weekday"]),
            cadence_weeks=int(rule["cadence_weeks"]),
            races_per_day=int(rule["races_per_day"]),
            target_race_count=int(rule["target_race_count"]),
            excluded=excluded_dates,
        )
        if new_valid_to:
            conn.execute(
                text('''
                    UPDATE "RACINGAPP"."SERIES_RULE"
                    SET valid_to = :valid_to,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE key = :rule_id
                '''),
                {"valid_to": new_valid_to, "rule_id": rule["key"]}
            )


def generate_series_races(conn, series_id, club_id, from_date, to_date):
    ensure_series_schedule_tables(conn)

    rules = conn.execute(
        text('''
             SELECT key, weekday, start_time, cadence_weeks, races_per_day,
                 extra_start_times, slot_gap_minutes, valid_from, valid_to
            FROM "RACINGAPP"."SERIES_RULE"
            WHERE series = :series_id
              AND is_active = TRUE
              AND valid_from <= :to_date
              AND (valid_to IS NULL OR valid_to >= :from_date)
            ORDER BY key ASC
        '''),
        {"series_id": series_id, "from_date": from_date, "to_date": to_date}
    ).mappings().all()

    exceptions = conn.execute(
        text('''
            SELECT exception_type, exception_date, original_start_at
            FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE series = :series_id
              AND is_active = TRUE
            ORDER BY key ASC
        '''),
        {"series_id": series_id}
    ).mappings().all()

    planned = {}

    for rule in rules:
        weekday = int(rule["weekday"])
        cadence = int(rule["cadence_weeks"])
        races_per_day = int(rule["races_per_day"])
        start_time = rule["start_time"]
        cadence_anchor = rule["valid_from"]
        rule_start = max(rule["valid_from"], from_date)
        rule_end = min(rule["valid_to"] or to_date, to_date)
        extra_start_times = [s.strip() for s in (rule.get("extra_start_times") or "").split(",") if s and s.strip()]
        slot_gap = int(rule["slot_gap_minutes"])

        day_start_times = [start_time]
        if races_per_day > 1:
            if len(extra_start_times) >= races_per_day - 1:
                day_start_times.extend([
                    datetime.strptime(t, "%H:%M").time()
                    for t in extra_start_times[:races_per_day - 1]
                ])
            else:
                day_start_times.extend([
                    (datetime.combine(date.today(), start_time) + timedelta(minutes=slot_gap * slot)).time()
                    for slot in range(1, races_per_day)
                ])

        if rule_start > rule_end:
            continue

        first = rule_start + timedelta(days=(weekday - rule_start.weekday()) % 7)
        while ((first - cadence_anchor).days // 7) % cadence != 0:
            first = first + timedelta(days=7)

        current = first
        while current <= rule_end:
            for slot in range(races_per_day):
                started_at = datetime.combine(current, day_start_times[slot])
                planned[started_at] = True
            current = current + timedelta(days=7 * cadence)

    excluded_dates = set()
    for ex in exceptions:
        ex_date = ex["exception_date"]
        if not ex_date and ex.get("exception_type") == "cancel" and ex.get("original_start_at"):
            ex_date = ex["original_start_at"].date()
        if ex_date and from_date <= ex_date <= to_date:
            excluded_dates.add(ex_date)

    if excluded_dates:
        for dt_key in list(planned.keys()):
            if dt_key.date() in excluded_dates:
                planned.pop(dt_key, None)

    max_race_no = conn.execute(
        text('SELECT COALESCE(MAX(race_no), 0) FROM "RACINGAPP"."RACE" WHERE series = :series_id'),
        {"series_id": series_id}
    ).scalar() or 0

    inserted = 0
    skipped = 0
    for started_at in sorted(planned.keys()):
        exists = conn.execute(
            text('''
                SELECT 1
                FROM "RACINGAPP"."RACE"
                WHERE series = :series_id
                  AND started_at = :started_at
                LIMIT 1
            '''),
            {"series_id": series_id, "started_at": started_at}
        ).scalar()
        if exists:
            skipped += 1
            continue

        max_race_no += 1
        conn.execute(
            text('''
                INSERT INTO "RACINGAPP"."RACE" (key, club, series, race_no, status, started_at, ended_at)
                VALUES (nextval('key'), :club, :series, :race_no, 'not_started', :started_at, NULL)
            '''),
            {"club": club_id, "series": series_id, "race_no": max_race_no, "started_at": started_at}
        )
        inserted += 1

    return {
        "rule_count": len(rules),
        "planned_count": len(planned),
        "inserted_count": inserted,
        "skipped_count": skipped,
    }
