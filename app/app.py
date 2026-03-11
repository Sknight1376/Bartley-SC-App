from flask import Flask, render_template, jsonify, request
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


from handicaps.calculations import handicap_calculations
from handicaps.conversions import time_conversions


import hashlib
import re

def normalise(name) -> str:
    name = "" if name is None else str(name)
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    return name

def create_key(name: str) -> int:
    norm = normalise(name)
    digest = hashlib.sha256(norm.encode("utf-8")).digest()
    key64 = int.from_bytes(digest[:8], "big", signed=False)
    return key64 & ((1 << 63) - 1)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dwh:DBTTEST@db:5432/dwh"
app.app_context().push()
db = SQLAlchemy(app)

db.Model.metadata.reflect(db.engine, schema='RACINGAPP')

class Boats(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.HANDICAPCONTROL"]

# Reflected RACEMASTER
class RaceMaster(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.RACEMASTER"]

# Reflected RACEMASTER
class ClubControl(db.Model):
    __table__ = db.metadata.tables["RACINGAPP.CLUBCONTROL"]

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


def get_or_create_club_id(club_name: str) -> int:
    club_name = normalise(club_name)
    if not club_name:
        raise ValueError("Empty club_name")

    stmt = text("""
        INSERT INTO "RACINGAPP"."CLUBCONTROL" (name)
        VALUES (:name)
        RETURNING key
    """)

    with db.engine.begin() as conn:
        return int(conn.execute(stmt, {"name": club_name}).scalar())


def get_or_create_series_id(series_name: str, club: str | None = None) -> int:
    series_name = normalise(series_name)
    club = normalise(club) if club else None

   

    # Assumes you added: UNIQUE (year, name)
    stmt = text("""
        INSERT INTO "RACINGAPP"."SERIESCONTROL" (name, club)
        VALUES (:name, :club)
        RETURNING key
    """)

    with db.engine.begin() as conn:
        return int(conn.execute(stmt, {"name": series_name, "club": club}).scalar())


# ---------- routes ----------

@app.route("/")
def index():
    all_boats = Boats.query.with_entities(Boats.boat, Boats.key).all()
    return render_template("index.html", boatarray=[(b.boat, b.key) for b in all_boats])

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
                "series": '1',
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

@app.route("/summary")
def summary():
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    club_name = request.args.get("club_name", "")
    series_name = request.args.get("series_name", "")
    race_no = request.args.get("race", type=int)

    if not club_name or not series_name or race_no is None:
        return render_template("summary.html",
                               start=start, end=end, duration="",
                               entry_count=0, results=[],
                               club_name=club_name, series_name=series_name, race=race_no)

    club_id = get_or_create_club_id(club_name)
    series_id = get_or_create_series_id(series_name)
    with db.engine.connect() as conn:
        entry_count = conn.execute(
            text("""
            SELECT COUNT(DISTINCT boatkey)
            FROM "RACINGAPP"."RACEMASTER"
            WHERE club = :club AND series = :series AND race = :race
            """),
            {"club": club_id, "series": series_id, "race": race_no}
        ).scalar() or 0

        # Final per boat = latest inserted record (max key) for that boat in this race
        results = conn.execute(
            text("""
            WITH final AS (
                SELECT DISTINCT ON (boatkey)
                key, boatkey, recorded_time, corrected_time, time
                FROM "RACINGAPP"."RACEMASTER"
                WHERE club = :club AND series = :series AND race = :race
                ORDER BY boatkey, key DESC
            )
            SELECT *
            FROM final
            ORDER BY corrected_time ASC NULLS LAST
            """),
            {"club": club_id, "series": series_id, "race": race_no}
        ).fetchall()

    duration = ""
    try:
      if start and end:
        dt0 = datetime.fromisoformat(start.replace("Z", "+00:00"))
        dt1 = datetime.fromisoformat(end.replace("Z", "+00:00"))
        duration = str(dt1 - dt0)
    except Exception:
      duration = ""

    return render_template("summary.html",
                           start=start, end=end, duration=duration,
                           entry_count=entry_count, results=results,
                           club_name=club_name, series_name=series_name, race=race_no)




@app.get("/api/clubs")
def api_get_clubs():
    sql = text('SELECT name FROM "RACINGAPP"."CLUBCONTROL" ORDER BY name')
    with db.engine.begin() as conn:
        rows = conn.execute(sql).fetchall()
    return jsonify({"clubs": [r[0] for r in rows]})



@app.post("/api/clubs")
def api_upsert_club():
    data = request.get_json(silent=True) or {}

    # IMPORTANT: keep as STRING here
    club_name = normalise(data.get("club_name", ""))
    if not club_name:
        return jsonify({"error": "club_name is required"}), 400

    # Deterministic bigint hash key from the name
    key = create_key(club_name)

    with db.engine.begin() as conn:
        # If club already exists by name, return its key
        existing = conn.execute(
            text('SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = :n'),
            {"n": club_name}
        ).scalar()

        if existing is not None:
            return jsonify({"key": int(existing), "club_name": club_name, "created": False})

        # Try insert using hash key
        try:
            conn.execute(
                text('INSERT INTO "RACINGAPP"."CLUBCONTROL"(key, name) VALUES (:k, :n)'),
                {"k": key, "n": club_name}
            )
            return jsonify({"key": key, "club_name": club_name, "created": True})

        except Exception:
            # Potential hash collision: key already exists for different club_name
            other = conn.execute(
                text('SELECT club_name FROM "RACINGAPP"."CLUBCONTROL" WHERE key = :k'),
                {"k": key}
            ).scalar()

            if other and other != club_name:
                return jsonify({
                    "error": "Hash collision: generated key already exists for a different club",
                    "existing_club_name": other
                }), 409

            raise



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)