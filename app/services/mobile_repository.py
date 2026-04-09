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
              AND (
                (
                  (rda.starts_at IS NULL OR rda.starts_at <= CURRENT_TIMESTAMP)
                  AND (rda.ends_at IS NULL OR rda.ends_at >= CURRENT_TIMESTAMP)
                )
                OR DATE(r.started_at) = CURRENT_DATE
              )
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()
    return [row["race_id"] for row in rows]


def get_upcoming_sailor_duties(conn, sailor_id):
    """Return upcoming duty assignments for a sailor (races today or in the future)."""
    return conn.execute(
        text('''
            SELECT rda.race_id,
                   rda.duty_type,
                   rda.starts_at AS duty_starts_at,
                   rda.ends_at   AS duty_ends_at,
                   rda.status,
                   r.started_at  AS race_date,
                   r.race_no,
                   cc.name       AS club_name,
                   rr.code       AS role_code
            FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
            JOIN "RACINGAPP"."RACE" r ON r.key = rda.race_id
            JOIN "RACINGAPP"."ROLE" rr ON rr.key = rda.role
            JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = r.club
            WHERE rda.sailor = :sailor_id
              AND rda.status = 'assigned'
              AND (r.started_at IS NULL OR r.started_at >= CURRENT_DATE)
            ORDER BY r.started_at ASC NULLS LAST, r.key ASC
        '''),
        {"sailor_id": sailor_id}
    ).mappings().all()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate_sailor(conn, username, password):
    return conn.execute(
        text('''
            SELECT su.key AS sailor_user_id,
                   su.username,
                   su.sailor AS sailor_id,
                   sc.club,
                   cc.name AS club_name,
                   sc.fullname,
                   sc.firstname,
                   sc.lastname
            FROM "RACINGAPP"."SAILORUSER" su
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = su.sailor
            LEFT JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = sc.club
            WHERE LOWER(su.username) = LOWER(:username)
              AND su.is_active = TRUE
              AND su.password_hash = crypt(:password, su.password_hash)
            LIMIT 1
        '''),
        {"username": username, "password": password}
    ).mappings().first()


def update_last_login(conn, user_id):
    conn.execute(
        text('UPDATE "RACINGAPP"."SAILORUSER" SET last_login = CURRENT_TIMESTAMP WHERE key = :user_id'),
        {"user_id": user_id}
    )


def check_username_exists(conn, username):
    return conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."SAILORUSER" WHERE LOWER(username) = LOWER(:username) LIMIT 1'),
        {"username": username}
    ).scalar()


def resolve_club(conn, club_id):
    return conn.execute(
        text('SELECT key, name FROM "RACINGAPP"."CLUBCONTROL" WHERE key = :club_id LIMIT 1'),
        {"club_id": club_id}
    ).mappings().first()


def insert_sailor(conn, fullname, firstname, lastname, club):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SAILORCONTROL" (key, fullname, firstname, lastname, club)
            VALUES (nextval('key'), :fullname, :firstname, :lastname, :club)
            RETURNING key
        '''),
        {"fullname": fullname, "firstname": firstname, "lastname": lastname, "club": club}
    ).scalar_one()


def insert_sailor_user(conn, sailor_id, username, password):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SAILORUSER" (key, sailor, username, password_hash, is_active)
            VALUES (nextval('key'), :sailor_id, :username, crypt(:password, gen_salt('bf')), FALSE)
            RETURNING key
        '''),
        {"sailor_id": sailor_id, "username": username, "password": password}
    ).scalar_one()


# ---------------------------------------------------------------------------
# Sailor profile & boats
# ---------------------------------------------------------------------------

def get_sailor_profile(conn, sailor_id):
    return conn.execute(
        text('''
            SELECT sc.key, sc.fullname, sc.firstname, sc.lastname, sc.club, cc.name AS club_name
            FROM "RACINGAPP"."SAILORCONTROL" sc
            LEFT JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = sc.club
            WHERE sc.key = :sailor_id
        '''),
        {"sailor_id": sailor_id}
    ).mappings().first()


def get_sailor_boats(conn, sailor_id):
    return conn.execute(
        text('''
            SELECT bc.key AS boat_key,
                   bc.boat AS boat_class_id,
                   bc.sail_number,
                   hc.boat AS boat_name,
                   hc.handicap
            FROM "RACINGAPP"."BOATCONTROL" bc
            LEFT JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
            WHERE bc.sailor = :sailor_id
            ORDER BY bc.key DESC
        '''),
        {"sailor_id": sailor_id}
    ).mappings().all()


def update_sailor_profile(conn, sailor_id, fullname, firstname, lastname, club_id):
    return conn.execute(
        text('''
            UPDATE "RACINGAPP"."SAILORCONTROL"
            SET fullname = :fullname,
                firstname = :firstname,
                lastname = :lastname,
                club = :club_id
            WHERE key = :sailor_id
        '''),
        {
            "fullname": fullname, "firstname": firstname,
            "lastname": lastname, "club_id": club_id, "sailor_id": sailor_id
        }
    )


def get_all_clubs(conn):
    return conn.execute(
        text('SELECT key AS id, name FROM "RACINGAPP"."CLUBCONTROL" ORDER BY name ASC')
    ).mappings().all()


def get_series_for_club(conn, club_id):
    return conn.execute(
        text('''
            SELECT key AS id, year, name
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE club = :club_id
            ORDER BY year DESC NULLS LAST, name ASC
        '''),
        {"club_id": club_id}
    ).mappings().all()


def get_boat_classes(conn):
    return conn.execute(
        text('''
            SELECT DISTINCT ON (hc.boat)
                   hc.key AS id,
                   hc.boat AS name,
                   hc.handicap
            FROM "RACINGAPP"."HANDICAPCONTROL" hc
            WHERE hc.boat IS NOT NULL
            ORDER BY hc.boat ASC, hc.date DESC, hc.key DESC
        ''')
    ).mappings().all()


def get_boat_class(conn, boat_class_id):
    return conn.execute(
        text('''
            SELECT key, boat AS boat_name, handicap
            FROM "RACINGAPP"."HANDICAPCONTROL"
            WHERE key = :boat_class_id
            LIMIT 1
        '''),
        {"boat_class_id": boat_class_id}
    ).mappings().first()


def insert_boat(conn, boat_class_id, sailor_id, sail_number):
    boat_key = conn.execute(text("SELECT NEXTVAL('key')")).scalar()
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number)
            VALUES (:key, :boat_class_id, :sailor_id, :sail_number)
        '''),
        {"key": boat_key, "boat_class_id": boat_class_id, "sailor_id": sailor_id, "sail_number": sail_number}
    )
    return boat_key


def delete_boat(conn, boat_key, sailor_id):
    return conn.execute(
        text('DELETE FROM "RACINGAPP"."BOATCONTROL" WHERE key = :boat_key AND sailor = :sailor_id'),
        {"boat_key": boat_key, "sailor_id": sailor_id}
    )


# ---------------------------------------------------------------------------
# Upcoming races & dashboard
# ---------------------------------------------------------------------------

def get_upcoming_races(conn, club_id, sailor_id):
    return conn.execute(
        text('''
            SELECT r.key AS race_id,
                   r.race_no,
                   r.status,
                   r.started_at,
                   sc.name AS series_name,
                   CASE WHEN EXISTS (
                       SELECT 1
                       FROM "RACINGAPP"."RACE_ENTRY" re
                       JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                       WHERE re.race_id = r.key AND bc.sailor = :sailor_id
                   ) THEN TRUE ELSE FALSE END AS joined,
                   CASE WHEN r.status = 'finished' OR EXISTS (
                       SELECT 1
                       FROM "RACINGAPP"."RACE_ENTRY" re2
                       JOIN "RACINGAPP"."BOATCONTROL" bc2 ON bc2.key = re2.boatkey
                       JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re2.key
                       WHERE re2.race_id = r.key AND bc2.sailor = :sailor_id
                   ) THEN TRUE ELSE FALSE END AS results_available
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id
              AND r.status IN ('not_started', 'active')
              AND r.started_at IS NOT NULL
              AND r.started_at < (NOW() + INTERVAL '5 day')
              AND (r.status = 'active' OR r.started_at >= NOW())
            ORDER BY r.started_at ASC, r.key ASC
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()


def get_dashboard_data(conn, club_id, sailor_id):
    """Returns (upcoming, completed, latest_result_day, latest_day_rows, positions)."""
    upcoming = conn.execute(
        text('''
            SELECT r.key AS race_id, r.race_no, r.status, r.started_at,
                   sc.name AS series_name,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" re
                       JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                       WHERE re.race_id = r.key AND bc.sailor = :sailor_id
                   ) THEN TRUE ELSE FALSE END AS joined,
                   CASE WHEN r.status = 'finished' OR EXISTS (
                       SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" re2
                       JOIN "RACINGAPP"."BOATCONTROL" bc2 ON bc2.key = re2.boatkey
                       JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re2.key
                       WHERE re2.race_id = r.key AND bc2.sailor = :sailor_id
                   ) THEN TRUE ELSE FALSE END AS results_available
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id
              AND r.status IN ('not_started', 'active')
              AND r.started_at IS NOT NULL
              AND r.started_at < (NOW() + INTERVAL '5 day')
              AND (r.status = 'active' OR r.started_at >= NOW())
            ORDER BY CASE WHEN r.status = 'active' THEN 0 ELSE 1 END,
                     r.started_at ASC NULLS LAST, r.key ASC
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()

    completed = conn.execute(
        text('''
            SELECT r.key AS race_id, r.race_no, r.status, r.started_at,
                   sc.name AS series_name,
                   TRUE AS joined, TRUE AS results_available
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
            JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
            WHERE r.club = :club_id AND bc.sailor = :sailor_id AND r.status = 'finished'
            GROUP BY r.key, r.race_no, r.status, r.started_at, sc.name
            ORDER BY COALESCE(r.ended_at, r.started_at) DESC NULLS LAST, r.key DESC
            LIMIT 10
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()

    latest_result_day = conn.execute(
        text('''
            SELECT DATE(MAX(COALESCE(r.ended_at, r.started_at))) AS latest_day
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
            JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
            WHERE r.club = :club_id AND bc.sailor = :sailor_id
              AND EXISTS (
                  SELECT 1 FROM "RACINGAPP"."LAP" l
                  WHERE l.race_entry_id = re.key AND l.is_finish = TRUE
              )
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).scalar()

    latest_day_rows = []
    if latest_result_day is not None:
        latest_day_rows = conn.execute(
            text('''
                SELECT r.key AS race_id, r.race_no, r.started_at, sc.name AS series_name,
                       re.sailor, re.boat, re.sail_number,
                       MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                       MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                       MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec
                FROM "RACINGAPP"."RACE" r
                JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
                JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
                WHERE r.club = :club_id AND bc.sailor = :sailor_id
                  AND DATE(COALESCE(r.ended_at, r.started_at)) = :latest_day
                  AND EXISTS (
                      SELECT 1 FROM "RACINGAPP"."LAP" l2
                      WHERE l2.race_entry_id = re.key AND l2.is_finish = TRUE
                  )
                GROUP BY r.key, r.race_no, r.started_at, sc.name, re.key, re.sailor, re.boat, re.sail_number
                ORDER BY r.race_no ASC, position ASC NULLS LAST, corrected_sec ASC NULLS LAST
            '''),
            {"club_id": club_id, "sailor_id": sailor_id, "latest_day": latest_result_day}
        ).mappings().all()

    positions = conn.execute(
        text('''
            WITH sailor_results AS (
                SELECT r.series AS series_id, sc.name AS series_name,
                       bc.sailor AS sailor_id, re.sailor AS sailor_name,
                       MAX(CASE WHEN l.is_finish THEN l.position END) AS finish_pos
                FROM "RACINGAPP"."RACE" r
                JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
                JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
                WHERE r.club = :club_id
                GROUP BY r.series, sc.name, bc.sailor, re.sailor, re.key
            ),
            points AS (
                SELECT series_id, series_name, sailor_id, sailor_name,
                       SUM(CASE WHEN finish_pos IS NULL THEN 9999 ELSE finish_pos END) AS points,
                       COUNT(*) FILTER (WHERE finish_pos IS NOT NULL) AS races_completed
                FROM sailor_results
                GROUP BY series_id, series_name, sailor_id, sailor_name
            ),
            ranked AS (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY series_id ORDER BY points ASC, races_completed DESC, sailor_name ASC
                       ) AS rank,
                       COUNT(*) OVER (PARTITION BY series_id) AS sailors_count
                FROM points
            )
            SELECT series_id, series_name, sailor_name, points, races_completed, rank, sailors_count
            FROM ranked
            WHERE sailor_id = :sailor_id
            ORDER BY series_name ASC
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()

    return upcoming, completed, latest_result_day, latest_day_rows, positions


def get_series_standings(conn, club_id):
    return conn.execute(
        text('''
            WITH sailor_results AS (
                SELECT r.series AS series_id, sc.name AS series_name,
                       bc.sailor AS sailor_id, re.sailor AS sailor_name,
                       MAX(CASE WHEN l.is_finish THEN l.position END) AS finish_pos
                FROM "RACINGAPP"."RACE" r
                JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
                JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
                WHERE r.club = :club_id
                GROUP BY r.series, sc.name, bc.sailor, re.sailor, re.key
            ),
            points AS (
                SELECT series_id, series_name, sailor_id, sailor_name,
                       SUM(CASE WHEN finish_pos IS NULL THEN 9999 ELSE finish_pos END) AS points,
                       COUNT(*) FILTER (WHERE finish_pos IS NOT NULL) AS races_completed
                FROM sailor_results
                GROUP BY series_id, series_name, sailor_id, sailor_name
            )
            SELECT series_id, series_name, sailor_id, sailor_name, points, races_completed,
                   ROW_NUMBER() OVER (
                       PARTITION BY series_id ORDER BY points ASC, races_completed DESC, sailor_name ASC
                   ) AS rank
            FROM points
            ORDER BY series_name ASC, rank ASC
        '''),
        {"club_id": club_id}
    ).mappings().all()


# ---------------------------------------------------------------------------
# Race join
# ---------------------------------------------------------------------------

def get_race_for_join(conn, race_id, club_id):
    return conn.execute(
        text('''
            SELECT key, status, started_at
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id AND club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()


def get_boat_for_join(conn, boat_key, sailor_id, club_id):
    return conn.execute(
        text('''
            SELECT bc.key AS boat_key,
                   bc.sail_number,
                   hc.boat,
                   hc.handicap,
                   sc.fullname
            FROM "RACINGAPP"."BOATCONTROL" bc
            JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            WHERE bc.key = :boat_key AND bc.sailor = :sailor_id AND sc.club = :club_id
        '''),
        {"boat_key": boat_key, "sailor_id": sailor_id, "club_id": club_id}
    ).mappings().first()


def check_race_entry_exists(conn, race_id, boat_key):
    return conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id AND boatkey = :boat_key'),
        {"race_id": race_id, "boat_key": boat_key}
    ).scalar()


def insert_race_entry_for_join(conn, race_id, boat_row):
    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_ENTRY" (key, race_id, boatkey, sailor, boat, sail_number, handicap)
            VALUES (nextval('key'), :race_id, :boatkey, :sailor, :boat, :sail_number, :handicap)
        '''),
        {
            "race_id": race_id,
            "boatkey": boat_row["boat_key"],
            "sailor": boat_row["fullname"],
            "boat": boat_row["boat"],
            "sail_number": boat_row["sail_number"],
            "handicap": boat_row["handicap"]
        }
    )


# ---------------------------------------------------------------------------
# Race results
# ---------------------------------------------------------------------------

def get_race_exists_for_club(conn, race_id, club_id):
    return conn.execute(
        text('SELECT 1 FROM "RACINGAPP"."RACE" WHERE key = :race_id AND club = :club_id'),
        {"race_id": race_id, "club_id": club_id}
    ).scalar()


def get_my_race_results(conn, race_id, sailor_id):
    return conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor, re.boat, re.sail_number,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec
            FROM "RACINGAPP"."RACE_ENTRY" re
            JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id AND bc.sailor = :sailor_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number
            ORDER BY position ASC NULLS LAST, corrected_sec ASC NULLS LAST
        '''),
        {"race_id": race_id, "sailor_id": sailor_id}
    ).mappings().all()


def get_race_leaderboard(conn, race_id):
    return conn.execute(
        text('''
            SELECT re.sailor, re.boat, re.sail_number,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number
            ORDER BY position ASC NULLS LAST, corrected_sec ASC NULLS LAST
        '''),
        {"race_id": race_id}
    ).mappings().all()


# ---------------------------------------------------------------------------
# Mobile race control
# ---------------------------------------------------------------------------

def get_control_upcoming_races_admin(conn, club_id):
    return conn.execute(
        text('''
            SELECT r.key AS race_id, r.series AS series_id, r.race_no,
                   r.started_at, r.status, sc.name AS series_name
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id AND r.status IN ('not_started', 'active')
            ORDER BY CASE WHEN r.status = 'active' THEN 0 ELSE 1 END,
                     r.started_at ASC NULLS LAST, r.key ASC
        '''),
        {"club_id": club_id}
    ).mappings().all()


def get_control_upcoming_races_duty(conn, club_id, sailor_id):
    return conn.execute(
        text('''
            SELECT r.key AS race_id, r.series AS series_id, r.race_no,
                   r.started_at, r.status, sc.name AS series_name
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id AND r.status IN ('not_started', 'active')
              AND EXISTS (
                  SELECT 1
                  FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
                  JOIN "RACINGAPP"."ROLE" rr ON rr.key = rda.role
                  WHERE rda.race_id = r.key AND rda.sailor = :sailor_id
                    AND rda.status = 'assigned' AND rr.code = 'race_officer'
                    AND (rda.starts_at IS NULL OR rda.starts_at <= CURRENT_TIMESTAMP)
                    AND (rda.ends_at IS NULL OR rda.ends_at >= CURRENT_TIMESTAMP)
              )
            ORDER BY CASE WHEN r.status = 'active' THEN 0 ELSE 1 END,
                     r.started_at ASC NULLS LAST, r.key ASC
        '''),
        {"club_id": club_id, "sailor_id": sailor_id}
    ).mappings().all()


def get_control_race_and_entries(conn, race_id, club_id):
    race_row = conn.execute(
        text('''
            SELECT key, race_no, status, started_at
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id AND club = :club_id
            LIMIT 1
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()

    if race_row is None:
        return None, []

    entries = conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor, re.boat, re.sail_number, re.handicap,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM "RACINGAPP"."LAP" l
                       WHERE l.race_entry_id = re.key AND l.is_finish = TRUE
                   ) THEN TRUE ELSE FALSE END AS finished
            FROM "RACINGAPP"."RACE_ENTRY" re
            WHERE re.race_id = :race_id
            ORDER BY re.key ASC
        '''),
        {"race_id": race_id}
    ).mappings().all()

    return race_row, entries


def get_control_summary(conn, race_id, club_id):
    race_row = conn.execute(
        text('''
            SELECT r.race_no, r.started_at, r.ended_at, r.status,
                   cc.name AS club_name, sc.name AS series_name
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."CLUBCONTROL" cc ON r.club = cc.key
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON r.series = sc.key
            WHERE r.key = :race_id AND r.club = :club_id
        '''),
        {"race_id": race_id, "club_id": club_id}
    ).mappings().first()

    if race_row is None:
        return None, []

    results = conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor, re.boat, re.sail_number, re.handicap,
                   COUNT(l.key) AS lap_count,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec   END) AS final_elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS final_corrected_sec,
                   MAX(CASE WHEN l.is_finish THEN l.position      END) AS final_position
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number, re.handicap
            ORDER BY MAX(CASE WHEN l.is_finish THEN l.position      END) ASC NULLS LAST,
                     MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) ASC NULLS LAST
        '''),
        {"race_id": race_id}
    ).mappings().all()

    return race_row, results
