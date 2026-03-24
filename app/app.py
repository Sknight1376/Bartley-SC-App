from flask import Flask, render_template, jsonify, request, session, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


from handicaps.calculations import handicap_calculations
from handicaps.conversions import time_conversions




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

# Reflected RACEMASTER
class RaceMaster(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.RACEMASTER"]

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

# >>> SET THIS to your real sequence name (schema/case sensitive)
# Example: '"RACINGAPP"."KEY"'
KEYUENCE = '"RACINGAPP"."key"'




handicaps = Boats.query.all()


# ---------- helpers ----------

def parse_hms_to_time(s: str):
    """Parse HH:MM:SS or H:MM:SS into python datetime.time."""
    s = (s or "").strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid time string: {s}")
    h, m, sec = [int(x) for x in parts]
    return datetime.strptime(f"{h:02d}:{m:02d}:{sec:02d}", "%H:%M:%S").time()



# ---------- routes ----------

@app.route("/")
def club_entry():
    # Clear any pending entries when returning to club entry page
    # This ensures entries are reset if user changes club/series
    session.pop("pending_entries", None)
    return render_template("club_entry.html")

@app.route("/sailor_entry")
def sailor_entry():
    clubId = request.args.get('clubName')
    seriesId = request.args.get('seriesName')
    session['club_id'] = clubId
    session['series_id'] = seriesId  # Store series_id in session
    # Boat list not strictly needed for race now (entries come from sessionStorage),
    # but we pass it anyway in case you want it later.
    return render_template("sailor_entry.html", clubId=clubId)


# @app.route("/summary")
# def summary():
#     # ... your existing code ...
#     pending = session.get("pending_entries", [])
#     # You can pass 'pending' to the template for display if you want
#     return render_template("summary.html",
#                            start=start, end=end, duration=duration,
#                            entry_count=entry_count, results=results,
#                            club_name=club_name, series_name=series_name, race=race_no,
#                            pending=pending)

@app.route("/race")
def race():
    # Boat list not strictly needed for race now (entries come from sessionStorage),
    # but we pass it anyway in case you want it later.
    all_boats = Boats.query.with_entities(Boats.boat, Boats.key).all()
    return render_template("Race.html", boatarray=[(b.boat, b.key) for b in all_boats])

@app.route('/times', methods=['POST'])
def times():
    boat_id = request.form.get('boat_id', type=int)
    elapsed_time = request.form.get('elapsed')
    split = request.form.get('split')
    club_name = request.form.get('club_name', "")
    series_name = request.form.get('series_name', "")
    race_no = request.form.get('race', type=int)

    # Safety checks
    if not boat_id or not elapsed_time or not split:
        return jsonify({"error": "Missing boat_id / elapsed / split"}), 400
    if not club_name or not series_name or race_no is None:
        return jsonify({"error": "Missing club_name / series_name / race"}), 400

    # Resolve club + series IDs
    with db.engine.begin() as conn:
        club_id = conn.execute(
            text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name=:n'),
            {"n": club_name}
        ).scalar()

        if not club_id:
            club_id = conn.execute(
                text('INSERT INTO "RACINGAPP"."CLUBCONTROL"(name) VALUES (:n) RETURNING key'),
                {"n": club_name}
            ).scalar()

        series_id = conn.execute(
            text('SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name=:n'),
            {"n": series_name}
        ).scalar()

        if not series_id:
            series_id = conn.execute(
                text('INSERT INTO "RACINGAPP"."SERIESCONTROL"(name) VALUES (:n) RETURNING key'),
                {"n": series_name}
            ).scalar()

        # handicap lookup
        matches = [c.handicap for c in handicaps if c.key == boat_id]
        if not matches:
            return jsonify({"error": "No handicap for boat"}), 400

        handicap = matches[0]
        corrected_str = handicap_calculations.corrected_time(elapsed_time, handicap)
        corrected_seconds = time_conversions.tosecs(corrected_str)

        # Prepare time fields
        recorded_time = parse_hms_to_time(elapsed_time)
        corrected_time = parse_hms_to_time(corrected_str)
        split_time = parse_hms_to_time(split)


        # Insert race master record
        conn.execute(
            text('''
                INSERT INTO "RACINGAPP"."RACEMASTER"
                ( boatkey, club, series, race, recorded_time, corrected_time, time)
                VALUES (:boatkey, :club, :series, :race, :recorded, :corrected, :t)
            '''),
            {
                "boatkey": boat_id,
                "club": club_id,
                "series": series_id,
                "race": race_no,
                "recorded": recorded_time,
                "corrected": corrected_time,
                "t": split_time
            }
        )

        conn.commit()

    return jsonify({
        "corrected_time": corrected_str,
        "seconds": corrected_seconds
    })

# @app.route("/summary")
# def summary():
#     start = request.args.get("start", "")
#     end = request.args.get("end", "")
#     club_name = request.args.get("club_name", "")
#     series_name = request.args.get("series_name", "")
#     race_no = request.args.get("race", type=int)

#     if not club_name or not series_name or race_no is None:
#         return render_template("summary.html",
#                                start=start, end=end, duration="",
#                                entry_count=0, results=[],
#                                club_name=club_name, series_name=series_name, race=race_no)

#     club_id = get_or_create_club_id(club_name)
#     series_id = get_or_create_series_id(series_name)
#     with db.engine.connect() as conn:
#         entry_count = conn.execute(
#             text("""
#             SELECT COUNT(DISTINCT boatkey)
#             FROM "RACINGAPP"."RACEMASTER"
#             WHERE club = :club AND series = :series AND race = :race
#             """),
#             {"club": club_id, "series": series_id, "race": race_no}
#         ).scalar() or 0

#         # Final per boat = latest inserted record (max key) for that boat in this race
#         results = conn.execute(
#             text("""
#             WITH final AS (
#                 SELECT DISTINCT ON (boatkey)
#                 key, boatkey, recorded_time, corrected_time, time
#                 FROM "RACINGAPP"."RACEMASTER"
#                 WHERE club = :club AND series = :series AND race = :race
#                 ORDER BY boatkey, key DESC
#             )
#             SELECT *
#             FROM final
#             ORDER BY corrected_time ASC NULLS LAST
#             """),
#             {"club": club_id, "series": series_id, "race": race_no}
#         ).fetchall()

#     duration = ""
#     try:
#       if start and end:
#         dt0 = datetime.fromisoformat(start.replace("Z", "+00:00"))
#         dt1 = datetime.fromisoformat(end.replace("Z", "+00:00"))
#         duration = str(dt1 - dt0)
#     except Exception:
#       duration = ""

#     return render_template("summary.html",
#                            start=start, end=end, duration=duration,
#                            entry_count=entry_count, results=results,
#                            club_name=club_name, series_name=series_name, race=race_no)




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
        if sailor and boat and sailnum:
            cleaned.append({"sailor": sailor, "boat": boat, "sailNumber": sailnum, "handicap": handicap, "key": key})

    if not cleaned:
        return jsonify({"ok": False, "error": "No valid entries provided"}), 400

    # Store in session for the next step (swap to DB later if you prefer)
    session["pending_entries"] = cleaned
    return jsonify({"ok": True, "count": len(cleaned)})

@app.get("/api/session/club")
def api_get_session_club():
    """Retrieve club_id from session"""
    club_id = session.get("club_id")
    if not club_id:
        return jsonify({"ok": False, "error": "No club in session"}), 400
    return jsonify({"ok": True, "club_id": club_id})



@app.get("/api/session/series")
def api_get_session_series():
    """Retrieve series_id from session"""
    series_id = session.get("series_id")
    if not series_id:
        return jsonify({"ok": False, "error": "No series in session"}), 400
    return jsonify({"ok": True, "series_id": series_id})

@app.get("/api/session/entries")
def api_get_session_entries():
    """Retrieve entries from session"""
    entries = session.get("pending_entries", [])
    if not entries:
        return jsonify({"ok": False, "error": "No entries in session"}), 400
    return jsonify({"ok": True, "entries": entries})


@app.get("/entry_sailor")
def entry_sailor():
    """Render the sailor entry page"""
    club_id = request.args.get("club_id", 1)  # Default to club 1, adjust as needed
    return render_template("sailor_entry.html", clubId=club_id)


@app.get("/entry_summary")
def entry_summary_page():
    """Render the entry summary page"""
    return render_template("entry_summary.html")

# @app.route("/test_race")
# def test_race():
#     """Load test entries and redirect to race control"""
#     session['club'] = 'Test Club'
#     session['series'] = 'Test Series'
#     session['entries'] = [
#         {'key': '1', 'boat': 'Laser 1', 'sailor': 'John Doe', 'handicap': 1100},
#         {'key': '2', 'boat': 'Laser 2', 'sailor': 'Jane Smith', 'handicap': 1120},
#         {'key': '3', 'boat': 'Laser 3', 'sailor': 'Bob Johnson', 'handicap': 1080}
#     ]
#     return redirect("/race_control")

@app.get("/race_control")
def race_control_page():
    """Render the race control page"""
    entries = session.get('entries', [])
    club = session.get('club', '')
    series = session.get('series', '')
    return render_template("race_control.html", entries=entries, club=club, series=series)


@app.get("/api/next_race/<series_id>")
def api_get_next_race(series_id):
    try:
        with db.engine.connect() as conn:
            result = conn.execute(
                text('SELECT MAX(race) FROM "RACINGAPP"."RACEMASTER" WHERE series = :series'),
                {"series": series_id}
            ).scalar()
            next_race = (result or 0) + 1
            return jsonify({"next_race": next_race})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/log_race_time")
def api_log_race_time():
    payload = request.get_json(silent=True) or {}
    boatkey = payload.get("boatkey")
    elapsed_time = payload.get("elapsed_time")  # HH:MM:SS
    corrected_time = payload.get("corrected_time")  # HH:MM:SS
    club_id = payload.get("club_id")
    series_id = payload.get("series_id")
    race_no = payload.get("race_no")
    is_finish = payload.get("is_finish", False)

    if not all([boatkey, elapsed_time, corrected_time, club_id, series_id, race_no]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        recorded_time = parse_hms_to_time(elapsed_time)
        corrected_time_parsed = parse_hms_to_time(corrected_time)
        split_time = recorded_time  # Assuming split is the elapsed for now

        with db.engine.begin() as conn:
            conn.execute(
                text('''
                    INSERT INTO "RACINGAPP"."RACEMASTER"
                    ( boatkey, club, series, race, recorded_time, corrected_time, time)
                    VALUES (:boatkey, :club, :series, :race, :recorded, :corrected, :t)
                '''),
                {
                    "boatkey": boatkey,
                    "club": club_id,
                    "series": series_id,
                    "race": race_no,
                    "recorded": recorded_time,
                    "corrected": corrected_time_parsed,
                    "t": split_time
                }
            )

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Bind on 0.0.0.0 for container support; call via http://localhost:5000 from host
    # Disable reloader to prevent random ephemeral ports in some launchers
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)