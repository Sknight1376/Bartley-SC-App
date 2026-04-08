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
                   hc.handicap
            FROM "RACINGAPP"."SAILORCONTROL" sc
            LEFT JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.sailor = sc.key
            LEFT JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
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
