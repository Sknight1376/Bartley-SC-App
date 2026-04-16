from sqlalchemy import text


def get_race_duties(conn, race_id):
    """Return all duty assignments for a race."""
    return conn.execute(
        text('''
            SELECT rda.key,
                   rda.race_id,
                   rda.sailor,
                   sc.fullname AS sailor_name,
                   rda.sailor_user,
                   rda.role,
                   r.code AS role_code,
                   rda.duty_type,
                   rda.starts_at,
                   rda.ends_at,
                   rda.status,
                   rda.notes,
                   rda.assigned_by,
                   rda.assigned_by AS granted_by,
                   rda.created_at
            FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
            JOIN "RACINGAPP"."ROLE" r ON r.key = rda.role
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = rda.sailor
            WHERE rda.race_id = :race_id
            ORDER BY rda.key ASC
        '''),
        {"race_id": race_id}
    ).mappings().all()


def get_sailor_for_club(conn, sailor_id, club_id):
    """Return (key, club) for a sailor, or None."""
    return conn.execute(
        text('''
            SELECT key, club
            FROM "RACINGAPP"."SAILORCONTROL"
            WHERE key = :sailor_id
            LIMIT 1
        '''),
        {"sailor_id": sailor_id}
    ).mappings().first()


def get_sailor_user_id(conn, sailor_id):
    """Return the latest SAILORUSER.key for a sailor, or None."""
    return conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."SAILORUSER"
            WHERE sailor = :sailor_id
            ORDER BY key DESC
            LIMIT 1
        '''),
        {"sailor_id": sailor_id}
    ).scalar()


def get_races_by_date_range(conn, club_id, from_date, to_date):
    """Return race keys whose started_at date falls within [from_date, to_date]."""
    return conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."RACE"
            WHERE club = :club_id
              AND started_at IS NOT NULL
              AND started_at >= CAST(:from_date AS timestamp)
              AND started_at < (CAST(:to_date AS timestamp) + INTERVAL '1 day')
            ORDER BY started_at ASC, key ASC
        '''),
        {"club_id": club_id, "from_date": from_date, "to_date": to_date}
    ).mappings().all()


def delete_duty_assignment(conn, duty_id, race_id):
    """Delete a duty assignment and return the SQLAlchemy result (check rowcount)."""
    return conn.execute(
        text('''
            DELETE FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT"
            WHERE key = :duty_id
              AND race_id = :race_id
        '''),
        {"duty_id": duty_id, "race_id": race_id}
    )
