from sqlalchemy import text


def get_sailors_with_boats(conn, club_id):
    return conn.execute(
        text('''
            SELECT sc.key AS sailor_id,
                   sc.fullname,
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
            JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.boat = hc.key
            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
            WHERE sc.club = :club_id
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
              AND (:from_date IS NULL OR r.started_at >= CAST(:from_date AS timestamp))
              AND (:to_date IS NULL OR r.started_at < (CAST(:to_date AS timestamp) + INTERVAL '1 day'))
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
              AND (:from_date IS NULL OR r.started_at >= CAST(:from_date AS timestamp))
              AND (:to_date IS NULL OR r.started_at < (CAST(:to_date AS timestamp) + INTERVAL '1 day'))
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
              AND r.status = 'finished'
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
                   COALESCE(MAX(l.lap_number), COUNT(l.key), 0) AS lap_count,
                   MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                   MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                   CASE WHEN MAX(CASE WHEN l.is_finish THEN 1 ELSE 0 END) = 1 THEN FALSE ELSE TRUE END AS dnf
            FROM "RACINGAPP"."RACE_ENTRY" re
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE re.race_id = :race_id
            GROUP BY re.key, re.sailor, re.boat, re.sail_number, re.handicap
            ORDER BY CASE
                       WHEN COALESCE(MAX(l.lap_number), COUNT(l.key), 0) > 0
                       THEN ROUND(MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)::numeric / COALESCE(MAX(l.lap_number), COUNT(l.key), 0), 0)
                       ELSE MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)
                     END ASC NULLS LAST,
                     CASE
                       WHEN COALESCE(MAX(l.lap_number), COUNT(l.key), 0) > 0
                       THEN ROUND(MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END)::numeric / COALESCE(MAX(l.lap_number), COUNT(l.key), 0), 0)
                       ELSE MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END)
                     END ASC NULLS LAST,
                     re.key ASC
        '''),
        {"race_id": race_id},
    ).mappings().all()


def get_latest_race_results_rows(conn, club_id, limit=5):
    return conn.execute(
        text('''
            SELECT r.key AS race_id,
                   r.race_no,
                   sc.name AS series_name,
                   r.started_at,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   COALESCE(MAX(l.lap_number), COUNT(l.key), 0) AS lap_count,
                   MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                   CASE
                     WHEN COALESCE(MAX(l.lap_number), COUNT(l.key), 0) > 0
                     THEN ROUND(MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)::numeric / COALESCE(MAX(l.lap_number), COUNT(l.key), 0), 0)
                     ELSE MAX(CASE WHEN l.is_finish THEN l.corrected_sec END)
                   END AS corrected_sec
            FROM "RACINGAPP"."RACE" r
            JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
            LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
            WHERE r.club = :club_id
              AND r.status = 'finished'
            GROUP BY r.key, r.race_no, sc.name, r.started_at, re.key, re.sailor, re.boat, re.sail_number
            ORDER BY r.started_at DESC NULLS LAST, corrected_sec ASC NULLS LAST, re.key ASC
            LIMIT :limit
        '''),
        {"club_id": club_id, "limit": int(limit)},
    ).mappings().all()


def get_series_results_rows(conn, club_id):
    return conn.execute(
        text('''
            WITH race_results AS (
                SELECT r.series AS series_id,
                       sc.name AS series_name,
                       r.key AS race_id,
                       r.race_no,
                       r.started_at,
                       bc.sailor AS sailor_id,
                       COALESCE(NULLIF(TRIM(re.sailor), ''), s.fullname, 'Unknown sailor') AS sailor_name,
                       COALESCE(NULLIF(TRIM(re.boat), ''), hc.boat, 'Unknown boat') AS boat_name,
                       re.sail_number,
                       COALESCE(MAX(l.lap_number), COUNT(l.key), 0) AS lap_count,
                       MAX(CASE WHEN l.is_finish THEN l.position END) AS finish_pos,
                       MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                       MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec,
                       CASE
                           WHEN COUNT(l.key) > 0 AND MAX(CASE WHEN l.is_finish THEN 1 ELSE 0 END) = 0 THEN TRUE
                           ELSE FALSE
                       END AS did_not_finish
                FROM "RACINGAPP"."RACE" r
                JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
                LEFT JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                LEFT JOIN "RACINGAPP"."SAILORCONTROL" s ON s.key = bc.sailor
                LEFT JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
                LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
                WHERE r.club = :club_id
                  AND r.status = 'finished'
                GROUP BY r.series, sc.name, r.key, r.race_no, r.started_at,
                         bc.sailor, s.fullname, re.key, re.sailor, re.boat, re.sail_number, hc.boat
            ),
            series_meta AS (
                SELECT r.series AS series_id,
                       MAX(r.started_at) AS latest_started_at,
                       COUNT(DISTINCT r.key) AS race_count
                FROM "RACINGAPP"."RACE" r
                WHERE r.club = :club_id
                  AND r.status = 'finished'
                GROUP BY r.series
            ),
            series_discard_meta AS (
                SELECT sm.series_id,
                       COALESCE(MAX(CASE WHEN ssd.after_races <= sm.race_count THEN ssd.discard_count END), 0) AS discard_count
                FROM series_meta sm
                LEFT JOIN "RACINGAPP"."SERIES_SCORING_DISCARD" ssd ON ssd.series = sm.series_id
                GROUP BY sm.series_id
            )
            SELECT rr.series_id,
                   rr.series_name,
                   rr.race_id,
                   rr.race_no,
                   rr.started_at,
                   rr.sailor_id,
                   rr.sailor_name,
                   rr.boat_name,
                   rr.sail_number,
                   rr.lap_count,
                   rr.finish_pos,
                   rr.elapsed_sec,
                   rr.corrected_sec,
                   rr.did_not_finish,
                   sm.latest_started_at,
                   sm.race_count,
                   COALESCE(sdm.discard_count, 0) AS discard_count
            FROM race_results rr
            JOIN series_meta sm ON sm.series_id = rr.series_id
            LEFT JOIN series_discard_meta sdm ON sdm.series_id = rr.series_id
            ORDER BY sm.latest_started_at DESC NULLS LAST,
                     rr.series_name ASC,
                     rr.started_at ASC NULLS LAST,
                     rr.race_no ASC,
                     CASE WHEN rr.finish_pos IS NULL THEN 1 ELSE 0 END,
                     rr.finish_pos ASC NULLS LAST,
                     rr.sailor_name ASC
        '''),
        {"club_id": club_id},
    ).mappings().all()


def get_club_summary_stats(conn, club_id):
    return conn.execute(
        text('''
            WITH sailor_count AS (
                SELECT COUNT(*) AS value
                FROM "RACINGAPP"."SAILORCONTROL"
                WHERE club = :club_id
            ),
            boat_count AS (
                SELECT COUNT(*) AS value
                FROM "RACINGAPP"."BOATCONTROL" bc
                JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
                WHERE sc.club = :club_id
            ),
            recent_races AS (
                SELECT COUNT(*) AS race_count,
                       COALESCE(AVG(entry_count), 0) AS avg_turnout
                FROM (
                    SELECT r.key,
                           COUNT(re.key) AS entry_count
                    FROM "RACINGAPP"."RACE" r
                    LEFT JOIN "RACINGAPP"."RACE_ENTRY" re ON re.race_id = r.key
                    WHERE r.club = :club_id
                      AND r.started_at >= NOW() - INTERVAL '90 days'
                    GROUP BY r.key
                ) x
            ),
            pending_reviews AS (
                SELECT COUNT(*) AS value
                FROM "RACINGAPP"."RACE" r
                WHERE r.club = :club_id
                  AND COALESCE(r.results_status, 'draft') <> 'locked'
            )
            SELECT (SELECT value FROM sailor_count) AS sailor_count,
                   (SELECT value FROM boat_count) AS boat_count,
                   (SELECT race_count FROM recent_races) AS recent_race_count,
                   (SELECT avg_turnout FROM recent_races) AS avg_turnout,
                   (SELECT value FROM pending_reviews) AS pending_review_count
        '''),
        {"club_id": club_id},
    ).mappings().first()
