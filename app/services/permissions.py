from datetime import datetime

from sqlalchemy import text


def _to_int_or_none(value):
    return int(value) if value not in (None, "", "null") else None


def club_user_has_role(conn, club_user_id, club_id, role_codes):
    if not club_user_id or not club_id:
        return False

    if isinstance(role_codes, str):
        role_codes = [role_codes]

    row = conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."CLUB_USER_ROLE" cur
            JOIN "RACINGAPP"."ROLE" r ON r.key = cur.role
            WHERE cur.club_user = :club_user_id
              AND cur.club = :club_id
              AND cur.is_active = TRUE
              AND r.code = ANY(:role_codes)
            LIMIT 1
        '''),
        {
            "club_user_id": int(club_user_id),
            "club_id": int(club_id),
            "role_codes": role_codes,
        }
    ).scalar()
    return bool(row)


def sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, role_codes, when_dt=None):
    if not sailor_user_id or not sailor_id:
        return False

    if isinstance(role_codes, str):
        role_codes = [role_codes]

    when_dt = when_dt or datetime.utcnow()
    row = conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."SAILOR_ROLE_GRANT" srg
            JOIN "RACINGAPP"."ROLE" r ON r.key = srg.role
            WHERE srg.sailor_user = :sailor_user_id
              AND srg.sailor = :sailor_id
              AND srg.is_active = TRUE
              AND (:club_id IS NULL OR srg.club IS NULL OR srg.club = :club_id)
              AND r.code = ANY(:role_codes)
              AND (srg.valid_from IS NULL OR srg.valid_from <= :when_dt)
              AND (srg.valid_to IS NULL OR srg.valid_to >= :when_dt)
            LIMIT 1
        '''),
        {
            "sailor_user_id": int(sailor_user_id),
            "sailor_id": int(sailor_id),
            "club_id": _to_int_or_none(club_id),
            "role_codes": role_codes,
            "when_dt": when_dt,
        }
    ).scalar()
    return bool(row)


def sailor_has_race_duty(conn, sailor_user_id, sailor_id, race_id, role_code="race_officer", when_dt=None):
    if not sailor_id or not race_id:
        return False

    when_dt = when_dt or datetime.utcnow()
    row = conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
            JOIN "RACINGAPP"."ROLE" r ON r.key = rda.role
            WHERE rda.race_id = :race_id
              AND rda.sailor = :sailor_id
              AND (:sailor_user_id IS NULL OR rda.sailor_user IS NULL OR rda.sailor_user = :sailor_user_id)
              AND rda.status = 'assigned'
              AND r.code = :role_code
              AND (rda.starts_at IS NULL OR rda.starts_at <= :when_dt)
              AND (rda.ends_at IS NULL OR rda.ends_at >= :when_dt)
            LIMIT 1
        '''),
        {
            "race_id": int(race_id),
            "sailor_id": int(sailor_id),
            "sailor_user_id": _to_int_or_none(sailor_user_id),
            "role_code": role_code,
            "when_dt": when_dt,
        }
    ).scalar()
    return bool(row)


def sailor_can_access_race_control(conn, sailor_user_id, sailor_id, club_id, race_id=None):
    if sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, "club_admin"):
        return True

    if race_id is None:
        return False

    return sailor_has_race_duty(conn, sailor_user_id, sailor_id, race_id, "race_officer")
