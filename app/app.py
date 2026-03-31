from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta, time




app = Flask(__name__)
# Connect to local PostgreSQL (Windows) instead of Docker
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dwh:DBTTEST@localhost:5432/dwh"
# Do not enforce SERVER_NAME in this environment; allow host and port to be set via run() parameters
# app.config['SERVER_NAME'] = "localhost:5000"
app.app_context().push()
db = SQLAlchemy(app)
app.secret_key = "4001376"
db.Model.metadata.reflect(db.engine, schema='RACINGAPP')

class Boats(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.HANDICAPCONTROL"]

# Reflected CLUBCONTROL
class ClubControl(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.CLUBCONTROL"]

# Reflected SERIESCONTROL
class SeriesControl(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.SERIESCONTROL"]

# Reflected SAILORCONTROL
class SailorControl(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.SAILORCONTROL"]


# Reflected BOATCONTROL
class BoatControl(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.BOATCONTROL"]

handicaps = Boats.query.all()


# ---------- helpers ----------

def parse_hms_to_seconds(s: str):
    """Parse HH:MM:SS or H:MM:SS into integer seconds."""
    s = (s or "").strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid time string: {s}")
    h, m, sec = [int(x) for x in parts]
    return h * 3600 + m * 60 + sec


def set_mobile_session(sailor_user_id, sailor_id, username, club_id):
    session["sailor_user_id"] = str(sailor_user_id)
    session["sailor_id"] = str(sailor_id)
    session["sailor_username"] = username
    if club_id is None:
        session.pop("sailor_club_id", None)
    else:
        session["sailor_club_id"] = str(club_id)



# ---------- routes ----------

@app.route("/")
def intro_page():
    return render_template("intro.html")


@app.get("/login")
def login_page():
    # Clear race state on explicit return to login
    session.pop("race", None)
    session.pop("series_id", None)
    return render_template("login.html")


@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Missing username or password"}), 400

    try:
        with db.engine.connect() as conn:
            user_row = conn.execute(
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

            if user_row:
                conn.execute(
                    text('UPDATE "RACINGAPP"."CLUBUSER" SET last_login = CURRENT_TIMESTAMP WHERE key = :user_id'),
                    {"user_id": user_row["user_id"]}
                )
                conn.commit()

        if not user_row:
            return jsonify({"ok": False, "error": "Invalid username or password"}), 401

        session["user_id"] = str(user_row["user_id"])
        session["username"] = user_row["username"]
        session["club_id"] = str(user_row["club_id"])
        session["club_name"] = user_row["club_name"]
        race_data = session.get("race", {})
        race_data["club_id"] = str(user_row["club_id"])
        session["race"] = race_data

        return jsonify({
            "ok": True,
            "club_id": str(user_row["club_id"]),
            "club_name": user_row["club_name"],
            "username": user_row["username"]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/sailor_portal")
def sailor_portal_page():
    return render_template("sailor_portal.html")


@app.post("/api/mobile/login")
def api_mobile_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Missing username or password"}), 400

    try:
        with db.engine.begin() as conn:
            sailor_user = conn.execute(
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

            if not sailor_user:
                return jsonify({"ok": False, "error": "Invalid username or password"}), 401

            conn.execute(
                text('UPDATE "RACINGAPP"."SAILORUSER" SET last_login = CURRENT_TIMESTAMP WHERE key = :user_id'),
                {"user_id": sailor_user["sailor_user_id"]}
            )

        set_mobile_session(
            sailor_user["sailor_user_id"],
            sailor_user["sailor_id"],
            sailor_user["username"],
            sailor_user["club"]
        )

        return jsonify({
            "ok": True,
            "username": sailor_user["username"],
            "sailor_id": sailor_user["sailor_id"],
            "club_id": sailor_user["club"],
            "club_name": sailor_user["club_name"],
            "full_name": sailor_user["fullname"],
            "first_name": sailor_user["firstname"],
            "last_name": sailor_user["lastname"]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/mobile/register")
def api_mobile_register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    club_id = payload.get("club_id")

    if not username or not password or not first_name:
        return jsonify({"ok": False, "error": "username, password, and first_name are required"}), 400

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            existing_user = conn.execute(
                text('SELECT 1 FROM "RACINGAPP"."SAILORUSER" WHERE LOWER(username) = LOWER(:username) LIMIT 1'),
                {"username": username}
            ).scalar()
            if existing_user:
                return jsonify({"ok": False, "error": "Username already exists"}), 409

            resolved_club_id = None
            resolved_club_name = None
            if club_id not in (None, "", "null"):
                club_row = conn.execute(
                    text('SELECT key, name FROM "RACINGAPP"."CLUBCONTROL" WHERE key = :club_id LIMIT 1'),
                    {"club_id": club_id}
                ).mappings().first()
                if not club_row:
                    return jsonify({"ok": False, "error": "Club not found"}), 404
                resolved_club_id = club_row["key"]
                resolved_club_name = club_row["name"]

            sailor_id = conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."SAILORCONTROL" (key, fullname, firstname, lastname, club)
                    VALUES (nextval('key'), :fullname, :firstname, :lastname, :club)
                    RETURNING key
                '''),
                {
                    "fullname": full_name,
                    "firstname": first_name,
                    "lastname": last_name or None,
                    "club": resolved_club_id
                }
            ).scalar_one()

            sailor_user_id = conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."SAILORUSER" (key, sailor, username, password_hash)
                    VALUES (nextval('key'), :sailor_id, :username, crypt(:password, gen_salt('bf')))
                    RETURNING key
                '''),
                {
                    "sailor_id": sailor_id,
                    "username": username,
                    "password": password
                }
            ).scalar_one()

        set_mobile_session(sailor_user_id, sailor_id, username, resolved_club_id)

        return jsonify({
            "ok": True,
            "username": username,
            "sailor_id": sailor_id,
            "club_id": resolved_club_id,
            "club_name": resolved_club_name,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name or None
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/mobile/logout")
def api_mobile_logout():
    for key in ["sailor_user_id", "sailor_id", "sailor_username", "sailor_club_id"]:
        session.pop(key, None)
    return jsonify({"ok": True})


@app.get("/api/mobile/me")
def api_mobile_me():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            sailor = conn.execute(
                text('''
                    SELECT sc.key, sc.fullname, sc.firstname, sc.lastname, sc.club, cc.name AS club_name
                    FROM "RACINGAPP"."SAILORCONTROL" sc
                    LEFT JOIN "RACINGAPP"."CLUBCONTROL" cc ON cc.key = sc.club
                    WHERE sc.key = :sailor_id
                '''),
                {"sailor_id": sailor_id}
            ).mappings().first()

            if not sailor:
                return jsonify({"ok": False, "error": "Sailor not found"}), 404

            boats = conn.execute(
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

        return jsonify({
            "ok": True,
            "profile": {
                "id": sailor["key"],
                "full_name": sailor["fullname"],
                "first_name": sailor["firstname"],
                "last_name": sailor["lastname"],
                "username": session.get("sailor_username"),
                "club_id": sailor["club"],
                "club_name": sailor["club_name"]
            },
            "boats": [dict(b) for b in boats]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.put("/api/mobile/me")
def api_mobile_update_me():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    club_id = payload.get("club_id")
    if not first_name:
        return jsonify({"ok": False, "error": "first_name is required"}), 400

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            resolved_club_id = None
            if club_id not in (None, "", "null"):
                club_row = conn.execute(
                    text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE key = :club_id LIMIT 1'),
                    {"club_id": club_id}
                ).mappings().first()
                if not club_row:
                    return jsonify({"ok": False, "error": "Club not found"}), 404
                resolved_club_id = club_row["key"]

            updated = conn.execute(
                text('''
                    UPDATE "RACINGAPP"."SAILORCONTROL"
                    SET fullname = :fullname,
                        firstname = :firstname,
                        lastname = :lastname,
                        club = :club_id
                    WHERE key = :sailor_id
                '''),
                {
                    "fullname": full_name,
                    "firstname": first_name,
                    "lastname": last_name or None,
                    "sailor_id": sailor_id,
                    "club_id": resolved_club_id
                }
            )

        if updated.rowcount == 0:
            return jsonify({"ok": False, "error": "Sailor not found"}), 404

        if resolved_club_id is None:
            session.pop("sailor_club_id", None)
        else:
            session["sailor_club_id"] = str(resolved_club_id)

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/clubs")
def api_mobile_clubs():
    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text('''
                    SELECT key AS id, name
                    FROM "RACINGAPP"."CLUBCONTROL"
                    ORDER BY name ASC
                ''')
            ).mappings().all()
        return jsonify({"ok": True, "clubs": [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/series")
def api_mobile_series():
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    if not club_id:
        return jsonify({"ok": True, "series": []})

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text('''
                    SELECT key AS id, year, name
                    FROM "RACINGAPP"."SERIESCONTROL"
                    WHERE club = :club_id
                    ORDER BY year DESC NULLS LAST, name ASC
                '''),
                {"club_id": club_id}
            ).mappings().all()
        return jsonify({"ok": True, "series": [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/boats")
def api_mobile_boats():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            boats = conn.execute(
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
        return jsonify({"ok": True, "boats": [dict(b) for b in boats]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/boat-classes")
def api_mobile_boat_classes():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
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
        return jsonify({"ok": True, "classes": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/mobile/boats")
def api_mobile_create_boat():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    sail_number = (payload.get("sail_number") or "").strip()
    boat_class_id = payload.get("boat_class_id")
    if not sail_number:
        return jsonify({"ok": False, "error": "sail_number is required"}), 400
    if boat_class_id in (None, "", "null"):
        return jsonify({"ok": False, "error": "boat_class_id is required"}), 400

    try:
        with db.engine.begin() as conn:
            class_row = conn.execute(
                text('''
                    SELECT key, boat AS boat_name, handicap
                    FROM "RACINGAPP"."HANDICAPCONTROL"
                    WHERE key = :boat_class_id
                    LIMIT 1
                '''),
                {"boat_class_id": boat_class_id}
            ).mappings().first()
            if not class_row:
                return jsonify({"ok": False, "error": "Boat class not found"}), 404

            # Generate new key for boat
            next_key_result = conn.execute(
                text("SELECT NEXTVAL('key')")
            ).scalar()
            boat_key = next_key_result

            # Insert into BOATCONTROL
            conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number)
                    VALUES (:key, :boat_class_id, :sailor_id, :sail_number)
                '''),
                {
                    "key": boat_key,
                    "boat_class_id": class_row["key"],
                    "sailor_id": sailor_id,
                    "sail_number": sail_number
                }
            )

        return jsonify({
            "ok": True,
            "boat": {
                "boat_key": boat_key,
                "boat_class_id": class_row["key"],
                "sail_number": sail_number,
                "boat_name": class_row["boat_name"],
                "handicap": class_row["handicap"]
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.delete("/api/mobile/boats/<int:boat_key>")
def api_mobile_delete_boat(boat_key):
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.begin() as conn:
            result = conn.execute(
                text('''
                    DELETE FROM "RACINGAPP"."BOATCONTROL"
                    WHERE key = :boat_key AND sailor = :sailor_id
                '''),
                {"boat_key": boat_key, "sailor_id": sailor_id}
            )
            if result.rowcount == 0:
                return jsonify({"ok": False, "error": "Boat not found"}), 404
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/races/upcoming")
def api_mobile_upcoming_races():
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    if not club_id:
        return jsonify({"ok": True, "races": []})

    try:
        with db.engine.connect() as conn:
            races = conn.execute(
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
                               WHERE re.race_id = r.key
                                 AND bc.sailor = :sailor_id
                                                     ) THEN TRUE ELSE FALSE END AS joined,
                                                     CASE WHEN r.status = 'finished' OR EXISTS (
                                                             SELECT 1
                                                             FROM "RACINGAPP"."RACE_ENTRY" re2
                                                             JOIN "RACINGAPP"."BOATCONTROL" bc2 ON bc2.key = re2.boatkey
                                                             JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re2.key
                                                             WHERE re2.race_id = r.key
                                                                 AND bc2.sailor = :sailor_id
                                                     ) THEN TRUE ELSE FALSE END AS results_available
                    FROM "RACINGAPP"."RACE" r
                    JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                    WHERE r.club = :club_id
                                            AND r.status IN ('not_started', 'active')
                                            AND r.started_at IS NOT NULL
                                            AND r.started_at < (NOW() + INTERVAL '7 day')
                                            AND (r.status = 'active' OR r.started_at >= NOW())
                                        ORDER BY r.started_at ASC, r.key ASC
                '''),
                {"club_id": club_id, "sailor_id": sailor_id}
            ).mappings().all()

        return jsonify({"ok": True, "races": [dict(r) for r in races]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/mobile/races/<int:race_id>/join")
def api_mobile_join_race(race_id):
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id or not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    boat_key = payload.get("boat_key")
    if not boat_key:
        return jsonify({"ok": False, "error": "boat_key is required"}), 400

    try:
        with db.engine.begin() as conn:
            race_row = conn.execute(
                text('''
                    SELECT key, status, started_at
                    FROM "RACINGAPP"."RACE"
                    WHERE key = :race_id
                      AND club = :club_id
                '''),
                {"race_id": race_id, "club_id": club_id}
            ).mappings().first()

            if not race_row:
                return jsonify({"ok": False, "error": "Race not found"}), 404
            if race_row["status"] == "finished":
                return jsonify({"ok": False, "error": "Race already finished"}), 409
            if not race_row["started_at"]:
                return jsonify({"ok": False, "error": "Race has no scheduled date/time"}), 409

            now_ts = datetime.now()
            latest_join_time = now_ts + timedelta(days=7)
            if not (now_ts <= race_row["started_at"] < latest_join_time):
                return jsonify({"ok": False, "error": "Race is not open for entry (outside next 7 days)"}), 409

            boat_row = conn.execute(
                text('''
                    SELECT bc.key AS boat_key,
                           bc.sail_number,
                           hc.boat,
                           hc.handicap,
                           sc.fullname
                    FROM "RACINGAPP"."BOATCONTROL" bc
                    JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON hc.key = bc.boat
                    JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
                    WHERE bc.key = :boat_key
                      AND bc.sailor = :sailor_id
                      AND sc.club = :club_id
                '''),
                {"boat_key": boat_key, "sailor_id": sailor_id, "club_id": club_id}
            ).mappings().first()

            if not boat_row:
                return jsonify({"ok": False, "error": "Boat not found for sailor"}), 404

            existing = conn.execute(
                text('SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id AND boatkey = :boat_key'),
                {"race_id": race_id, "boat_key": boat_key}
            ).scalar()
            if existing:
                return jsonify({"ok": True, "joined": True, "message": "Already joined"})

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

        return jsonify({"ok": True, "joined": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/mobile/races/<int:race_id>/results")
def api_mobile_race_results(race_id):
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id or not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            race_exists = conn.execute(
                text('SELECT 1 FROM "RACINGAPP"."RACE" WHERE key = :race_id AND club = :club_id'),
                {"race_id": race_id, "club_id": club_id}
            ).scalar()
            if not race_exists:
                return jsonify({"ok": False, "error": "Race not found"}), 404

            my_results = conn.execute(
                text('''
                    SELECT re.key AS entry_id,
                           re.sailor,
                           re.boat,
                           re.sail_number,
                           MAX(CASE WHEN l.is_finish THEN l.position END) AS position,
                           MAX(CASE WHEN l.is_finish THEN l.elapsed_sec END) AS elapsed_sec,
                           MAX(CASE WHEN l.is_finish THEN l.corrected_sec END) AS corrected_sec
                    FROM "RACINGAPP"."RACE_ENTRY" re
                    JOIN "RACINGAPP"."BOATCONTROL" bc ON bc.key = re.boatkey
                    LEFT JOIN "RACINGAPP"."LAP" l ON l.race_entry_id = re.key
                    WHERE re.race_id = :race_id
                      AND bc.sailor = :sailor_id
                    GROUP BY re.key, re.sailor, re.boat, re.sail_number
                    ORDER BY position ASC NULLS LAST, corrected_sec ASC NULLS LAST
                '''),
                {"race_id": race_id, "sailor_id": sailor_id}
            ).mappings().all()

            leaderboard = conn.execute(
                text('''
                    SELECT re.sailor,
                           re.boat,
                           re.sail_number,
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

        def secs_to_hms(s):
            if s is None:
                return None
            s = int(s)
            return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

        return jsonify({
            "ok": True,
            "my_results": [
                {
                    "entry_id": r["entry_id"],
                    "sailor": r["sailor"],
                    "boat": r["boat"],
                    "sail_number": r["sail_number"],
                    "position": r["position"],
                    "elapsed_time": secs_to_hms(r["elapsed_sec"]),
                    "corrected_time": secs_to_hms(r["corrected_sec"])
                }
                for r in my_results
            ],
            "leaderboard": [
                {
                    "sailor": r["sailor"],
                    "boat": r["boat"],
                    "sail_number": r["sail_number"],
                    "position": r["position"],
                    "corrected_time": secs_to_hms(r["corrected_sec"])
                }
                for r in leaderboard
            ]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/landing")
def landing_page():
    club_id = session.get("club_id")
    club_name = session.get("club_name")
    if not club_id:
        return redirect("/login")
    return render_template("landing.html", clubName=club_name, username=session.get("username"))


@app.get("/members")
def members_page():
    if not session.get("club_id"):
        return redirect("/login")
    return render_template("members.html", clubName=session.get("club_name"))


@app.get("/api/members")
def api_get_members():
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
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

        members = {}
        for r in rows:
            sid = str(r["sailor_id"])
            if sid not in members:
                members[sid] = {
                    "id": r["sailor_id"],
                    "full_name": r["fullname"],
                    "first_name": r["firstname"],
                    "last_name": r["lastname"],
                    "boats": []
                }
            if r["boat_key"] is not None:
                members[sid]["boats"].append({
                    "boat_key": r["boat_key"],
                    "boat": r["boat_name"],
                    "sail_number": r["sail_number"],
                    "handicap": r["handicap"]
                })

        return jsonify({"ok": True, "members": list(members.values())})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/members")
def api_create_member():
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    if not first_name:
        return jsonify({"ok": False, "error": "first_name is required"}), 400

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            sailor_id = conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."SAILORCONTROL"
                    (key, fullname, firstname, lastname, club)
                    VALUES (nextval('key'), :fullname, :firstname, :lastname, :club)
                    RETURNING key
                '''),
                {
                    "fullname": full_name,
                    "firstname": first_name,
                    "lastname": last_name or None,
                    "club": club_id
                }
            ).scalar()

        return jsonify({"ok": True, "member_id": sailor_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.put("/api/members/<int:member_id>")
def api_update_member(member_id):
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    if not first_name:
        return jsonify({"ok": False, "error": "first_name is required"}), 400

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            updated = conn.execute(
                text('''
                    UPDATE "RACINGAPP"."SAILORCONTROL"
                    SET fullname = :fullname,
                        firstname = :firstname,
                        lastname = :lastname
                    WHERE key = :member_id
                      AND club = :club_id
                '''),
                {
                    "fullname": full_name,
                    "firstname": first_name,
                    "lastname": last_name or None,
                    "member_id": member_id,
                    "club_id": club_id
                }
            )

        if updated.rowcount == 0:
            return jsonify({"ok": False, "error": "Member not found"}), 404

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/boats/catalog")
def api_boat_catalog():
    if not session.get("club_id"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text('''
                    SELECT DISTINCT ON (hc.boat)
                           hc.key,
                           hc.boat,
                           hc.handicap
                    FROM "RACINGAPP"."HANDICAPCONTROL" hc
                    ORDER BY hc.boat, hc.date DESC, hc.key DESC
                ''')
            ).mappings().all()

        boats = [{"key": r["key"], "boat": r["boat"], "handicap": r["handicap"]} for r in rows]
        return jsonify({"ok": True, "boats": boats})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/members/<int:member_id>/boats")
def api_assign_boat(member_id):
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    handicap_key = payload.get("handicap_key")
    sail_number = (payload.get("sail_number") or "").strip()
    if not handicap_key or not sail_number:
        return jsonify({"ok": False, "error": "handicap_key and sail_number are required"}), 400

    try:
        with db.engine.begin() as conn:
            sailor_exists = conn.execute(
                text('SELECT 1 FROM "RACINGAPP"."SAILORCONTROL" WHERE key = :member_id AND club = :club_id'),
                {"member_id": member_id, "club_id": club_id}
            ).scalar()

            if not sailor_exists:
                return jsonify({"ok": False, "error": "Member not found"}), 404

            boat_key = conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number)
                    VALUES (nextval('key'), :boat, :sailor, :sail_number)
                    RETURNING key
                '''),
                {"boat": handicap_key, "sailor": member_id, "sail_number": sail_number}
            ).scalar()

        return jsonify({"ok": True, "boat_key": boat_key})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/series")
def series_page():
    if not session.get("club_id"):
        return redirect("/login")
    return render_template("series.html", clubName=session.get("club_name"))


@app.get("/api/series/manage")
def api_series_manage_list():
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text('''
                    SELECT s.key,
                           s.year,
                           s.name,
                           COALESCE(r.total_races, 0) AS total_races,
                           r.next_race_at,
                           r.last_race_at
                    FROM "RACINGAPP"."SERIESCONTROL" s
                    LEFT JOIN (
                        SELECT series,
                               COUNT(*) AS total_races,
                               MIN(started_at) FILTER (WHERE started_at >= NOW()) AS next_race_at,
                               MAX(started_at) AS last_race_at
                        FROM "RACINGAPP"."RACE"
                        GROUP BY series
                    ) r ON r.series = s.key
                    WHERE s.club = :club_id
                    ORDER BY s.year DESC NULLS LAST, s.name ASC
                '''),
                {"club_id": club_id}
            ).mappings().all()

        return jsonify({"ok": True, "series": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/series/manage")
def api_series_manage_create():
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    year = (payload.get("year") or "").strip()
    name = (payload.get("name") or "").strip()
    race_count = int(payload.get("race_count") or 0)
    day_of_week = (payload.get("day_of_week") or "Saturday").strip().lower()
    start_hour = int(payload.get("start_hour") or 11)
    start_minute = int(payload.get("start_minute") or 0)
    races_per_day = int(payload.get("races_per_day") or 1)
    start_date_raw = (payload.get("start_date") or "").strip()

    if not name:
        return jsonify({"ok": False, "error": "Series name is required"}), 400
    if not year:
        return jsonify({"ok": False, "error": "Series year is required"}), 400
    if race_count <= 0:
        return jsonify({"ok": False, "error": "race_count must be greater than 0"}), 400
    if races_per_day <= 0:
        return jsonify({"ok": False, "error": "races_per_day must be greater than 0"}), 400
    if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
        return jsonify({"ok": False, "error": "Invalid start time"}), 400

    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    target_weekday = weekday_map.get(day_of_week)
    if target_weekday is None:
        return jsonify({"ok": False, "error": "Invalid day_of_week"}), 400

    try:
        if start_date_raw:
            base_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        else:
            base_date = datetime.now().date()
    except Exception:
        return jsonify({"ok": False, "error": "start_date must be YYYY-MM-DD"}), 400

    try:
        with db.engine.begin() as conn:
            exists = conn.execute(
                text('''
                    SELECT 1
                    FROM "RACINGAPP"."SERIESCONTROL"
                    WHERE club = :club_id
                      AND LOWER(name) = LOWER(:name)
                      AND year = :year
                '''),
                {"club_id": club_id, "name": name, "year": year}
            ).scalar()

            if exists:
                return jsonify({"ok": False, "error": "Series already exists for this club/year"}), 409

            series_id = conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."SERIESCONTROL" (key, year, name, club)
                    VALUES (nextval('key'), :year, :name, :club)
                    RETURNING key
                '''),
                {"year": year, "name": name, "club": club_id}
            ).scalar()

            max_race_no = conn.execute(
                text('SELECT COALESCE(MAX(race_no), 0) FROM "RACINGAPP"."RACE" WHERE series = :series_id'),
                {"series_id": series_id}
            ).scalar() or 0

            # Build schedule: e.g. Saturdays 11:00 with optional multiple races/day.
            days_to_add = (target_weekday - base_date.weekday()) % 7
            next_race_date = base_date + timedelta(days=days_to_add)

            created = 0
            race_no = int(max_race_no)
            while created < race_count:
                for slot in range(races_per_day):
                    if created >= race_count:
                        break

                    race_no += 1
                    slot_minutes = slot * 10
                    scheduled_at = datetime.combine(
                        next_race_date,
                        time(hour=start_hour, minute=start_minute)
                    ) + timedelta(minutes=slot_minutes)

                    conn.execute(
                        text('''
                            INSERT INTO "RACINGAPP"."RACE" (key, club, series, race_no, status, started_at, ended_at)
                            VALUES (nextval('key'), :club, :series, :race_no, 'not_started', :started_at, NULL)
                        '''),
                        {
                            "club": club_id,
                            "series": series_id,
                            "race_no": race_no,
                            "started_at": scheduled_at
                        }
                    )
                    created += 1

                next_race_date = next_race_date + timedelta(days=7)

        return jsonify({"ok": True, "series_id": series_id, "scheduled_races": race_count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.put("/api/series/manage/<int:series_id>")
def api_series_manage_update(series_id):
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    year = (payload.get("year") or "").strip()
    name = (payload.get("name") or "").strip()

    if not name:
        return jsonify({"ok": False, "error": "Series name is required"}), 400
    if not year:
        return jsonify({"ok": False, "error": "Series year is required"}), 400

    try:
        with db.engine.begin() as conn:
            updated = conn.execute(
                text('''
                    UPDATE "RACINGAPP"."SERIESCONTROL"
                    SET year = :year,
                        name = :name
                    WHERE key = :series_id
                      AND club = :club_id
                '''),
                {"year": year, "name": name, "series_id": series_id, "club_id": club_id}
            )

        if updated.rowcount == 0:
            return jsonify({"ok": False, "error": "Series not found"}), 404

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/club_entry")
def club_entry():
    # Entry setup is now behind login; club comes from session
    club_id = session.get("club_id")
    if not club_id:
        return redirect("/login")

    # Clear pending race setup when starting a new entry flow
    session.pop("race", None)
    race_data = session.get("race", {})
    race_data["club_id"] = str(club_id)
    session["race"] = race_data
    return render_template("club_entry.html", clubId=str(club_id), clubName=session.get("club_name"))

@app.route("/sailor_entry")
def sailor_entry():
    clubId = request.args.get('clubName') or session.get("club_id")
    seriesId = request.args.get('seriesName')
    raceId = request.args.get('raceId')
    if not clubId:
        return redirect("/login")
    session['club_id'] = clubId
    session['series_id'] = seriesId  # Store series_id in session
    race_data = session.get("race", {})
    race_data["club_id"] = clubId
    race_data["series_id"] = seriesId
    if raceId:
        race_data["race_id"] = raceId
    session["race"] = race_data
    # Boat list not strictly needed for race now (entries come from sessionStorage),
    # but we pass it anyway in case you want it later.
    return render_template("sailor_entry.html", clubId=clubId, raceId=raceId or race_data.get("race_id"))


@app.get("/api/clubs")
def api_get_club():
    clubcontrol = ClubControl.query.with_entities(ClubControl.name, ClubControl.key).all()
    clubs = [{"id": b.key, "name": b.name} for b in clubcontrol]
    return jsonify(clubs=clubs)


@app.get("/api/series/<club_id>")
def api_get_series(club_id):
    seriescontrol = SeriesControl.query.with_entities(SeriesControl.name, SeriesControl.key).filter_by(club=club_id)
    series = [{"id": b.key, "name": b.name} for b in seriescontrol]
    return jsonify(series=series)


@app.get("/api/races/upcoming/<club_id>")
def api_get_upcoming_races_for_club(club_id):
    """Return the next available race in each active series for a club."""
    if not session.get("club_id"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    # Guard: club admins can only query their own club
    if str(session.get("club_id")) != str(club_id):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text('''
                    WITH ranked AS (
                        SELECT r.key AS race_id,
                               r.series AS series_id,
                               r.race_no,
                               r.started_at,
                               r.status,
                               sc.name AS series_name,
                               ROW_NUMBER() OVER (
                                   PARTITION BY r.series
                                   ORDER BY r.started_at ASC, r.key ASC
                               ) AS rn
                        FROM "RACINGAPP"."RACE" r
                        JOIN "RACINGAPP"."SERIESCONTROL" sc ON sc.key = r.series
                        WHERE r.club = :club_id
                          AND r.status = 'not_started'
                          AND r.started_at IS NOT NULL
                          AND r.started_at >= NOW()
                    )
                    SELECT race_id, series_id, race_no, started_at, status, series_name
                    FROM ranked
                    WHERE rn = 1
                    ORDER BY started_at ASC, race_id ASC
                '''),
                {"club_id": club_id}
            ).mappings().all()

        return jsonify({"ok": True, "races": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/races/<int:race_id>/entries")
def api_get_race_entries(race_id):
    """Return entry table rows for a specific race (web club flow)."""
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            race_ok = conn.execute(
                text('''
                    SELECT 1
                    FROM "RACINGAPP"."RACE"
                    WHERE key = :race_id
                      AND club = :club_id
                    LIMIT 1
                '''),
                {"race_id": race_id, "club_id": club_id}
            ).scalar()
            if not race_ok:
                return jsonify({"ok": False, "error": "Race not found"}), 404

            rows = conn.execute(
                text('''
                    SELECT re.boatkey AS key,
                           re.sailor,
                           re.boat,
                           re.sail_number AS "sailNumber",
                           re.handicap
                    FROM "RACINGAPP"."RACE_ENTRY" re
                    WHERE re.race_id = :race_id
                    ORDER BY re.key ASC
                '''),
                {"race_id": race_id}
            ).mappings().all()

        return jsonify({"ok": True, "entries": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/name/<club_id>")
def api_get_sailorname(club_id):
    sailorcontrol = SailorControl.query.with_entities(SailorControl.fullname, SailorControl.key).filter_by(club=club_id)
    names = [{"id": b.key, "name": b.fullname} for b in sailorcontrol]
    return jsonify(names=names)

@app.get("/api/boat/<sailor_id>")
def api_get_boat(sailor_id):
    boatcontrol = BoatControl.query\
        .join(Boats, BoatControl.boat==Boats.key).with_entities(Boats.boat, BoatControl.key, BoatControl.sail_number, Boats.handicap).filter(BoatControl.sailor==sailor_id)
    boats = [{"id": {"key":b.key, "sailNumber":b.sail_number, "boat":b.boat, "handicap":b.handicap}, "name": b.boat +" "+ b.sail_number} for b in boatcontrol]
    return jsonify(boats=boats)


@app.post("/api/entries")
def api_entries():
    payload = request.get_json(silent=True) or {}
    entries = payload.get("entries") or []
    # Basic validation
    cleaned = []
    for e in entries:
        sailor = (e.get("sailor") or "").strip()
        boat = (e.get("boat") or "").strip()
        sailnum = (e.get("sailNumber") or "").strip()
        handicap = (e.get("handicap") or "").strip()
        key = (e.get("key") or "").strip()
        entry_id = e.get("entry_id")
        if sailor and boat and sailnum:
            cleaned_entry = {"sailor": sailor, "boat": boat, "sailNumber": sailnum, "handicap": handicap, "key": key}
            if entry_id:
                cleaned_entry["entry_id"] = entry_id
            cleaned.append(cleaned_entry)

    if not cleaned:
        return jsonify({"ok": False, "error": "No valid entries provided"}), 400

    # Store in session for the next step (swap to DB later if you prefer)
    race_data = session.get('race', {})
    race_data['entries'] = cleaned
    session['race'] = race_data
    return jsonify({"ok": True, "count": len(cleaned)})

@app.post("/api/set_club_series")
def api_set_club_series():
    payload = request.get_json(silent=True) or {}
    club_id = payload.get("club_id") or session.get("club_id")
    series_id = payload.get("series_id")
    race_id = payload.get("race_id")
    if not club_id or not series_id:
        return jsonify({"ok": False, "error": "Missing club_id or series_id"}), 400
    session["club_id"] = club_id
    session["series_id"] = series_id
    race_data = session.get("race", {})
    race_data["club_id"] = club_id
    race_data["series_id"] = series_id
    if race_id:
        race_data["race_id"] = race_id
    session["race"] = race_data
    return jsonify({"ok": True})

@app.get("/api/session/attributes")
def api_get_session_attributes():
    """Retrieve session attributes in one response"""
    # Normalize /session attributes under a consistent tree
    race_data = session.get("race", {})
    attributes = {
        "club_id": race_data.get("club_id") or session.get("club_id"),
        "series_id": race_data.get("series_id") or session.get("series_id"),
        "entries": race_data.get("entries") or session.get("entries", []),
        "race_id": race_data.get("race_id"),
        "race_no": race_data.get("race_no"),
        "status": race_data.get("status", "not_started")
    }

    if not attributes["entries"]:
        return jsonify({"ok": False, "error": "No entries in session"}), 400

    return jsonify({"ok": True, "attributes": attributes})


@app.get("/entry_sailor")
def entry_sailor():
    """Render the sailor entry page"""
    club_id = request.args.get("club_id", 1)  # Default to club 1, adjust as needed
    return render_template("sailor_entry.html", clubId=club_id)


@app.get("/entry_summary")
def entry_summary_page():
    """Render the entry summary page"""
    if not session.get("club_id"):
        return redirect("/login")
    return render_template("entry_summary.html")

@app.route("/test_race")
def test_race():
    """Load test entries and redirect to race control"""
    with db.engine.connect() as conn:
        club_id = conn.execute(
            text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = :name LIMIT 1'),
            {"name": "Test Club"}
        ).scalar()
        series_id = conn.execute(
            text('SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = :name LIMIT 1'),
            {"name": "Test Series"}
        ).scalar()
        rows = conn.execute(
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
        ).mappings().all() if club_id else []

    session['race'] = {
        'club_id': str(club_id) if club_id is not None else 'Test Club',
        'series_id': str(series_id) if series_id is not None else 'Test Series',
        'entries': [
            {
                'key': str(row['boatkey']),
                'boat': row['boat'],
                'sailor': row['sailor'],
                'handicap': row['handicap'],
                'sailNumber': row['sail_number']
            }
            for row in rows
        ] or [
            {'key': '1', 'boat': 'Laser 1', 'sailor': 'John Doe', 'handicap': 1100, 'sailNumber': '123'},
            {'key': '2', 'boat': 'Laser 2', 'sailor': 'Jane Smith', 'handicap': 1120, 'sailNumber': '456'},
            {'key': '3', 'boat': 'Laser 3', 'sailor': 'Bob Johnson', 'handicap': 1080, 'sailNumber': '789'}
        ],
        'status': 'not_started'
    }
    return redirect("/race_control")

@app.get("/race_control")
def race_control_page():
    """Render the race control page"""
    if not session.get("club_id"):
        return redirect("/login")
    return render_template("race_control.html")


@app.post("/api/races/start")
def api_start_race():
    payload = request.get_json(silent=True) or {}
    race_data = session.get("race", {})
    club_id = payload.get("club_id") or race_data.get("club_id") or session.get("club_id")
    series_id = payload.get("series_id") or race_data.get("series_id") or session.get("series_id")
    selected_race_id = payload.get("race_id") or race_data.get("race_id")
    entries = payload.get("entries") or race_data.get("entries") or []

    if not club_id or not series_id:
        return jsonify({"ok": False, "error": "Missing club_id or series_id"}), 400
    if not entries:
        return jsonify({"ok": False, "error": "No entries provided"}), 400

    if race_data.get("race_id") and race_data.get("status") == "active":
        return jsonify({
            "ok": True,
            "race_id": race_data.get("race_id"),
            "race_no": race_data.get("race_no"),
            "entries": race_data.get("entries", [])
        })

    race_id = None
    race_no = None
    persisted_entries = []

    try:
        with db.engine.begin() as conn:
            if selected_race_id:
                selected = conn.execute(
                    text('''
                        SELECT key, race_no, status
                        FROM "RACINGAPP"."RACE"
                        WHERE key = :race_id
                          AND club = :club_id
                          AND series = :series_id
                        LIMIT 1
                    '''),
                    {"race_id": selected_race_id, "club_id": club_id, "series_id": series_id}
                ).mappings().first()

                if not selected:
                    return jsonify({"ok": False, "error": "Selected race not found for this club/series"}), 404
                if selected["status"] == "finished":
                    return jsonify({"ok": False, "error": "Selected race is already finished"}), 409

                race_id = selected["key"]
                race_no = selected["race_no"]

                conn.execute(
                    text('''
                        UPDATE "RACINGAPP"."RACE"
                        SET status = 'active',
                            started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                        WHERE key = :race_id
                    '''),
                    {"race_id": race_id}
                )

                # Reset any existing entries for this selected race before saving new entry list
                conn.execute(
                    text('DELETE FROM "RACINGAPP"."RACE_ENTRY" WHERE race_id = :race_id'),
                    {"race_id": race_id}
                )
            else:
                race_no = conn.execute(
                    text('SELECT COALESCE(MAX(race_no), 0) + 1 FROM "RACINGAPP"."RACE" WHERE series = :series'),
                    {"series": series_id}
                ).scalar()

                race_id = conn.execute(
                    text('''
                        INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at)
                        VALUES (:club, :series, :race_no, :status, CURRENT_TIMESTAMP)
                        RETURNING key
                    '''),
                    {"club": club_id, "series": series_id, "race_no": race_no, "status": "active"}
                ).scalar()

            for entry in entries:
                # Resolve and validate boatkey (must be bigint in RACE_ENTRY)
                raw_boatkey = entry.get("key")
                boatkey = None
                if raw_boatkey not in (None, ""):
                    try:
                        boatkey = int(raw_boatkey)
                    except (TypeError, ValueError):
                        boatkey = None

                # Fallback resolve by sailor + sail number (+ club when available)
                if boatkey is None:
                    club_id_int = None
                    try:
                        club_id_int = int(club_id)
                    except (TypeError, ValueError):
                        club_id_int = None

                    boatkey = conn.execute(
                        text('''
                            SELECT bc.key
                            FROM "RACINGAPP"."BOATCONTROL" bc
                            JOIN "RACINGAPP"."SAILORCONTROL" sc ON sc.key = bc.sailor
                            WHERE sc.fullname = :sailor
                              AND bc.sail_number = :sail_number
                              AND (:club_id IS NULL OR sc.club = :club_id)
                            ORDER BY bc.key DESC
                            LIMIT 1
                        '''),
                        {
                            "sailor": entry.get("sailor"),
                            "sail_number": entry.get("sailNumber"),
                            "club_id": club_id_int
                        }
                    ).scalar()

                if boatkey is None:
                    return jsonify({
                        "ok": False,
                        "error": f"Missing/invalid boat key for entry: {entry.get('sailor', 'unknown')} ({entry.get('sailNumber', 'no sail #')}). Re-add this sailor/boat from the entry screen.",
                        "race_id": race_id,
                        "race_no": race_no,
                        "entries": persisted_entries
                    }), 400

                handicap_raw = entry.get("handicap")
                handicap = None
                if handicap_raw not in (None, "", "N/A"):
                    try:
                        handicap = int(float(handicap_raw))
                    except (TypeError, ValueError):
                        handicap = None

                entry_id = conn.execute(
                    text('''
                        INSERT INTO "RACINGAPP"."RACE_ENTRY" (race_id, boatkey, sailor, boat, sail_number, handicap)
                        VALUES (:race_id, :boatkey, :sailor, :boat, :sail_number, :handicap)
                        RETURNING key
                    '''),
                    {
                        "race_id": race_id,
                        "boatkey": boatkey,
                        "sailor": entry.get("sailor"),
                        "boat": entry.get("boat"),
                        "sail_number": entry.get("sailNumber"),
                        "handicap": handicap
                    }
                ).scalar()

                persisted_entry = dict(entry)
                persisted_entry["entry_id"] = entry_id
                persisted_entries.append(persisted_entry)

        race_data.update({
            "club_id": str(club_id),
            "series_id": str(series_id),
            "race_id": race_id,
            "race_no": race_no,
            "status": "active",
            "entries": persisted_entries
        })
        session["race"] = race_data

        return jsonify({"ok": True, "race_id": race_id, "race_no": race_no, "entries": persisted_entries})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "race_id": race_id, "race_no": race_no, "entries": persisted_entries}), 500


@app.post("/api/races/<int:race_id>/lap")
def api_record_race_lap(race_id):
    payload = request.get_json(silent=True) or {}
    entry_id = payload.get("entry_id")
    lap_number = payload.get("lap_number")
    elapsed_time = payload.get("elapsed_time")
    corrected_time = payload.get("corrected_time")
    position = payload.get("position")
    is_finish = bool(payload.get("is_finish", False))

    if not all([entry_id, lap_number, elapsed_time]):
        return jsonify({"ok": False, "error": "Missing required lap fields"}), 400

    try:
        elapsed_sec = parse_hms_to_seconds(elapsed_time)
        corrected_sec = parse_hms_to_seconds(corrected_time) if corrected_time and corrected_time != "N/A" else None

        with db.engine.begin() as conn:
            entry_exists = conn.execute(
                text('SELECT 1 FROM "RACINGAPP"."RACE_ENTRY" WHERE key = :entry_id AND race_id = :race_id'),
                {"entry_id": entry_id, "race_id": race_id}
            ).scalar()

            if not entry_exists:
                return jsonify({"ok": False, "error": "Race entry not found"}), 404

            conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."LAP" (race_entry_id, lap_number, is_finish, elapsed_sec, corrected_sec, position)
                    VALUES (:race_entry_id, :lap_number, :is_finish, :elapsed_sec, :corrected_sec, :position)
                '''),
                {
                    "race_entry_id": entry_id,
                    "lap_number": lap_number,
                    "is_finish": is_finish,
                    "elapsed_sec": elapsed_sec,
                    "corrected_sec": corrected_sec,
                    "position": position
                }
            )

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/races/<int:race_id>/finish")
def api_finish_race(race_id):
    try:
        with db.engine.begin() as conn:
            updated = conn.execute(
                text('''
                    UPDATE "RACINGAPP"."RACE"
                    SET status = :status,
                        ended_at = CURRENT_TIMESTAMP
                    WHERE key = :race_id
                '''),
                {"status": "finished", "race_id": race_id}
            )

        if updated.rowcount == 0:
            return jsonify({"ok": False, "error": "Race not found"}), 404

        race_data = session.get("race", {})
        if race_data.get("race_id") == race_id:
            race_data["status"] = "finished"
            session["race"] = race_data

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/race_summary")
def race_summary_page():
    """Render the race summary page"""
    return render_template("race_summary.html")


@app.get("/api/races/<int:race_id>/summary")
def api_race_summary(race_id):
    """Return full race summary: metadata + results per entry"""
    try:
        with db.engine.connect() as conn:
            race_row = conn.execute(
                text('''
                    SELECT r.race_no, r.started_at, r.ended_at, r.status,
                           cc.name AS club_name, sc.name AS series_name
                    FROM "RACINGAPP"."RACE" r
                    JOIN "RACINGAPP"."CLUBCONTROL" cc ON r.club = cc.key
                    JOIN "RACINGAPP"."SERIESCONTROL" sc ON r.series = sc.key
                    WHERE r.key = :race_id
                '''),
                {"race_id": race_id}
            ).mappings().first()

            if not race_row:
                return jsonify({"ok": False, "error": "Race not found"}), 404

            results_rows = conn.execute(
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

        def secs_to_hms(s):
            if s is None:
                return None
            s = int(s)
            return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

        started_at = race_row["started_at"]
        ended_at   = race_row["ended_at"]
        duration_sec = int((ended_at - started_at).total_seconds()) if started_at and ended_at else None

        race_info = {
            "race_no":     race_row["race_no"],
            "club_name":   race_row["club_name"],
            "series_name": race_row["series_name"],
            "started_at":  started_at.strftime("%H:%M:%S") if started_at else None,
            "date":        started_at.strftime("%d %B %Y") if started_at else None,
            "duration":    secs_to_hms(duration_sec),
        }

        results = [
            {
                "entry_id":      row["entry_id"],
                "sailor":        row["sailor"],
                "boat":          row["boat"],
                "sail_number":   row["sail_number"],
                "handicap":      row["handicap"],
                "lap_count":     int(row["lap_count"]) if row["lap_count"] else 0,
                "elapsed_time":  secs_to_hms(row["final_elapsed_sec"]),
                "corrected_time":secs_to_hms(row["final_corrected_sec"]),
                "position":      row["final_position"],
                "dnf":           row["final_position"] is None,
            }
            for row in results_rows
        ]

        return jsonify({"ok": True, "race": race_info, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Bind on 0.0.0.0 for container support; call via http://localhost:5000 from host
    # Disable reloader to prevent random ephemeral ports in some launchers
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)