from sqlalchemy import text


def get_members_with_boats(conn, club_id):
    return conn.execute(
        text('''
            SELECT sc.key AS sailor_id,
                   sc.fullname,
                   sc.firstname,
                   sc.lastname,
                   bc.key AS boat_key,
                   bc.sail_number,
                   hc.boat AS boat_name,
                   hc.handicap,
                   su.key AS sailor_user_id,
                   su.username AS app_username,
                   su.is_active AS app_is_active,
                   su.last_login AS app_last_login
            FROM "RACINGAPP"."SAILORCONTROL" sc
            LEFT JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.sailor = sc.key
            LEFT JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
            LEFT JOIN LATERAL (
                SELECT key, username, is_active, last_login
                FROM "RACINGAPP"."SAILORUSER"
                WHERE sailor = sc.key
                ORDER BY key DESC
                LIMIT 1
            ) su ON TRUE
            WHERE sc.club = :club_id
            ORDER BY sc.fullname, bc.key
        '''),
        {"club_id": club_id}
    ).mappings().all()


def insert_member(conn, fullname, firstname, lastname, club_id):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SAILORCONTROL"
            (key, fullname, firstname, lastname, club)
            VALUES (nextval('key'), :fullname, :firstname, :lastname, :club)
            RETURNING key
        '''),
        {
            "fullname": fullname,
            "firstname": firstname,
            "lastname": lastname,
            "club": club_id,
        }
    ).scalar()


def update_member(conn, member_id, club_id, fullname, firstname, lastname):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILORCONTROL"
            SET fullname = :fullname,
                firstname = :firstname,
                lastname = :lastname
            WHERE key = :member_id
              AND club = :club_id
        '''),
        {
            "fullname": fullname,
            "firstname": firstname,
            "lastname": lastname,
            "member_id": member_id,
            "club_id": club_id,
        }
    )


def get_boat_catalog(conn):
    return conn.execute(
        text('''
            SELECT DISTINCT ON (hc.boat)
                   hc.key,
                   hc.boat,
                   hc.handicap
            FROM "RACINGAPP"."HANDICAPCONTROL" hc
            ORDER BY hc.boat, hc.date DESC, hc.key DESC
        ''')
    ).mappings().all()


def get_app_registrations(conn, club_id):
    """Sailors who registered via the app and are awaiting admin confirmation (is_active = FALSE)."""
    return conn.execute(
        text('''
            SELECT sc.key AS sailor_id,
                   sc.fullname,
                   sc.firstname,
                   sc.lastname,
                   su.key AS sailor_user_id,
                   su.username AS app_username,
                   su.created_at AS registered_at
            FROM "RACINGAPP"."SAILORCONTROL" sc
            JOIN "RACINGAPP"."SAILORUSER" su ON su.sailor = sc.key
            WHERE sc.club = :club_id
              AND su.is_active = FALSE
            ORDER BY su.created_at DESC
        '''),
        {"club_id": club_id}
    ).mappings().all()


def confirm_app_registration(conn, sailor_user_id, club_id):
    """Activate a pending app registration, scoped to the club for safety."""
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILORUSER" su
            SET is_active = TRUE
            FROM "RACINGAPP"."SAILORCONTROL" sc
            WHERE su.key = :sailor_user_id
              AND su.sailor = sc.key
              AND sc.club = :club_id
        '''),
        {"sailor_user_id": sailor_user_id, "club_id": club_id}
    )


def link_app_user_to_member(conn, sailor_user_id, target_sailor_id, club_id):
    """Re-point a SAILORUSER to an existing SAILORCONTROL record and activate it.
    Returns the old sailor_id so the caller can attempt cleanup."""
    target_ok = conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."SAILORCONTROL" WHERE key = :sid AND club = :club_id'),
        {"sid": target_sailor_id, "club_id": club_id}
    ).scalar()
    if not target_ok:
        raise ValueError("Target member not found in this club")

    old_sailor_id = conn.execute(
        text('''
            SELECT su.sailor
            FROM "RACINGAPP"."SAILORUSER" su
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = su.sailor
            WHERE su.key = :uid
              AND sc.club = :club_id
            LIMIT 1
        '''),
        {"uid": sailor_user_id, "club_id": club_id}
    ).scalar()
    if old_sailor_id is None:
        raise ValueError("Registration not found in this club")

    conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILORUSER"
            SET sailor = :target_sailor_id,
                is_active = TRUE
            WHERE key = :sailor_user_id
        '''),
        {"target_sailor_id": target_sailor_id, "sailor_user_id": sailor_user_id}
    )

    conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILOR_ROLE_GRANT"
            SET sailor = :target_sailor_id,
                club = COALESCE(club, :club_id)
            WHERE sailor_user = :sailor_user_id
              AND sailor = :old_sailor_id
        '''),
        {
            "target_sailor_id": target_sailor_id,
            "club_id": club_id,
            "sailor_user_id": sailor_user_id,
            "old_sailor_id": old_sailor_id,
        }
    )
    return old_sailor_id


def delete_orphaned_sailor(conn, sailor_id, club_id):
    """Delete a SAILORCONTROL record only when it no longer has related data."""
    boat_count = conn.execute(
        text('SELECT COUNT(*) FROM "RACINGAPP"."BOATCONTROL" WHERE sailor = :sid'),
        {"sid": sailor_id}
    ).scalar() or 0
    user_count = conn.execute(
        text('SELECT COUNT(*) FROM "RACINGAPP"."SAILORUSER" WHERE sailor = :sid'),
        {"sid": sailor_id}
    ).scalar() or 0
    role_grant_count = conn.execute(
        text('SELECT COUNT(*) FROM "RACINGAPP"."SAILOR_ROLE_GRANT" WHERE sailor = :sid'),
        {"sid": sailor_id}
    ).scalar() or 0
    duty_count = conn.execute(
        text('SELECT COUNT(*) FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" WHERE sailor = :sid'),
        {"sid": sailor_id}
    ).scalar() or 0
    if boat_count > 0 or user_count > 0 or role_grant_count > 0 or duty_count > 0:
        raise ValueError("Sailor still has related records; not deleted")
    conn.execute(
        text('DELETE FROM "RACINGAPP"."SAILORCONTROL" WHERE key = :sid AND club = :club_id'),
        {"sid": sailor_id, "club_id": club_id}
    )


def member_exists(conn, member_id, club_id):
    return conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."SAILORCONTROL" WHERE key = :member_id AND club = :club_id'),
        {"member_id": member_id, "club_id": club_id}
    ).scalar()


def insert_member_boat(conn, handicap_key, member_id, sail_number):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number)
            VALUES (nextval('key'), :boat, :sailor, :sail_number)
            RETURNING key
        '''),
        {"boat": handicap_key, "sailor": member_id, "sail_number": sail_number}
    ).scalar()
