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

