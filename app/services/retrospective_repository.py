from sqlalchemy import text


def check_series_for_club(conn, series_id, club_id):
    """Return 1 if series belongs to club, else None."""
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


def get_next_race_no(conn, series_id):
    """Return MAX(race_no) + 1 for a series (min 1)."""
    return conn.execute(
        text('SELECT COALESCE(MAX(race_no), 0) + 1 FROM "RACINGAPP"."RACE" WHERE series = :series_id'),
        {"series_id": series_id}
    ).scalar()


def insert_retrospective_race(conn, values):
    """INSERT a retrospective RACE row and return the new key."""
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE" (
                club, series, race_no, status, started_at, ended_at,
                source_mode, results_status
            )
            VALUES (
                :club_id, :series_id, :race_no,
                'finished', :started_at, :ended_at,
                'retrospective', 'draft'
            )
            RETURNING key
        '''),
        values
    ).scalar()


def list_retrospective_races(conn, club_id, series_id, from_date, to_date):
    """Return all races for a club, optionally filtered by series and date range."""
    return conn.execute(
        text('''
            SELECT r.key AS race_id,
                   r.series AS series_id,
                   sc.name AS series_name,
                   r.race_no,
                   r.status,
                   r.results_status,
                   r.source_mode,
                   r.started_at,
                   r.ended_at,
                   r.results_locked_at,
                   CASE WHEN r.results_status = 'locked' OR r.results_locked_at IS NOT NULL
                        THEN TRUE ELSE FALSE END AS is_locked
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id
              AND (:series_id IS NULL OR r.series = :series_id)
              AND (
                  :from_date IS NULL OR DATE(COALESCE(r.started_at, r.ended_at, CURRENT_TIMESTAMP)) >= :from_date
              )
              AND (
                  :to_date IS NULL OR DATE(COALESCE(r.started_at, r.ended_at, CURRENT_TIMESTAMP)) <= :to_date
              )
            ORDER BY COALESCE(r.started_at, r.ended_at) DESC NULLS LAST, r.key DESC
        '''),
        {
            "club_id": club_id,
            "series_id": series_id,
            "from_date": from_date,
            "to_date": to_date,
        }
    ).mappings().all()


def get_race_for_preview(conn, race_id, club_id):
    """Return race metadata for the retrospective preview endpoint."""
    return conn.execute(
        text('''
            SELECT r.key,
                   r.race_no,
                   r.status,
                   r.results_status,
                   r.source_mode,
                   r.started_at,
                   r.ended_at,
                   cc.name AS club_name,
                   sc.name AS series_name
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = r.club
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.key = :race_id
              AND r.club = :club_id
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()


def get_preview_entries(conn, race_id):
    """Return entries with aggregated finish data for the preview."""
    return conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   re.handicap,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END)   AS elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec,
                   MAX(CASE WHEN l.is_finish THEN l.position END)      AS position
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number, re.handicap
            ORDER BY
                MAX(CASE WHEN l.is_finish THEN l.position END)      ASC NULLS LAST,
                MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) ASC NULLS LAST,
                re.key ASC
        '''),
        {"race_id": race_id}
    ).mappings().all()


def set_race_to_draft(conn, race_id, club_id):
    """Mark a race as finished/retrospective/draft (used when saving a draft)."""
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET status = 'finished',
                source_mode = 'retrospective',
                results_status = 'draft',
                ended_at = COALESCE(ended_at, CURRENT_TIMESTAMP)
            WHERE key = :race_id
              AND club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    )


def delete_all_entry_laps(conn, race_id):
    """Delete all laps for every entry in a race (used by replace_existing)."""
    conn.execute(
        text('''
            DELETE FROM "RACINGAPP"."LAP"
            WHERE race_entry_id IN (
                SELECT key FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id
            )
        '''),
        {"race_id": race_id}
    )


def delete_all_entries(conn, race_id):
    """Delete all entries for a race (used by replace_existing)."""
    conn.execute(
        text('DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id'),
        {"race_id": race_id}
    )


def resolve_boatkey(conn, club_id, sailor, sail_number):
    """Resolve boatkey for a retrospective entry; returns None if not found."""
    return conn.execute(
        text('''
            SELECT bc.key
            FROM "RACINGAPP"."BOATCONTROL" bc
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            WHERE sc.club = :club_id
              AND sc.fullname = :sailor
              AND bc.sail_number = :sail_number
            ORDER BY bc.key DESC
            LIMIT 1
        '''),
        {"club_id": club_id, "sailor": sailor, "sail_number": sail_number}
    ).scalar()


def insert_retrospective_entry(conn, values):
    """INSERT a RACE_ENTRY row for a retrospective race and return new key."""
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_ENTRY" (
                race_id, boatkey, sailor, boat, sail_number, handicap,
                created_by_user, created_by_type, source, revision_id
            )
            VALUES (
                :race_id, :boatkey, :sailor, :boat, :sail_number, :handicap,
                :created_by_user, :created_by_type, 'retrospective', :revision_id
            )
            RETURNING key
        '''),
        values
    ).scalar()


def insert_retrospective_lap(conn, values):
    """INSERT a finish LAP row for a retrospective entry."""
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."LAP" (
                race_entry_id, lap_number, is_finish, elapsed_sec, corrected_sec,
                position, created_by_user, created_by_type, source, revision_id
            )
            VALUES (
                :race_entry_id, :lap_number, TRUE, :elapsed_sec, :corrected_sec,
                :position, :created_by_user, :created_by_type, 'retrospective', :revision_id
            )
        '''),
        values
    )


def publish_race_results(conn, race_id, club_id):
    """Mark a race's results as published."""
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET status = 'finished',
                source_mode = CASE WHEN source_mode IS NULL THEN 'retrospective' ELSE source_mode END,
                results_status = 'published',
                ended_at = COALESCE(ended_at, CURRENT_TIMESTAMP)
            WHERE key = :race_id
              AND club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    )
