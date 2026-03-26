from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dwh:DBTTEST@db:5432/dwh"
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



# ---------- routes ----------

@app.route("/")
def club_entry():
    # Clear any pending entries when returning to club entry page
    # This ensures entries are reset if user changes club/series
    session.pop("race", None)
    session.pop("club_id", None)
    session.pop("series_id", None)
    return render_template("club_entry.html")

@app.route("/sailor_entry")
def sailor_entry():
    clubId = request.args.get('clubName')
    seriesId = request.args.get('seriesName')
    session['club_id'] = clubId
    session['series_id'] = seriesId  # Store series_id in session
    race_data = session.get("race", {})
    race_data["club_id"] = clubId
    race_data["series_id"] = seriesId
    session["race"] = race_data
    # Boat list not strictly needed for race now (entries come from sessionStorage),
    # but we pass it anyway in case you want it later.
    return render_template("sailor_entry.html", clubId=clubId)


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
    club_id = payload.get("club_id")
    series_id = payload.get("series_id")
    if not club_id or not series_id:
        return jsonify({"ok": False, "error": "Missing club_id or series_id"}), 400
    session["club_id"] = club_id
    session["series_id"] = series_id
    race_data = session.get("race", {})
    race_data["club_id"] = club_id
    race_data["series_id"] = series_id
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
    return render_template("race_control.html")


@app.post("/api/races/start")
def api_start_race():
    payload = request.get_json(silent=True) or {}
    race_data = session.get("race", {})
    club_id = payload.get("club_id") or race_data.get("club_id") or session.get("club_id")
    series_id = payload.get("series_id") or race_data.get("series_id") or session.get("series_id")
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