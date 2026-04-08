from sqlalchemy import text


def resolve_sailor_club_id(conn, sailor_id):
    return conn.execute(
        text('''
            SELECT club
            FROM "RACINGAPP"."SAILORCONTROL"
            WHERE key = :sailor_id
            LIMIT 1
        '''),
        {"sailor_id": sailor_id}
    ).scalar()


def get_assigned_race_ids(conn, club_id, sailor_id):
    rows = conn.execute(
        text('''
            SELECT DISTINCT rda.race_id
            FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
            JOIN "RACINGAPP"."RACE" r ON r.key = rda.race_id
            JOIN "RACINGAPP"."ROLE" rr ON rr.key = rda.role
            WHERE r.club = :club_id
              AND rda.sailor = :sailor_id
              AND rda.status = 'assigned'
              AND rr.code = 'race_officer'
              AND (rda.starts_at IS NULL OR rda.starts_at <= CURRENT_TIMESTAMP)
              AND (rda.ends_at IS NULL OR rda.ends_at >= CURRENT_TIMESTAMP)
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()
    return [row["race_id"] for row in rows]
