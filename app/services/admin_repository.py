from sqlalchemy import text


def check_db_health(conn):
    conn.execute(text("SELECT 1"))
    return True


def get_race_audit_rows(conn, race_id):
    """Return up to 500 audit entries for a race, newest first."""
    return conn.execute(
        text('''
            SELECT key,
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
                   after_json,
                   created_at
            FROM "RACINGAPP"."RACE_RESULT_AUDIT"
            WHERE race_id = :race_id
            ORDER BY key DESC
            LIMIT 500
        '''),
        {"race_id": race_id}
    ).mappings().all()


def get_race_revision_rows(conn, race_id):
    """Return up to 250 revisions for a race, newest first."""
    return conn.execute(
        text('''
            SELECT key,
                   race_id,
                   revision_no,
                   status,
                   source_mode,
                   reason,
                   created_at,
                   created_by_user,
                   created_by_type,
                   based_on_revision_id,
                   snapshot_json
            FROM "RACINGAPP"."RACE_RESULT_REVISION"
            WHERE race_id = :race_id
            ORDER BY revision_no DESC
            LIMIT 250
        '''),
        {"race_id": race_id}
    ).mappings().all()


def authenticate_club_user(conn, username, password):
    return conn.execute(
        text('''
            SELECT cu.key AS user_id,
                   cu.username,
                   cc.key AS club_id,
                   cc.name AS club_name
            FROM "RACINGAPP"."CLUBUSER" cu
            JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = cu.club
            WHERE LOWER(cu.username) = LOWER(:username)
              AND cu.is_active = TRUE
              AND cu.password_hash = crypt(:password, cu.password_hash)
            LIMIT 1
        '''),
        {"username": username, "password": password}
    ).mappings().first()


def update_club_user_last_login(conn, user_id):
    conn.execute(
        text('UPDATE "RACINGAPP"."CLUBUSER" SET last_login = CURRENT_TIMESTAMP WHERE key = :user_id'),
        {"user_id": user_id}
    )


def get_club_id_by_name(conn, name):
    return conn.execute(
        text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = :name LIMIT 1'),
        {"name": name}
    ).scalar()


def get_series_id_by_name(conn, name):
    return conn.execute(
        text('SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = :name LIMIT 1'),
        {"name": name}
    ).scalar()


def get_test_race_seed_entries(conn, club_id):
    if not club_id:
        return []
    return conn.execute(
        text('''
            SELECT bc.key AS boatkey,
                   sc.fullname AS sailor,
                   hc.boat AS boat,
                   bc.sail_number AS sail_number,
                   hc.handicap AS handicap
            FROM "RACINGAPP"."BOATCONTROL" bc
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
            WHERE sc.club = :club_id
            ORDER BY sc.fullname
            LIMIT 3
        '''),
        {"club_id": club_id}
    ).mappings().all()

