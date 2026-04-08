from sqlalchemy import text


def get_sailors_with_boats(conn, club_id):
    return conn.execute(
        text('''
            SELECT sc.key AS sailor_id,
                   sc.fullname,
                   sc.firstname,
                   sc.surname,
                   bc.key AS boatkey,
                   bc.sail_number,
                   hc.boat AS boat_class,
                   hc.handicap
            FROM "RACINGAPP"."SAILORCONTROL" sc
            LEFT JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.sailor = sc.key
            LEFT JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
            WHERE sc.club = :club_id
            ORDER BY sc.fullname ASC, bc.key ASC
        '''),
        {"club_id": club_id},
    ).mappings().all()


def get_boat_class_usage(conn, club_id):
    return conn.execute(
        text('''
            SELECT hc.key AS handicap_key,
                   hc.boat AS boat_class,
                   hc.handicap,
                   COUNT(bc.key) AS assigned_count
            FROM "RACINGAPP"."HANDICAPCONTROL" hc
            LEFT JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.boat = hc.key
            LEFT JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            WHERE sc.club = :club_id OR sc.club IS NULL
            GROUP BY hc.key, hc.boat, hc.handicap
            ORDER BY assigned_count DESC, hc.boat ASC
        '''),
        {"club_id": club_id},
    ).mappings().all()


def get_race_calendar_rows(conn, club_id, from_date=None, to_date=None, limit=200):
    return conn.execute(
        text('''
            SELECT r.key AS race_id,
                   r.series AS series_id,
                   sc.name AS series_name,
                   r.race_no,
                   r.started_at,
                   r.ended_at,
                   r.status,
                   r.results_status,
                   r.source_mode
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id
              AND (:from_date IS NULL OR DATE(r.started_at) >= :from_date)
              AND (:to_date IS NULL OR DATE(r.started_at) <= :to_date)
            ORDER BY r.started_at ASC NULLS LAST, r.key ASC
            LIMIT :limit
        '''),
        {
            "club_id": club_id,
            "from_date": from_date,
            "to_date": to_date,
            "limit": int(limit),
        },
    ).mappings().all()


def get_duty_roster_rows(conn, club_id, from_date=None, to_date=None, limit=300):
    return conn.execute(
        text('''
            SELECT rda.key AS duty_id,
                   rda.race_id,
                   r.race_no,
                   r.started_at,
                   r.status AS race_status,
                   scs.name AS series_name,
                   rda.sailor,
                   s.fullname AS sailor_name,
                   rda.duty_type,
                   role.code AS role_code,
                   rda.status,
                   rda.notes
            FROM "RACINGAPP"."RACE_DUTY_ASSIGNMENT" rda
            JOIN "RACINGAPP"."RACE" r ON r.key = rda.race_id
            JOIN "RACINGAPP"."SERIESCONTROL" scs ON scs.key = r.series
            JOIN "RACINGAPP"."SAILORCONTROL" s ON s.key = rda.sailor
            JOIN "RACINGAPP"."ROLE" role ON role.key = rda.role
            WHERE r.club = :club_id
              AND (:from_date IS NULL OR DATE(r.started_at) >= :from_date)
              AND (:to_date IS NULL OR DATE(r.started_at) <= :to_date)
            ORDER BY r.started_at ASC NULLS LAST, r.race_no ASC, s.fullname ASC
            LIMIT :limit
        '''),
        {
            "club_id": club_id,
            "from_date": from_date,
            "to_date": to_date,
            "limit": int(limit),
        },
    ).mappings().all()


def get_results_review_queue_rows(conn, club_id, limit=200):
    return conn.execute(
        text('''
            SELECT r.key AS race_id,
                   r.race_no,
                   r.started_at,
                   r.status,
                   r.results_status,
                   r.source_mode,
                   sc.name AS series_name,
                   COUNT(re.key) AS entry_count,
                   COUNT(l.key) FILTER (WHERE l.is_finish = TRUE) AS finish_count
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            LEFT JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE r.club = :club_id
              AND COALESCE(r.results_status, 'draft') <> 'locked'
            GROUP BY r.key, r.race_no, r.started_at, r.status, r.results_status, r.source_mode, sc.name
            ORDER BY r.started_at DESC NULLS LAST, r.key DESC
            LIMIT :limit
        '''),
        {"club_id": club_id, "limit": int(limit)},
    ).mappings().all()


def get_handicap_recommendation_rows(conn, club_id, limit=200):
    return conn.execute(
        text('''
            SELECT a.key,
                   a.race_id,
                   r.race_no,
                   sc.name AS series_name,
                   a.entity_id AS recommendation_id,
                   a.action,
                   a.reason,
                   a.created_at,
                   a.actor_type,
                   a.actor_user_id
            FROM "RACINGAPP"."RACE_RESULT_AUDIT" a
            JOIN "RACINGAPP"."RACE" r ON r.key = a.race_id
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            WHERE r.club = :club_id
              AND a.entity_type = 'handicap_recommendation'
            ORDER BY a.created_at DESC, a.key DESC
            LIMIT :limit
        '''),
        {"club_id": club_id, "limit": int(limit)},
    ).mappings().all()


def race_belongs_to_club(conn, race_id, club_id):
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


def get_export_results_rows(conn, race_id):
    return conn.execute(
        text('''
            SELECT re.key AS entry_id,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   re.handicap,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                   CASE WHEN MAX(CASE WHEN l.is_finish THEN 1 ELSE 0 END) = 1 THEN FALSE ELSE TRUE END AS dnf
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number, re.handicap
            ORDER BY position ASC NULLS LAST, corrected_sec ASC NULLS LAST, re.key ASC
        '''),
        {"race_id": race_id},
    ).mappings().all()
