from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta, time, date
import json

from services.permissions import (
    club_user_has_role as permission_club_user_has_role,
    sailor_has_active_role as permission_sailor_has_active_role,
    sailor_has_race_duty as permission_sailor_has_race_duty,
    sailor_can_access_race_control as permission_sailor_can_access_race_control,
)
from admin_api import (
    decide_handicap_recommendation,
    get_race_audit,
    get_race_revisions,
    health_check,
)
from mobile_api import (
    build_control_access_response,
    mobile_boat_classes,
    mobile_boats,
    mobile_clubs,
    mobile_control_entries,
    mobile_control_summary,
    mobile_control_upcoming_races,
    mobile_create_boat,
    mobile_dashboard,
    mobile_delete_boat,
    mobile_join_race,
    mobile_login,
    mobile_me,
    mobile_race_results,
    mobile_register,
    mobile_series,
    mobile_series_standings,
    mobile_upcoming_races,
    mobile_update_me,
)
from members_api import (
    members_assign_boat,
    members_boat_catalog,
    members_create,
    members_list,
    members_update,
)
from series_management import (
    create_exception,
    create_series_basic,
    create_series_rule,
    create_series_with_schedule,
    delete_exception,
    delete_rule,
    generate_series_schedule,
    get_scoring,
    get_series,
    list_exceptions,
    list_series,
    list_series_races_view,
    list_series_rules,
    save_scoring,
    update_exception,
    update_rule,
    update_series_metadata,
)
from race_control import (
    add_race_entry,
    delete_race_lap,
    edit_race_lap,
    lock_results,
    mobile_control_finish,
    mobile_control_lap,
    mobile_control_start,
    remove_race_entry,
    unlock_results,
    web_finish_race,
    web_record_lap,
)
from retrospective import (
    create_retrospective_race,
    list_retrospective_races,
    preview_retrospective_results,
    publish_race_results,
    save_retrospective_draft,
)
from duties import (
    assign_race_duty,
    assign_race_duty_by_date,
    delete_race_duty,
    list_race_duties,
)




app = Flask(__name__)
# Connect to local PostgreSQL (Windows) instead of Docker
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dwh:DBTTEST@localhost:5432/dwh"
# Do not enforce SERVER_NAME in this environment; allow host and port to be set via run() parameters
# app.config['SERVER_NAME'] = "localhost:5000"
app.app_context().push()
db = SQLAlchemy(app)
app.secret_key = "4001376"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
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
    session.permanent = True          # cookie lives for PERMANENT_SESSION_LIFETIME (24 h)
    session["sailor_user_id"] = str(sailor_user_id)
    session["sailor_id"] = str(sailor_id)
    session["sailor_username"] = username
    if club_id is None:
        session.pop("sailor_club_id", None)
    else:
        session["sailor_club_id"] = str(club_id)


def grant_club_role(conn, club_user_id, club_id, role_code, granted_by=None):
    role_id = conn.execute(
        text('SELECT key FROM "RACINGAPP"."ROLE" WHERE code = :code LIMIT 1'),
        {"code": role_code}
    ).scalar()
    if not role_id:
        return

    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."CLUB_USER_ROLE" (key, club_user, club, role, granted_by, is_active)
            VALUES (nextval('key'), :club_user, :club, :role, :granted_by, TRUE)
            ON CONFLICT (club_user, club, role)
            DO UPDATE SET is_active = TRUE,
                          granted_by = COALESCE(EXCLUDED.granted_by, "RACINGAPP"."CLUB_USER_ROLE".granted_by),
                          granted_at = CURRENT_TIMESTAMP
        '''),
        {
            "club_user": club_user_id,
            "club": club_id,
            "role": role_id,
            "granted_by": granted_by,
        }
    )


def grant_sailor_role(conn, sailor_user_id, sailor_id, club_id, role_code, granted_by=None, grant_reason=None):
    role_id = conn.execute(
        text('SELECT key FROM "RACINGAPP"."ROLE" WHERE code = :code LIMIT 1'),
        {"code": role_code}
    ).scalar()
    if not role_id:
        return

    existing = conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."SAILOR_ROLE_GRANT"
            WHERE sailor_user = :sailor_user
              AND sailor = :sailor
              AND role = :role
            LIMIT 1
        '''),
        {
            "sailor_user": sailor_user_id,
            "sailor": sailor_id,
            "role": role_id,
        }
    ).scalar()

    if existing:
        conn.execute(
            text('''
                UPDATE "RACINGAPP"."SAILOR_ROLE_GRANT"
                SET is_active = TRUE,
                    club = :club,
                    granted_by = COALESCE(:granted_by, granted_by),
                    grant_reason = COALESCE(:grant_reason, grant_reason),
                    granted_at = CURRENT_TIMESTAMP
                WHERE key = :key
            '''),
            {
                "key": existing,
                "club": club_id,
                "granted_by": granted_by,
                "grant_reason": grant_reason,
            }
        )
        return

    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."SAILOR_ROLE_GRANT"
            (key, sailor_user, sailor, club, role, granted_by, grant_reason, is_active)
            VALUES (nextval('key'), :sailor_user, :sailor, :club, :role, :granted_by, :grant_reason, TRUE)
        '''),
        {
            "sailor_user": sailor_user_id,
            "sailor": sailor_id,
            "club": club_id,
            "role": role_id,
            "granted_by": granted_by,
            "grant_reason": grant_reason,
        }
    )


def club_user_has_role(conn, club_user_id, club_id, role_code):
    return permission_club_user_has_role(conn, club_user_id, club_id, role_code)


def sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, role_code):
    return permission_sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, role_code)


def sailor_has_race_duty(conn, race_id, sailor_id, duty_code):
    return permission_sailor_has_race_duty(conn, race_id, sailor_id, duty_code)


def sailor_can_access_race_control(conn, sailor_user_id, sailor_id, club_id, race_id):
    return permission_sailor_can_access_race_control(conn, sailor_user_id, sailor_id, club_id, race_id)


def require_mobile_race_control_access(race_id):
    sailor_user_id = session.get("sailor_user_id")
    sailor_id = session.get("sailor_id")
    club_id = session.get("sailor_club_id")

    if not sailor_user_id or not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.begin() as conn:
            if not club_id:
                club_id = conn.execute(
                    text('''
                        SELECT club
                        FROM "RACINGAPP"."SAILORCONTROL"
                        WHERE key = :sailor_id
                        LIMIT 1
                    '''),
                    {"sailor_id": sailor_id}
                ).scalar()
                if club_id:
                    session["sailor_club_id"] = str(club_id)

            if not club_id:
                return jsonify({"ok": False, "error": "No club assigned for sailor"}), 403

            allowed = sailor_can_access_race_control(conn, sailor_user_id, sailor_id, club_id, race_id)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    if not allowed:
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    return None


def require_club_admin(redirect_to_login=False):
    club_user_id = session.get("user_id")
    club_id = session.get("club_id")

    if not club_user_id or not club_id:
        if redirect_to_login:
            return redirect("/login")
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            allowed = club_user_has_role(conn, club_user_id, club_id, "club_admin")
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    if not allowed:
        if redirect_to_login:
            return redirect("/login")
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    return None


def require_club_admin_or_race_officer(redirect_to_login=False):
    club_user_id = session.get("user_id")
    club_id = session.get("club_id")

    if not club_user_id or not club_id:
        if redirect_to_login:
            return redirect("/login")
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        with db.engine.connect() as conn:
            is_admin = club_user_has_role(conn, club_user_id, club_id, "club_admin")
            is_race_officer = club_user_has_role(conn, club_user_id, club_id, "race_officer")
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    if not (is_admin or is_race_officer):
        if redirect_to_login:
            return redirect("/login")
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    return None


def get_actor_context(mobile=False):
    if mobile:
        sailor_user_id = session.get("sailor_user_id")
        sailor_id = session.get("sailor_id")
        return {
            "actor_type": "sailor_user",
            "actor_user_id": int(sailor_user_id) if sailor_user_id not in (None, "", "null") else None,
            "actor_sailor_id": int(sailor_id) if sailor_id not in (None, "", "null") else None,
            "created_by_type": "sailor_user",
            "created_by_user": int(sailor_user_id) if sailor_user_id not in (None, "", "null") else None,
        }

    user_id = session.get("user_id")
    return {
        "actor_type": "club_user",
        "actor_user_id": int(user_id) if user_id not in (None, "", "null") else None,
        "actor_sailor_id": None,
        "created_by_type": "club_user",
        "created_by_user": int(user_id) if user_id not in (None, "", "null") else None,
    }


def race_is_locked(race_row):
    if not race_row:
        return False
    return race_row.get("results_status") == "locked" or race_row.get("results_locked_at") is not None


def get_race_state(conn, race_id, club_id=None):
    return conn.execute(
        text('''
            SELECT key, club, series, status, results_status, results_locked_at, source_mode
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
              AND (:club_id IS NULL OR club = :club_id)
            LIMIT 1
        '''),
        {
            "race_id": race_id,
            "club_id": int(club_id) if club_id not in (None, "", "null") else None,
        }
    ).mappings().first()


def _json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    return value


def build_race_snapshot(conn, race_id):
    race_row = conn.execute(
        text('''
            SELECT key,
                   club,
                   series,
                   race_no,
                   status,
                   results_status,
                   source_mode,
                   started_at,
                   ended_at,
                   results_locked_at,
                   results_locked_by
            FROM "RACINGAPP"."RACE"
            WHERE key = :race_id
            LIMIT 1
        '''),
        {"race_id": race_id}
    ).mappings().first()

    entries = conn.execute(
        text('''
            SELECT re.key,
                   re.race_id,
                   re.boatkey,
                   re.sailor,
                   re.boat,
                   re.sail_number,
                   re.handicap,
                   re.created_by_user,
                   re.created_by_type,
                   re.source,
                   re.revision_id
            FROM "RACINGAPP"."RACE_ENTRY" re
            WHERE re.race_id = :race_id
            ORDER BY re.key
        '''),
        {"race_id": race_id}
    ).mappings().all()

    laps = conn.execute(
        text('''
            SELECT l.key,
                   l.race_entry_id,
                   l.lap_number,
                   l.is_finish,
                   l.elapsed_sec,
                   l.corrected_sec,
                   l.position,
                   l.created_by_user,
                   l.created_by_type,
                   l.source,
                   l.revision_id
            FROM "RACINGAPP"."LAP" l
            JOIN "RACINGAPP"."RACE_ENTRY" re ON re.key = l.race_entry_id
            WHERE re.race_id = :race_id
            ORDER BY l.key
        '''),
        {"race_id": race_id}
    ).mappings().all()

    return {
        "race": {k: _json_safe(v) for k, v in (dict(race_row) if race_row else {}).items()},
        "entries": [{k: _json_safe(v) for k, v in dict(row).items()} for row in entries],
        "laps": [{k: _json_safe(v) for k, v in dict(row).items()} for row in laps],
    }


def create_race_revision(conn, race_id, actor, reason=None, status="draft", source_mode="live"):
    based_on_revision_id = conn.execute(
        text('''
            SELECT key
            FROM "RACINGAPP"."RACE_RESULT_REVISION"
            WHERE race_id = :race_id
            ORDER BY revision_no DESC
            LIMIT 1
        '''),
        {"race_id": race_id}
    ).scalar()

    next_revision_no = conn.execute(
        text('''
            SELECT COALESCE(MAX(revision_no), 0) + 1
            FROM "RACINGAPP"."RACE_RESULT_REVISION"
            WHERE race_id = :race_id
        '''),
        {"race_id": race_id}
    ).scalar()

    snapshot_json = json.dumps(build_race_snapshot(conn, race_id))

    revision_id = conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_RESULT_REVISION" (
                key,
                race_id,
                revision_no,
                status,
                source_mode,
                reason,
                created_by_user,
                created_by_type,
                based_on_revision_id,
                snapshot_json
            )
            VALUES (
                nextval('key'),
                :race_id,
                :revision_no,
                :status,
                :source_mode,
                :reason,
                :created_by_user,
                :created_by_type,
                :based_on_revision_id,
                CAST(:snapshot_json AS JSONB)
            )
            RETURNING key
        '''),
        {
            "race_id": race_id,
            "revision_no": next_revision_no,
            "status": status,
            "source_mode": source_mode,
            "reason": reason,
            "created_by_user": actor.get("created_by_user"),
            "created_by_type": actor.get("created_by_type"),
            "based_on_revision_id": based_on_revision_id,
            "snapshot_json": snapshot_json,
        }
    ).scalar()
    return revision_id


def resolve_role_id(conn, role_code):
    return conn.execute(
        text('SELECT key FROM "RACINGAPP"."ROLE" WHERE code = :code LIMIT 1'),
        {"code": role_code}
    ).scalar()


def upsert_race_duty_assignment(
    conn,
    race_id,
    sailor_id,
    sailor_user_id,
    role_id,
    duty_type,
    starts_at,
    ends_at,
    status,
    assigned_by,
    notes,
):
    return conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (
                key,
                race_id,
                sailor,
                sailor_user,
                role,
                duty_type,
                starts_at,
                ends_at,
                status,
                assigned_by,
                notes
            )
            VALUES (
                nextval('key'),
                :race_id,
                :sailor,
                :sailor_user,
                :role,
                :duty_type,
                :starts_at,
                :ends_at,
                :status,
                :assigned_by,
                :notes
            )
            ON CONFLICT (race_id, sailor, role)
            DO UPDATE SET
                sailor_user = EXCLUDED.sailor_user,
                duty_type = EXCLUDED.duty_type,
                starts_at = EXCLUDED.starts_at,
                ends_at = EXCLUDED.ends_at,
                status = EXCLUDED.status,
                assigned_by = EXCLUDED.assigned_by,
                notes = EXCLUDED.notes
            RETURNING key
        '''),
        {
            "race_id": race_id,
            "sailor": sailor_id,
            "sailor_user": sailor_user_id,
            "role": role_id,
            "duty_type": duty_type,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": status,
            "assigned_by": assigned_by,
            "notes": notes,
        }
    ).scalar()


def write_race_audit(
    conn,
    race_id,
    actor,
    entity_type,
    action,
    entity_id=None,
    reason=None,
    before_obj=None,
    after_obj=None,
    revision_id=None,
):
    before_json = json.dumps(before_obj) if before_obj is not None else None
    after_json = json.dumps(after_obj) if after_obj is not None else None

    conn.execute(
        text('''
            INSERT INTO "RACINGAPP"."RACE_RESULT_AUDIT" (
                key,
                race_id,
                revision_id,
                entity_type,
                entity_id,
                action,
                actor_type,
                actor_user_id,
                actor_sailor_id,
                reason,
                before_json,
                after_json
            )
            VALUES (
                nextval('key'),
                :race_id,
                :revision_id,
                :entity_type,
                :entity_id,
                :action,
                :actor_type,
                :actor_user_id,
                :actor_sailor_id,
                :reason,
                CAST(:before_json AS JSONB),
                CAST(:after_json AS JSONB)
            )
        '''),
        {
            "race_id": race_id,
            "revision_id": revision_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_type": actor.get("actor_type") or "unknown",
            "actor_user_id": actor.get("actor_user_id"),
            "actor_sailor_id": actor.get("actor_sailor_id"),
            "reason": reason,
            "before_json": before_json,
            "after_json": after_json,
        }
    )


def ensure_series_schedule_tables(conn):
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_RULE" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
            start_time TIME NOT NULL,
            cadence_weeks INTEGER NOT NULL DEFAULT 1 CHECK (cadence_weeks > 0),
            races_per_day INTEGER NOT NULL DEFAULT 1 CHECK (races_per_day > 0),
            target_race_count INTEGER NULL,
            extra_start_times TEXT NULL,
            slot_gap_minutes INTEGER NOT NULL DEFAULT 10 CHECK (slot_gap_minutes > 0),
            valid_from DATE NOT NULL,
            valid_to DATE NULL,
            anchor_date DATE NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_EXCEPTION" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            exception_type VARCHAR(16) NOT NULL CHECK (exception_type IN ('cancel', 'move', 'add')),
            exception_date DATE NULL,
            original_start_at TIMESTAMP NULL,
            override_start_at TIMESTAMP NULL,
            note TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_SCORING" (
            series BIGINT PRIMARY KEY REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            scoring_system VARCHAR(32) NOT NULL DEFAULT 'low_point',
            races_to_count INTEGER NULL,
            discard_after_races INTEGER NULL,
            discards_allowed INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS "RACINGAPP"."SERIES_SCORING_DISCARD" (
            key BIGINT PRIMARY KEY DEFAULT nextval('key'),
            series BIGINT NOT NULL REFERENCES "RACINGAPP"."SERIESCONTROL"(key) ON DELETE CASCADE,
            discard_count INTEGER NOT NULL CHECK (discard_count > 0),
            after_races INTEGER NOT NULL CHECK (after_races > 0),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series, discard_count)
        )
    '''))

    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_RULE"
        ADD COLUMN IF NOT EXISTS extra_start_times TEXT NULL
    '''))
    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_RULE"
        ADD COLUMN IF NOT EXISTS target_race_count INTEGER NULL
    '''))
    conn.execute(text('''
        ALTER TABLE "RACINGAPP"."SERIES_EXCEPTION"
        ADD COLUMN IF NOT EXISTS exception_date DATE NULL
    '''))

    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_rule_series
            ON "RACINGAPP"."SERIES_RULE" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_exception_series
            ON "RACINGAPP"."SERIES_EXCEPTION" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_series_scoring_discard_series
            ON "RACINGAPP"."SERIES_SCORING_DISCARD" (series)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_race_series_started
            ON "RACINGAPP"."RACE" (series, started_at)
    '''))


def parse_date_yyyy_mm_dd(value, field_name):
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"{field_name} must be YYYY-MM-DD")


def parse_time_hh_mm(value, field_name):
    raw = (value or "").strip()
    try:
        return datetime.strptime(raw, "%H:%M").time()
    except Exception:
        raise ValueError(f"{field_name} must be HH:MM (24h)")


def parse_time_list_hh_mm(value, field_name):
    if value is None:
        return []

    if isinstance(value, list):
        raw_items = value
    else:
        raw_text = str(value).strip()
        if not raw_text:
            return []
        raw_items = raw_text.split(',')

    parsed = []
    for idx, item in enumerate(raw_items):
        t = parse_time_hh_mm(str(item).strip(), f"{field_name}[{idx}]")
        parsed.append(t)
    return parsed


def parse_iso_datetime(value, field_name):
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1]
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        raise ValueError(f"{field_name} must be ISO datetime")


def parse_weekday(value):
    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        raise ValueError("weekday must be between 0 and 6")

    raw = (value or "").strip().lower()
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6
    }
    if raw in weekday_map:
        return weekday_map[raw]
    raise ValueError("weekday must be 0..6 or weekday name")


def calculate_rule_end_date(valid_from, weekday, cadence_weeks, races_per_day, target_race_count):
    if target_race_count is None or target_race_count <= 0:
        return None

    days_to_add = (weekday - valid_from.weekday()) % 7
    current = valid_from + timedelta(days=days_to_add)
    remaining = int(target_race_count)

    while True:
        remaining -= min(races_per_day, remaining)
        if remaining <= 0:
            return current
        current = current + timedelta(days=7 * cadence_weeks)


def calculate_rule_end_date_with_exceptions(valid_from, weekday, cadence_weeks, races_per_day, target_race_count, excluded_dates):
    if target_race_count is None or target_race_count <= 0:
        return None

    excluded_set = set(excluded_dates or [])
    days_to_add = (weekday - valid_from.weekday()) % 7
    current = valid_from + timedelta(days=days_to_add)
    remaining = int(target_race_count)

    while True:
        if current not in excluded_set:
            remaining -= min(races_per_day, remaining)
            if remaining <= 0:
                return current
        current = current + timedelta(days=7 * cadence_weeks)


def recompute_series_rule_end_dates(conn, series_id):
    rules = conn.execute(
        text('''
            SELECT key, weekday, cadence_weeks, races_per_day, target_race_count, valid_from
            FROM "RACINGAPP"."SERIES_RULE"
            WHERE series = :series_id
              AND is_active = TRUE
              AND target_race_count IS NOT NULL
              AND target_race_count > 0
        '''),
        {"series_id": series_id}
    ).mappings().all()

    exception_rows = conn.execute(
        text('''
            SELECT COALESCE(exception_date, DATE(original_start_at)) AS exception_date
            FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE series = :series_id
              AND is_active = TRUE
              AND exception_type = 'cancel'
        '''),
        {"series_id": series_id}
    ).mappings().all()

    excluded_dates = [r["exception_date"] for r in exception_rows if r.get("exception_date")]

    for rule in rules:
        new_valid_to = calculate_rule_end_date_with_exceptions(
            valid_from=rule["valid_from"],
            weekday=int(rule["weekday"]),
            cadence_weeks=int(rule["cadence_weeks"]),
            races_per_day=int(rule["races_per_day"]),
            target_race_count=int(rule["target_race_count"]),
            excluded_dates=excluded_dates,
        )
        if new_valid_to:
            conn.execute(
                text('''
                    UPDATE "RACINGAPP"."SERIES_RULE"
                    SET valid_to = :valid_to,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE key = :rule_id
                '''),
                {"valid_to": new_valid_to, "rule_id": rule["key"]}
            )


def check_series_access(conn, series_id, club_id):
    return conn.execute(
        text('''
            SELECT 1
            FROM "RACINGAPP"."SERIESCONTROL"
            WHERE key = :series_id
              AND club = :club_id
            LIMIT 1
        '''),
        {"series_id": series_id, "club_id": club_id}
    ).scalar()


def generate_series_races(conn, series_id, club_id, from_date, to_date):
    ensure_series_schedule_tables(conn)

    rules = conn.execute(
        text('''
             SELECT key, weekday, start_time, cadence_weeks, races_per_day,
                 extra_start_times, slot_gap_minutes, valid_from, valid_to
            FROM "RACINGAPP"."SERIES_RULE"
            WHERE series = :series_id
              AND is_active = TRUE
              AND valid_from <= :to_date
              AND (valid_to IS NULL OR valid_to >= :from_date)
            ORDER BY key ASC
        '''),
        {"series_id": series_id, "from_date": from_date, "to_date": to_date}
    ).mappings().all()

    exceptions = conn.execute(
        text('''
                        SELECT exception_type, exception_date, original_start_at
            FROM "RACINGAPP"."SERIES_EXCEPTION"
            WHERE series = :series_id
              AND is_active = TRUE
            ORDER BY key ASC
        '''),
        {"series_id": series_id}
    ).mappings().all()

    planned = {}

    for rule in rules:
        weekday = int(rule["weekday"])
        cadence = int(rule["cadence_weeks"])
        races_per_day = int(rule["races_per_day"])
        start_time = rule["start_time"]
        cadence_anchor = rule["valid_from"]
        rule_start = max(rule["valid_from"], from_date)
        rule_end = min(rule["valid_to"] or to_date, to_date)
        extra_start_times = [s.strip() for s in (rule.get("extra_start_times") or "").split(",") if s and s.strip()]
        slot_gap = int(rule["slot_gap_minutes"])

        day_start_times = [start_time]
        if races_per_day > 1:
            if len(extra_start_times) >= races_per_day - 1:
                day_start_times.extend([
                    datetime.strptime(t, "%H:%M").time()
                    for t in extra_start_times[:races_per_day - 1]
                ])
            else:
                day_start_times.extend([
                    (datetime.combine(date.today(), start_time) + timedelta(minutes=slot_gap * slot)).time()
                    for slot in range(1, races_per_day)
                ])

        if rule_start > rule_end:
            continue

        first = rule_start + timedelta(days=(weekday - rule_start.weekday()) % 7)
        while ((first - cadence_anchor).days // 7) % cadence != 0:
            first = first + timedelta(days=7)

        current = first
        while current <= rule_end:
            for slot in range(races_per_day):
                started_at = datetime.combine(current, day_start_times[slot])
                planned[started_at] = True
            current = current + timedelta(days=7 * cadence)

    excluded_dates = set()
    for ex in exceptions:
        ex_date = ex["exception_date"]
        if not ex_date and ex.get("exception_type") == "cancel" and ex.get("original_start_at"):
            ex_date = ex["original_start_at"].date()
        if ex_date and from_date <= ex_date <= to_date:
            excluded_dates.add(ex_date)

    if excluded_dates:
        for dt_key in list(planned.keys()):
            if dt_key.date() in excluded_dates:
                planned.pop(dt_key, None)

    max_race_no = conn.execute(
        text('SELECT COALESCE(MAX(race_no), 0) FROM "RACINGAPP"."RACE" WHERE series = :series_id'),
        {"series_id": series_id}
    ).scalar() or 0

    inserted = 0
    skipped = 0
    for started_at in sorted(planned.keys()):
        exists = conn.execute(
            text('''
                SELECT 1
                FROM "RACINGAPP"."RACE"
                WHERE series = :series_id
                  AND started_at = :started_at
                LIMIT 1
            '''),
            {"series_id": series_id, "started_at": started_at}
        ).scalar()
        if exists:
            skipped += 1
            continue

        max_race_no += 1
        conn.execute(
            text('''
                INSERT INTO "RACINGAPP"."RACE" (key, club, series, race_no, status, started_at, ended_at)
                VALUES (nextval('key'), :club, :series, :race_no, 'not_started', :started_at, NULL)
            '''),
            {"club": club_id, "series": series_id, "race_no": max_race_no, "started_at": started_at}
        )
        inserted += 1

    return {
        "rule_count": len(rules),
        "planned_count": len(planned),
        "inserted_count": inserted,
        "skipped_count": skipped,
    }



# ---------- routes ----------

@app.route("/")
def intro_page():
    return render_template("intro.html")


@app.get("/api/health")
@app.get("/api/mobile/health")
def api_health():
    payload, status = health_check(db)
    return jsonify(payload), status


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
                grant_club_role(conn, user_row["user_id"], user_row["club_id"], "club_admin", user_row["user_id"])
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
    payload, status = mobile_login(
        db,
        request.get_json(silent=True) or {},
        grant_sailor_role,
        set_mobile_session,
    )
    return jsonify(payload), status


@app.post("/api/mobile/register")
def api_mobile_register():
    payload, status = mobile_register(
        db,
        request.get_json(silent=True) or {},
        grant_sailor_role,
        set_mobile_session,
    )
    return jsonify(payload), status


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
    payload, status = mobile_me(db, sailor_id, session.get("sailor_username"))
    return jsonify(payload), status


@app.put("/api/mobile/me")
def api_mobile_update_me():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_update_me(
        db, sailor_id, request.get_json(silent=True) or {}, session
    )
    return jsonify(payload), status


@app.get("/api/mobile/clubs")
def api_mobile_clubs():
    payload, status = mobile_clubs(db)
    return jsonify(payload), status


@app.get("/api/mobile/series")
def api_mobile_series():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_series(db, session.get("sailor_club_id"), sailor_id)
    return jsonify(payload), status


@app.get("/api/mobile/boats")
def api_mobile_boats():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_boats(db, sailor_id)
    return jsonify(payload), status


@app.get("/api/mobile/boat-classes")
def api_mobile_boat_classes():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_boat_classes(db)
    return jsonify(payload), status


@app.post("/api/mobile/boats")
def api_mobile_create_boat():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_create_boat(db, sailor_id, request.get_json(silent=True) or {})
    return jsonify(payload), status


@app.delete("/api/mobile/boats/<int:boat_key>")
def api_mobile_delete_boat(boat_key):
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_delete_boat(db, sailor_id, boat_key)
    return jsonify(payload), status


@app.get("/api/mobile/races/upcoming")
def api_mobile_upcoming_races():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_upcoming_races(db, session.get("sailor_club_id"), sailor_id)
    return jsonify(payload), status


@app.get("/api/mobile/dashboard")
def api_mobile_dashboard():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_dashboard(db, sailor_id, session)
    return jsonify(payload), status


@app.get("/api/mobile/series/standings")
def api_mobile_series_standings():
    sailor_id = session.get("sailor_id")
    if not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_series_standings(db, sailor_id, session)
    return jsonify(payload), status


@app.post("/api/mobile/races/<int:race_id>/join")
def api_mobile_join_race(race_id):
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id or not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_join_race(
        db, race_id, club_id, sailor_id, request.get_json(silent=True) or {}
    )
    return jsonify(payload), status


@app.get("/api/mobile/races/<int:race_id>/results")
def api_mobile_race_results(race_id):
    club_id = session.get("sailor_club_id")
    sailor_id = session.get("sailor_id")
    if not sailor_id or not club_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_race_results(db, race_id, club_id, sailor_id)
    return jsonify(payload), status


@app.get("/api/mobile/races/control/upcoming")
def api_mobile_control_upcoming_races():
    sailor_user_id = session.get("sailor_user_id")
    sailor_id = session.get("sailor_id")
    if not sailor_user_id or not sailor_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    payload, status = mobile_control_upcoming_races(
        db, sailor_user_id, sailor_id, session, sailor_has_active_role
    )
    return jsonify(payload), status


@app.get("/api/mobile/races/control/access")
def api_mobile_control_access():
    payload, status = build_control_access_response(db, session, sailor_has_active_role)
    return jsonify(payload), status


@app.get("/api/mobile/races/<int:race_id>/control-entries")
def api_mobile_control_entries(race_id):
    guard = require_mobile_race_control_access(race_id)
    if guard is not None:
        return guard

    payload, status = mobile_control_entries(db, race_id, session.get("sailor_club_id"))
    return jsonify(payload), status


@app.post("/api/mobile/races/<int:race_id>/control-start")
def api_mobile_control_start(race_id):
    guard = require_mobile_race_control_access(race_id)
    if guard is not None:
        return guard

    payload, status = mobile_control_start(
        db,
        race_id,
        session.get("sailor_club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=True),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/mobile/races/<int:race_id>/control-lap")
def api_mobile_control_lap(race_id):
    guard = require_mobile_race_control_access(race_id)
    if guard is not None:
        return guard

    payload, status = mobile_control_lap(
        db,
        race_id,
        session.get("sailor_club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=True),
        parse_hms_to_seconds,
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/mobile/races/<int:race_id>/control-finish")
def api_mobile_control_finish(race_id):
    guard = require_mobile_race_control_access(race_id)
    if guard is not None:
        return guard

    payload, status = mobile_control_finish(
        db,
        race_id,
        session.get("sailor_club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=True),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.get("/api/mobile/races/<int:race_id>/control-summary")
def api_mobile_control_summary(race_id):
    guard = require_mobile_race_control_access(race_id)
    if guard is not None:
        return guard
    payload, status = mobile_control_summary(db, race_id, session.get("sailor_club_id"))
    return jsonify(payload), status


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
    payload, status = members_list(db, session.get("club_id"))
    return jsonify(payload), status


@app.post("/api/members")
def api_create_member():
    guard = require_club_admin()
    if guard is not None:
        return guard
    payload, status = members_create(
        db,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    return jsonify(payload), status


@app.put("/api/members/<int:member_id>")
def api_update_member(member_id):
    guard = require_club_admin()
    if guard is not None:
        return guard
    payload, status = members_update(
        db,
        member_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    return jsonify(payload), status


@app.get("/api/boats/catalog")
def api_boat_catalog():
    guard = require_club_admin()
    if guard is not None:
        return guard
    payload, status = members_boat_catalog(db)
    return jsonify(payload), status


@app.post("/api/members/<int:member_id>/boats")
def api_assign_boat(member_id):
    guard = require_club_admin()
    if guard is not None:
        return guard
    payload, status = members_assign_boat(
        db,
        member_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    return jsonify(payload), status


@app.get("/series")
def series_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template("series.html", clubName=session.get("club_name"))


def get_active_series_setup_id():
    query_series_id = request.args.get("series_id", type=int)
    if query_series_id:
        session["series_setup_id"] = query_series_id
        return query_series_id

    stored_series_id = session.get("series_setup_id")
    try:
        return int(stored_series_id) if stored_series_id is not None else None
    except Exception:
        session.pop("series_setup_id", None)
        return None


@app.get("/series/new")
def series_new_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return redirect("/series/new/start")


@app.get("/series/new/start")
def series_new_start_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template(
        "series_new_start.html",
        clubName=session.get("club_name"),
        currentSeriesId=get_active_series_setup_id(),
    )


@app.post("/api/series/manage/setup/clear")
def api_series_manage_setup_clear():
    guard = require_club_admin()
    if guard is not None:
        return guard

    session.pop("series_setup_id", None)
    return jsonify({"ok": True})


@app.get("/series/new/name")
def series_new_name_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template(
        "series_new_name.html",
        clubName=session.get("club_name"),
        currentSeriesId=get_active_series_setup_id(),
    )


@app.get("/series/new/schedule")
def series_new_schedule_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template(
        "series_new_schedule.html",
        clubName=session.get("club_name"),
        currentSeriesId=get_active_series_setup_id(),
    )


@app.get("/series/new/scoring")
def series_new_scoring_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template(
        "series_new_scoring.html",
        clubName=session.get("club_name"),
        currentSeriesId=get_active_series_setup_id(),
    )


@app.get("/series/new/summary")
def series_new_summary_page():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard
    return render_template(
        "series_new_summary.html",
        clubName=session.get("club_name"),
        currentSeriesId=get_active_series_setup_id(),
    )


@app.post("/api/series/manage/basic")
def api_series_manage_create_basic():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = create_series_basic(
        db,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    if status == 200 and payload.get("ok") and payload.get("series_id"):
        session["series_setup_id"] = int(payload["series_id"])
    return jsonify(payload), status


@app.get("/api/series/manage")
def api_series_manage_list():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_series(db, session.get("club_id"))
    return jsonify(payload), status


@app.get("/api/series/manage/<int:series_id>")
def api_series_manage_get(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = get_series(db, series_id, session.get("club_id"))
    return jsonify(payload), status


@app.post("/api/series/manage")
def api_series_manage_create():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = create_series_with_schedule(
        db,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    return jsonify(payload), status


@app.put("/api/series/manage/<int:series_id>")
def api_series_manage_update(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = update_series_metadata(
        db,
        series_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
    )
    if status == 200 and payload.get("ok"):
        session["series_setup_id"] = int(series_id)
    return jsonify(payload), status


@app.get("/api/series/manage/<int:series_id>/rules")
def api_series_manage_rules_list(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_series_rules(
        db,
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
    )
    return jsonify(payload), status


@app.post("/api/series/manage/<int:series_id>/rules")
def api_series_manage_rules_create(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = create_series_rule(
        db,
        request.get_json(silent=True) or {},
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
        parse_weekday,
        parse_time_hh_mm,
        parse_time_list_hh_mm,
        parse_date_yyyy_mm_dd,
        calculate_rule_end_date,
        recompute_series_rule_end_dates,
    )
    return jsonify(payload), status


@app.put("/api/series/manage/<int:series_id>/rules/<int:rule_id>")
def api_series_manage_rules_update(series_id, rule_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = update_rule(
        db,
        request.get_json(silent=True) or {},
        series_id,
        rule_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
        parse_weekday,
        parse_time_hh_mm,
        parse_time_list_hh_mm,
        parse_date_yyyy_mm_dd,
        calculate_rule_end_date,
        recompute_series_rule_end_dates,
    )
    return jsonify(payload), status


@app.delete("/api/series/manage/<int:series_id>/rules/<int:rule_id>")
def api_series_manage_rules_delete(series_id, rule_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = delete_rule(
        db,
        series_id,
        rule_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
    )
    return jsonify(payload), status


@app.get("/api/series/manage/<int:series_id>/exceptions")
def api_series_manage_exceptions_list(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_exceptions(
        db,
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
    )
    return jsonify(payload), status


@app.post("/api/series/manage/<int:series_id>/exceptions")
def api_series_manage_exceptions_create(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = create_exception(
        db,
        request.get_json(silent=True) or {},
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
        parse_date_yyyy_mm_dd,
        recompute_series_rule_end_dates,
    )
    return jsonify(payload), status


@app.put("/api/series/manage/<int:series_id>/exceptions/<int:exception_id>")
def api_series_manage_exceptions_update(series_id, exception_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = update_exception(
        db,
        request.get_json(silent=True) or {},
        series_id,
        exception_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
        parse_date_yyyy_mm_dd,
        recompute_series_rule_end_dates,
    )
    return jsonify(payload), status


@app.delete("/api/series/manage/<int:series_id>/exceptions/<int:exception_id>")
def api_series_manage_exceptions_delete(series_id, exception_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = delete_exception(
        db,
        series_id,
        exception_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
        recompute_series_rule_end_dates,
    )
    return jsonify(payload), status


@app.get("/api/series/manage/<int:series_id>/scoring")
def api_series_manage_scoring_get(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = get_scoring(
        db,
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
    )
    return jsonify(payload), status


@app.post("/api/series/manage/<int:series_id>/scoring")
def api_series_manage_scoring_save(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = save_scoring(
        db,
        request.get_json(silent=True) or {},
        series_id,
        session.get("club_id"),
        ensure_series_schedule_tables,
        check_series_access,
    )
    return jsonify(payload), status


@app.post("/api/series/manage/<int:series_id>/generate")
def api_series_manage_generate(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = generate_series_schedule(
        db,
        request.get_json(silent=True) or {},
        series_id,
        session.get("club_id"),
        parse_date_yyyy_mm_dd,
        check_series_access,
        generate_series_races,
    )
    return jsonify(payload), status


@app.get("/api/series/manage/<int:series_id>/races")
def api_series_manage_races_list(series_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_series_races_view(
        db,
        series_id,
        session.get("club_id"),
        check_series_access,
    )
    return jsonify(payload), status


@app.get("/club_entry")
def club_entry():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard

    # Entry setup is now behind login; club comes from session
    club_id = session.get("club_id")

    # Clear pending race setup when starting a new entry flow
    session.pop("race", None)
    race_data = session.get("race", {})
    race_data["club_id"] = str(club_id)
    session["race"] = race_data
    return render_template("club_entry.html", clubId=str(club_id), clubName=session.get("club_name"))

@app.route("/sailor_entry")
def sailor_entry():
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard

    clubId = request.args.get('clubName') or session.get("club_id")
    seriesId = request.args.get('seriesName')
    raceId = request.args.get('raceId')
    if str(clubId) != str(session.get("club_id")):
        return redirect("/club_entry")
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
    guard = require_club_admin()
    if guard is not None:
        return guard

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
    guard = require_club_admin()
    if guard is not None:
        return guard

    club_id = session.get("club_id")

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
    guard = require_club_admin()
    if guard is not None:
        return guard

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
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload = request.get_json(silent=True) or {}
    club_id = payload.get("club_id") or session.get("club_id")
    series_id = payload.get("series_id")
    race_id = payload.get("race_id")
    if not club_id or not series_id:
        return jsonify({"ok": False, "error": "Missing club_id or series_id"}), 400
    if str(club_id) != str(session.get("club_id")):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
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
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard

    club_id = request.args.get("club_id") or session.get("club_id")
    return render_template("sailor_entry.html", clubId=club_id)


@app.get("/entry_summary")
def entry_summary_page():
    """Render the entry summary page"""
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard

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
    guard = require_club_admin(redirect_to_login=True)
    if guard is not None:
        return guard

    return render_template("race_control.html")


@app.post("/api/races/start")
def api_start_race():
    guard = require_club_admin()
    if guard is not None:
        return guard

    actor = get_actor_context(mobile=False)

    payload = request.get_json(silent=True) or {}
    race_data = session.get("race", {})
    club_id = payload.get("club_id") or race_data.get("club_id") or session.get("club_id")
    series_id = payload.get("series_id") or race_data.get("series_id") or session.get("series_id")
    selected_race_id = payload.get("race_id") or race_data.get("race_id")
    entries = payload.get("entries") or race_data.get("entries") or []
    source_mode = (payload.get("source_mode") or "live").strip().lower()
    if source_mode not in ("live", "retrospective"):
        source_mode = "live"
    reason = (payload.get("reason") or "Web race start").strip() or "Web race start"

    if not club_id or not series_id:
        return jsonify({"ok": False, "error": "Missing club_id or series_id"}), 400
    if str(club_id) != str(session.get("club_id")):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
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
    revision_id = None

    try:
        with db.engine.begin() as conn:
            if selected_race_id:
                selected = conn.execute(
                    text('''
                        SELECT key, race_no, status, results_status, results_locked_at
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
                if race_is_locked(selected):
                    return jsonify({"ok": False, "error": "Results are locked for this race"}), 409
                if selected["status"] == "finished":
                    return jsonify({"ok": False, "error": "Selected race is already finished"}), 409

                race_id = selected["key"]
                race_no = selected["race_no"]

                conn.execute(
                    text('''
                        UPDATE "RACINGAPP"."RACE"
                        SET status = 'active',
                            source_mode = :source_mode,
                            results_status = CASE WHEN results_status = 'locked' THEN results_status ELSE 'draft' END,
                            started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                        WHERE key = :race_id
                    '''),
                    {"race_id": race_id, "source_mode": source_mode}
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
                        INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at, source_mode, results_status)
                        VALUES (:club, :series, :race_no, :status, CURRENT_TIMESTAMP, :source_mode, 'draft')
                        RETURNING key
                    '''),
                    {
                        "club": club_id,
                        "series": series_id,
                        "race_no": race_no,
                        "status": "active",
                        "source_mode": source_mode,
                    }
                ).scalar()

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=source_mode,
            )

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
                        INSERT INTO "RACINGAPP"."RACE_ENTRY" (
                            race_id,
                            boatkey,
                            sailor,
                            boat,
                            sail_number,
                            handicap,
                            created_by_user,
                            created_by_type,
                            source,
                            revision_id
                        )
                        VALUES (
                            :race_id,
                            :boatkey,
                            :sailor,
                            :boat,
                            :sail_number,
                            :handicap,
                            :created_by_user,
                            :created_by_type,
                            :source,
                            :revision_id
                        )
                        RETURNING key
                    '''),
                    {
                        "race_id": race_id,
                        "boatkey": boatkey,
                        "sailor": entry.get("sailor"),
                        "boat": entry.get("boat"),
                        "sail_number": entry.get("sailNumber"),
                        "handicap": handicap,
                        "created_by_user": actor.get("created_by_user"),
                        "created_by_type": actor.get("created_by_type"),
                        "source": source_mode,
                        "revision_id": revision_id,
                    }
                ).scalar()

                persisted_entry = dict(entry)
                persisted_entry["entry_id"] = entry_id
                persisted_entries.append(persisted_entry)

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="race_started",
                reason=reason,
                after_obj={
                    "race_no": race_no,
                    "entry_count": len(persisted_entries),
                    "source_mode": source_mode,
                },
                revision_id=revision_id,
            )

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
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = web_record_lap(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        parse_hms_to_seconds,
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/entries")
def api_add_race_entry(race_id):
    guard = require_club_admin_or_race_officer()
    if guard is not None:
        return guard

    payload, status = add_race_entry(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.delete("/api/races/<int:race_id>/entries/<int:entry_id>")
def api_remove_race_entry(race_id, entry_id):
    guard = require_club_admin_or_race_officer()
    if guard is not None:
        return guard

    payload, status = remove_race_entry(
        db,
        race_id,
        entry_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.patch("/api/races/<int:race_id>/laps/<int:lap_id>")
def api_edit_race_lap(race_id, lap_id):
    guard = require_club_admin_or_race_officer()
    if guard is not None:
        return guard

    payload, status = edit_race_lap(
        db,
        race_id,
        lap_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        parse_hms_to_seconds,
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.delete("/api/races/<int:race_id>/laps/<int:lap_id>")
def api_delete_race_lap(race_id, lap_id):
    guard = require_club_admin_or_race_officer()
    if guard is not None:
        return guard

    payload, status = delete_race_lap(
        db,
        race_id,
        lap_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/finish")
def api_finish_race(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = web_finish_race(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )

    if status == 200 and payload.get("ok"):
        race_data = session.get("race", {})
        if race_data.get("race_id") == race_id:
            race_data["status"] = "finished"
            session["race"] = race_data

    return jsonify(payload), status


@app.get("/api/races/retrospective")
def api_list_retrospective_races():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_retrospective_races(
        db,
        session.get("club_id"),
        request.args.get("series_id"),
        (request.args.get("from_date") or "").strip(),
        (request.args.get("to_date") or "").strip(),
        parse_date_yyyy_mm_dd,
    )
    return jsonify(payload), status


@app.post("/api/races/retrospective")
def api_create_retrospective_race():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = create_retrospective_race(
        db,
        request.get_json(silent=True) or {},
        session.get("club_id"),
        get_actor_context(mobile=False),
        parse_iso_datetime,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/retrospective/draft")
def api_save_retrospective_draft(race_id):
    guard = require_club_admin_or_race_officer()
    if guard is not None:
        return guard

    payload, status = save_retrospective_draft(
        db,
        race_id,
        request.get_json(silent=True) or {},
        session.get("club_id"),
        get_actor_context(mobile=False),
        parse_hms_to_seconds,
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.get("/api/races/<int:race_id>/retrospective/preview")
def api_preview_retrospective_results(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = preview_retrospective_results(
        db,
        race_id,
        session.get("club_id"),
        race_is_locked,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/results/publish")
def api_publish_race_results(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = publish_race_results(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/results/lock")
def api_lock_race_results(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = lock_results(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/results/unlock")
def api_unlock_race_results(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = unlock_results(
        db,
        race_id,
        session.get("club_id"),
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.get("/api/races/<int:race_id>/audit")
def api_get_race_audit(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = get_race_audit(db, race_id, session.get("club_id"))
    return jsonify(payload), status


@app.get("/api/races/<int:race_id>/revisions")
def api_get_race_revisions(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = get_race_revisions(db, race_id, session.get("club_id"))
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/handicap-recommendations/<int:recommendation_id>/decision")
def api_decide_handicap_recommendation(race_id, recommendation_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = decide_handicap_recommendation(
        db,
        race_id,
        session.get("club_id"),
        recommendation_id,
        request.get_json(silent=True) or {},
        get_actor_context(mobile=False),
        create_race_revision,
        write_race_audit,
    )
    return jsonify(payload), status


@app.get("/api/races/<int:race_id>/duties")
def api_list_race_duties(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = list_race_duties(db, race_id, session.get("club_id"))
    return jsonify(payload), status


@app.post("/api/races/<int:race_id>/duties")
def api_assign_race_duty(race_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = assign_race_duty(
        db,
        race_id,
        request.get_json(silent=True) or {},
        session.get("club_id"),
        get_actor_context(mobile=False),
        parse_iso_datetime,
        resolve_role_id,
        upsert_race_duty_assignment,
        write_race_audit,
    )
    return jsonify(payload), status


@app.post("/api/races/duties/by-date")
def api_assign_race_duty_by_date():
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = assign_race_duty_by_date(
        db,
        request.get_json(silent=True) or {},
        session.get("club_id"),
        get_actor_context(mobile=False),
        parse_iso_datetime,
        parse_date_yyyy_mm_dd,
        resolve_role_id,
        upsert_race_duty_assignment,
        write_race_audit,
    )
    return jsonify(payload), status


@app.delete("/api/races/<int:race_id>/duties/<int:duty_id>")
def api_delete_race_duty(race_id, duty_id):
    guard = require_club_admin()
    if guard is not None:
        return guard

    payload, status = delete_race_duty(
        db,
        race_id,
        duty_id,
        session.get("club_id"),
        get_actor_context(mobile=False),
        write_race_audit,
    )
    return jsonify(payload), status


@app.get("/race_summary")
def race_summary_page():
    """Render the race summary page"""
    return render_template("race_summary.html")


@app.get("/api/races/<int:race_id>/summary")
def api_race_summary(race_id):
    """Return full race summary: metadata + results per entry"""
    guard = require_club_admin()
    if guard is not None:
        return guard

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
                      AND r.club = :club_id
                '''),
                {"race_id": race_id, "club_id": session.get("club_id")}
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