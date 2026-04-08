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
