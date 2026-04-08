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
                   COALESCE(r.total_races, 0) AS total_races,
                   r.next_race_at,
                   r.last_race_at
            FROM "RACINGAPP"."SERIESCONTROL" s
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
