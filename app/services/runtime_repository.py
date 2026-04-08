import json
from sqlalchemy import text


def get_role_id_by_code(conn, role_code):
    return conn.execute(
        text('SELECT key FROM "RACINGAPP"."ROLE" WHERE code = :code LIMIT 1'),
        {"code": role_code},
    ).scalar()


def upsert_club_user_role(conn, club_user_id, club_id, role_id, granted_by=None):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."CLUB_USER_ROLE" (key, club_user, club, role, granted_by, is_active)
            VALUES (nextval('key'), :club_user, :club, :role, :granted_by, TRUE)
            ON CONFLICT (club_user, club, role)
            DO UPDATE SET is_active = TRUE,
                          granted_by = COALESCE(EXCLUDED.granted_by, "RACINGAPP"."CLUB_USER_ROLE".granted_by),
                          granted_at = CURRENT_TIMESTAMP
        '''),
        {
            "club_user": club_user_id,
            "club": club_id,
            "role": role_id,
            "granted_by": granted_by,
        },
    )


def get_sailor_role_grant_key(conn, sailor_user_id, sailor_id, role_id):
    return conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."SAILOR_ROLE_GRANT"
            WHERE sailor_user = :sailor_user
              AND sailor = :sailor
              AND role = :role
            LIMIT 1
        '''),
        {
            "sailor_user": sailor_user_id,
            "sailor": sailor_id,
            "role": role_id,
        },
    ).scalar()


def update_sailor_role_grant(conn, key, club_id, granted_by=None, grant_reason=None):
    conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILOR_ROLE_GRANT"
            SET is_active = TRUE,
                club = :club,
                granted_by = COALESCE(:granted_by, granted_by),
                grant_reason = COALESCE(:grant_reason, grant_reason),
                granted_at = CURRENT_TIMESTAMP
            WHERE key = :key
        '''),
        {
            "key": key,
            "club": club_id,
            "granted_by": granted_by,
            "grant_reason": grant_reason,
        },
    )


def insert_sailor_role_grant(conn, sailor_user_id, sailor_id, club_id, role_id, granted_by=None, grant_reason=None):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SAILOR_ROLE_GRANT"
            (key, sailor_user, sailor, club, role, granted_by, grant_reason, is_active)
            VALUES (nextval('key'), :sailor_user, :sailor, :club, :role, :granted_by, :grant_reason, TRUE)
        '''),
        {
            "sailor_user": sailor_user_id,
            "sailor": sailor_id,
            "club": club_id,
            "role": role_id,
            "granted_by": granted_by,
            "grant_reason": grant_reason,
        },
    )


def resolve_sailor_club_id(conn, sailor_id):
    return conn.execute(
        text('''
            SELECT club
            FROM "RACINGAPP"."SAILORCONTROL"
            WHERE key = :sailor_id
            LIMIT 1
        '''),
        {"sailor_id": sailor_id},
    ).scalar()


def get_race_state_row(conn, race_id, club_id=None):
    return conn.execute(
        text('''
            SELECT key, club, series, status, results_status, results_locked_at, source_mode
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
              AND (:club_id IS NULL OR club = :club_id)
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id},
    ).mappings().first()


def get_race_snapshot_race(conn, race_id):
    return conn.execute(
        text('''
            SELECT key,
                   club,
                   series,
                   race_no,
                   status,
                   results_status,
                   source_mode,
                   started_at,
                   ended_at,
                   results_locked_at,
                   results_locked_by
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
            LIMIT 1
        '''),
        {"race_id": race_id},
    ).mappings().first()


def get_race_snapshot_entries(conn, race_id):
    return conn.execute(
        text('''
            SELECT re.key,
                   re.race_id,
                   re.boatkey,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   re.handicap,
                   re.created_by_user,
                   re.created_by_type,
                   re.source,
                   re.revision_id
            FROM "RACINGAPP"."RACE_ENTRY" re
            WHERE re.race_id = :race_id
            ORDER BY re.key
        '''),
        {"race_id": race_id},
    ).mappings().all()


def get_race_snapshot_laps(conn, race_id):
    return conn.execute(
        text('''
            SELECT l.key,
                   l.race_entry_id,
                   l.lap_number,
                   l.is_finish,
                   l.elapsed_sec,
                   l.corrected_sec,
                   l.position,
                   l.created_by_user,
                   l.created_by_type,
                   l.source,
                   l.revision_id
            FROM "RACINGAPP"."LAP" l
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.key = l.race_entry_id
            WHERE re.race_id = :race_id
            ORDER BY l.key
        '''),
        {"race_id": race_id},
    ).mappings().all()


def get_latest_race_revision_id(conn, race_id):
    return conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."RACE_RESULT_REVISION"
            WHERE race_id = :race_id
            ORDER BY revision_no DESC
            LIMIT 1
        '''),
        {"race_id": race_id},
    ).scalar()


def get_next_race_revision_no(conn, race_id):
    return conn.execute(
        text('''
            SELECT COALESCE(MAX(revision_no), 0) + 1
            FROM "RACINGAPP"."RACE_RESULT_REVISION"
            WHERE race_id = :race_id
        '''),
        {"race_id": race_id},
    ).scalar()


def insert_race_revision(conn, values):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_RESULT_REVISION" (
                key,
                race_id,
                revision_no,
                status,
                source_mode,
                reason,
                created_by_user,
                created_by_type,
                based_on_revision_id,
                snapshot_json
            )
            VALUES (
                nextval('key'),
                :race_id,
                :revision_no,
                :status,
                :source_mode,
                :reason,
                :created_by_user,
                :created_by_type,
                :based_on_revision_id,
                CAST(:snapshot_json AS JSONB)
            )
            RETURNING key
        '''),
        values,
    ).scalar()


def insert_race_audit(conn, values):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_RESULT_AUDIT" (
                key,
                race_id,
                revision_id,
                entity_type,
                entity_id,
                action,
                actor_type,
                actor_user_id,
                actor_sailor_id,
                reason,
                before_json,
                after_json
            )
            VALUES (
                nextval('key'),
                :race_id,
                :revision_id,
                :entity_type,
                :entity_id,
                :action,
                :actor_type,
                :actor_user_id,
                :actor_sailor_id,
                :reason,
                CAST(:before_json AS JSONB),
                CAST(:after_json AS JSONB)
            )
        '''),
        values,
    )


def upsert_race_duty_assignment_row(conn, values):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (
                key,
                race_id,
                sailor,
                sailor_user,
                role,
                duty_type,
                starts_at,
                ends_at,
                status,
                assigned_by,
                notes
            )
            VALUES (
                nextval('key'),
                :race_id,
                :sailor,
                :sailor_user,
                :role,
                :duty_type,
                :starts_at,
                :ends_at,
                :status,
                :assigned_by,
                :notes
            )
            ON CONFLICT (race_id, sailor, role)
            DO UPDATE SET
                sailor_user = EXCLUDED.sailor_user,
                duty_type = EXCLUDED.duty_type,
                starts_at = EXCLUDED.starts_at,
                ends_at = EXCLUDED.ends_at,
                status = EXCLUDED.status,
                assigned_by = EXCLUDED.assigned_by,
                notes = EXCLUDED.notes
            RETURNING key
        '''),
        values,
    ).scalar()


def get_upcoming_races_for_club(conn, club_id):
    return conn.execute(
        text('''
            WITH ranked AS (
                SELECT r.key AS race_id,
                       r.series AS series_id,
                       r.race_no,
                       r.started_at,
                       r.status,
                       sc.name AS series_name,
                       ROW_NUMBER() OVER (
                           PARTITION BY r.series
                           ORDER BY r.started_at ASC, r.key ASC
                       ) AS rn
                FROM "RACINGAPP"."RACE" r
                JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                WHERE r.club = :club_id
                  AND r.status = 'not_started'
                  AND r.started_at IS NOT NULL
                  AND r.started_at >= NOW()
            )
            SELECT race_id, series_id, race_no, started_at, status, series_name
            FROM ranked
            WHERE rn = 1
            ORDER BY started_at ASC, race_id ASC
        '''),
        {"club_id": club_id},
    ).mappings().all()


def race_exists_for_club(conn, race_id, club_id):
    return conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id},
    ).scalar()


def get_race_entries_for_race(conn, race_id):
    return conn.execute(
        text('''
            SELECT re.boatkey AS key,
                   re.sailor,
                   re.boat,
                   re.sail_number AS "sailNumber",
                   re.handicap
            FROM "RACINGAPP"."RACE_ENTRY" re
            WHERE re.race_id = :race_id
            ORDER BY re.key ASC
        '''),
        {"race_id": race_id},
    ).mappings().all()
