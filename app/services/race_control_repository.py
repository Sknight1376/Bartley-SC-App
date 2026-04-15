from sqlalchemy import text


def get_race_for_club(conn, race_id, club_id):
    return conn.execute(
        text('''
            SELECT key, status, results_status, results_locked_at, source_mode
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()


def set_race_active(conn, race_id, source_mode):
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET status = 'active',
                source_mode = :source_mode,
                results_status = CASE WHEN results_status = 'locked' THEN results_status ELSE 'draft' END,
                started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
            WHERE key = :race_id
        '''),
        {"race_id": race_id, "source_mode": source_mode}
    )


def race_entry_exists(conn, entry_id, race_id):
    return bool(conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" WHERE key = :entry_id AND race_id = :race_id'),
        {"entry_id": entry_id, "race_id": race_id}
    ).scalar())


def insert_lap(conn, values):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."LAP" (
                race_entry_id,
                lap_number,
                is_finish,
                elapsed_sec,
                corrected_sec,
                position,
                created_by_user,
                created_by_type,
                source,
                revision_id
            )
            VALUES (
                :race_entry_id,
                :lap_number,
                :is_finish,
                :elapsed_sec,
                :corrected_sec,
                :position,
                :created_by_user,
                :created_by_type,
                :source,
                :revision_id
            )
        '''),
        values
    )


def finish_race(conn, race_id, club_id):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET status = :status,
                results_status = 'published',
                ended_at = CURRENT_TIMESTAMP
            WHERE key = :race_id
              AND club = :club_id
        '''),
        {"status": "finished", "race_id": race_id, "club_id": club_id}
    )


def lock_race_results(conn, race_id, club_id, locked_by):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET results_status = 'locked',
                results_locked_at = CURRENT_TIMESTAMP,
                results_locked_by = :locked_by
            WHERE key = :race_id
              AND club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id, "locked_by": locked_by}
    )


def unlock_race_results(conn, race_id, club_id):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."RACE"
            SET results_status = 'published',
                results_locked_at = NULL,
                results_locked_by = NULL
            WHERE key = :race_id
              AND club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    )


# ---------------------------------------------------------------------------
# Race entry helpers
# ---------------------------------------------------------------------------

def resolve_boatkey(conn, club_id, sailor, sail_number):
    """Return the best-match boatkey for a sailor+sail_number within a club, or None."""
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


def insert_race_entry(conn, values):
    """INSERT a RACE_ENTRY row and return the new key."""
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_ENTRY" (
                race_id, boatkey, sailor, boat, sail_number, handicap,
                created_by_user, created_by_type, source, revision_id
            )
            VALUES (
                :race_id, :boatkey, :sailor, :boat, :sail_number, :handicap,
                :created_by_user, :created_by_type, :source, :revision_id
            )
            RETURNING key
        '''),
        values
    ).scalar()


def get_entry_for_race(conn, entry_id, race_id):
    """Return a single entry row (key, sailor, boat, sail_number, handicap) or None."""
    return conn.execute(
        text('''
            SELECT key, sailor, boat, sail_number, handicap
            FROM "RACINGAPP"."RACE_ENTRY"
            WHERE key = :entry_id
              AND race_id = :race_id
            LIMIT 1
        '''),
        {"entry_id": entry_id, "race_id": race_id}
    ).mappings().first()


def list_race_entries(conn, race_id):
    """Return race entries with stable DB entry keys for control resume flows."""
    return conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   re.handicap,
                   re.boatkey
            FROM "RACINGAPP"."RACE_ENTRY" re
            WHERE re.race_id = :race_id
            ORDER BY re.key ASC
        '''),
        {"race_id": race_id}
    ).mappings().all()


def get_lap_count_for_entry(conn, entry_id):
    """Return the number of laps recorded for an entry."""
    return conn.execute(
        text('SELECT COUNT(*) FROM "RACINGAPP"."LAP" WHERE race_entry_id = :entry_id'),
        {"entry_id": entry_id}
    ).scalar()


def delete_entry_laps(conn, entry_id):
    """Delete all laps for a race entry."""
    conn.execute(
        text('DELETE FROM "RACINGAPP"."LAP" WHERE race_entry_id = :entry_id'),
        {"entry_id": entry_id}
    )


def delete_entry(conn, entry_id, race_id):
    """Delete a single race entry."""
    conn.execute(
        text('DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE key = :entry_id AND race_id = :race_id'),
        {"entry_id": entry_id, "race_id": race_id}
    )


# ---------------------------------------------------------------------------
# Lap helpers
# ---------------------------------------------------------------------------

def get_lap_for_race(conn, lap_id, race_id):
    """Return a single lap row joined to its entry (to verify race ownership), or None."""
    return conn.execute(
        text('''
            SELECT l.key,
                   l.race_entry_id,
                   l.lap_number,
                   l.is_finish,
                   l.elapsed_sec,
                   l.corrected_sec,
                   l.position
            FROM "RACINGAPP"."LAP" l
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.key = l.race_entry_id
            WHERE l.key = :lap_id
              AND re.race_id = :race_id
            LIMIT 1
        '''),
        {"lap_id": lap_id, "race_id": race_id}
    ).mappings().first()


def update_lap(conn, lap_id, values):
    """Update mutable fields on a lap row."""
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."LAP"
            SET lap_number        = :lap_number,
                is_finish         = :is_finish,
                elapsed_sec       = :elapsed_sec,
                corrected_sec     = :corrected_sec,
                position          = :position,
                created_by_user   = :created_by_user,
                created_by_type   = :created_by_type,
                revision_id       = :revision_id
            WHERE key = :lap_id
        '''),
        {**values, "lap_id": lap_id}
    )


def delete_lap(conn, lap_id):
    """Delete a single lap row."""
    conn.execute(
        text('DELETE FROM "RACINGAPP"."LAP" WHERE key = :lap_id'),
        {"lap_id": lap_id}
    )


def get_selected_race_for_start(conn, race_id, club_id, series_id):
    return conn.execute(
        text('''
            SELECT key, race_no, status, results_status, results_locked_at
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
              AND club = :club_id
              AND series = :series_id
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id, "series_id": series_id}
    ).mappings().first()


def clear_race_entries_for_race(conn, race_id):
    conn.execute(
        text('DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id'),
        {"race_id": race_id}
    )


def get_next_race_no_for_series(conn, series_id):
    return conn.execute(
        text('SELECT COALESCE(MAX(race_no), 0) + 1 FROM "RACINGAPP"."RACE" WHERE series = :series'),
        {"series": series_id}
    ).scalar()


def insert_race_start_row(conn, club_id, series_id, race_no, source_mode):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at, source_mode, results_status)
            VALUES (:club, :series, :race_no, :status, CURRENT_TIMESTAMP, :source_mode, 'draft')
            RETURNING key
        '''),
        {
            "club": club_id,
            "series": series_id,
            "race_no": race_no,
            "status": "active",
            "source_mode": source_mode,
        }
    ).scalar()


def resolve_boatkey_for_start(conn, sailor, sail_number, club_id=None):
    return conn.execute(
        text('''
            SELECT bc.key
            FROM "RACINGAPP"."BOATCONTROL" bc
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            WHERE sc.fullname = :sailor
              AND bc.sail_number = :sail_number
              AND (:club_id IS NULL OR sc.club = :club_id)
            ORDER BY bc.key DESC
            LIMIT 1
        '''),
        {"sailor": sailor, "sail_number": sail_number, "club_id": club_id}
    ).scalar()


def get_race_summary_header(conn, race_id, club_id):
    return conn.execute(
        text('''
            SELECT r.race_no, r.started_at, r.ended_at, r.status,
                   cc.name AS club_name, sc.name AS series_name
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."CLUBCONTROL" cc ON r.club = cc.key
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON r.series = sc.key
            WHERE r.key = :race_id
              AND r.club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()


def get_race_summary_results(conn, race_id):
    return conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor, re.boat, re.sail_number, re.handicap,
                   COALESCE(MAX(l.lap_number), COUNT(l.key), 0) AS lap_count,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS final_elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS final_corrected_sec,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS final_position
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number, re.handicap
            ORDER BY CASE
                       WHEN COALESCE(MAX(l.lap_number), COUNT(l.key), 0) > 0
                       THEN ROUND(MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)::numeric / COALESCE(MAX(l.lap_number), COUNT(l.key), 0), 0)
                       ELSE MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)
                     END ASC NULLS LAST,
                     CASE
                       WHEN COALESCE(MAX(l.lap_number), COUNT(l.key), 0) > 0
                       THEN ROUND(MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END)::numeric / COALESCE(MAX(l.lap_number), COUNT(l.key), 0), 0)
                       ELSE MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END)
                     END ASC NULLS LAST,
                     re.key ASC
        '''),
        {"race_id": race_id}
    ).mappings().all()
