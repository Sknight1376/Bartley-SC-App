from datetime import datetime, timedelta

from services.schema_validation import (
    validate_mobile_create_boat_payload,
    validate_mobile_join_race_payload,
    validate_mobile_login_payload,
    validate_mobile_profile_update_payload,
    validate_mobile_register_payload,
)
from services.mobile_repository import (
    authenticate_sailor,
    check_race_entry_exists,
    check_username_exists,
    delete_boat,
    get_all_clubs,
    get_assigned_race_ids,
    get_boat_class,
    get_boat_classes,
    get_boat_for_join,
    get_control_race_and_entries,
    get_control_summary,
    get_control_upcoming_races_admin,
    get_control_upcoming_races_duty,
    get_dashboard_data,
    get_my_race_results,
    get_race_exists_for_club,
    get_race_for_join,
    get_race_leaderboard,
    get_sailor_boats,
    get_sailor_profile,
    get_series_for_club,
    get_series_standings,
    get_upcoming_races,
    insert_boat,
    insert_race_entry_for_join,
    insert_sailor,
    insert_sailor_user,
    resolve_club,
    resolve_sailor_club_id,
    update_last_login,
    update_sailor_profile,
)
from services.error_responses import error_payload_for_exception


def _secs_to_hms(s):
    if s is None:
        return None
    s = int(s)
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


# ---------------------------------------------------------------------------
# Control access (pre-existing)
# ---------------------------------------------------------------------------

def build_control_access_response(db, session_dict, sailor_has_active_role):
    sailor_user_id = session_dict.get("sailor_user_id")
    sailor_id = session_dict.get("sailor_id")
    club_id = session_dict.get("sailor_club_id")

    if not sailor_user_id or not sailor_id:
        return {"ok": False, "error": "Unauthorized"}, 401

    try:
        with db.engine.connect() as conn:
            if not club_id:
                club_id = resolve_sailor_club_id(conn, sailor_id)
                if club_id:
                    session_dict["sailor_club_id"] = str(club_id)

            if not club_id:
                return {"ok": True, "can_race_control": False, "assigned_race_ids": []}, 200

            is_mobile_admin = sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, "club_admin")
            assigned_race_ids = get_assigned_race_ids(conn, club_id, sailor_id)

        return {
            "ok": True,
            "can_race_control": bool(is_mobile_admin or assigned_race_ids),
            "is_mobile_admin": bool(is_mobile_admin),
            "assigned_race_ids": assigned_race_ids,
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def mobile_login(db, payload, grant_sailor_role, set_mobile_session):
    try:
        validated = validate_mobile_login_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    try:
        with db.engine.begin() as conn:
            sailor_user = authenticate_sailor(conn, validated["username"], validated["password"])
            if not sailor_user:
                return {"ok": False, "error": "Invalid username or password"}, 401

            update_last_login(conn, sailor_user["sailor_user_id"])
            grant_sailor_role(
                conn,
                sailor_user["sailor_user_id"],
                sailor_user["sailor_id"],
                sailor_user["club"],
                "sailor",
            )

        set_mobile_session(
            sailor_user["sailor_user_id"],
            sailor_user["sailor_id"],
            sailor_user["username"],
            sailor_user["club"],
        )

        return {
            "ok": True,
            "username": sailor_user["username"],
            "sailor_id": sailor_user["sailor_id"],
            "club_id": sailor_user["club"],
            "club_name": sailor_user["club_name"],
            "full_name": sailor_user["fullname"],
            "first_name": sailor_user["firstname"],
            "last_name": sailor_user["lastname"],
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_register(db, payload, grant_sailor_role, set_mobile_session):
    try:
        validated = validate_mobile_register_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    username = validated["username"]
    password = validated["password"]
    first_name = validated["first_name"]
    last_name = validated["last_name"]
    club_id = validated["club_id"]

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            if check_username_exists(conn, username):
                return {"ok": False, "error": "Username already exists"}, 409

            resolved_club_id = None
            resolved_club_name = None
            if club_id not in (None, "", "null"):
                club_row = resolve_club(conn, club_id)
                if not club_row:
                    return {"ok": False, "error": "Club not found"}, 404
                resolved_club_id = club_row["key"]
                resolved_club_name = club_row["name"]

            sailor_id = insert_sailor(conn, full_name, first_name, last_name or None, resolved_club_id)
            sailor_user_id = insert_sailor_user(conn, sailor_id, username, password)
            grant_sailor_role(
                conn,
                sailor_user_id,
                sailor_id,
                resolved_club_id,
                "sailor",
                grant_reason="Initial sailor registration",
            )

        set_mobile_session(sailor_user_id, sailor_id, username, resolved_club_id)

        return {
            "ok": True,
            "username": username,
            "sailor_id": sailor_id,
            "club_id": resolved_club_id,
            "club_name": resolved_club_name,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name or None,
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


# ---------------------------------------------------------------------------
# Sailor profile
# ---------------------------------------------------------------------------

def mobile_me(db, sailor_id, username):
    try:
        with db.engine.connect() as conn:
            sailor = get_sailor_profile(conn, sailor_id)
            if not sailor:
                return {"ok": False, "error": "Sailor not found"}, 404
            boats = get_sailor_boats(conn, sailor_id)

        return {
            "ok": True,
            "profile": {
                "id": sailor["key"],
                "full_name": sailor["fullname"],
                "first_name": sailor["firstname"],
                "last_name": sailor["lastname"],
                "username": username,
                "club_id": sailor["club"],
                "club_name": sailor["club_name"],
            },
            "boats": [dict(b) for b in boats],
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_update_me(db, sailor_id, payload, session_dict):
    try:
        validated = validate_mobile_profile_update_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    first_name = validated["first_name"]
    last_name = validated["last_name"]
    club_id = validated["club_id"]

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            resolved_club_id = None
            if club_id not in (None, "", "null"):
                club_row = resolve_club(conn, club_id)
                if not club_row:
                    return {"ok": False, "error": "Club not found"}, 404
                resolved_club_id = club_row["key"]

            result = update_sailor_profile(conn, sailor_id, full_name, first_name, last_name or None, resolved_club_id)

        if result.rowcount == 0:
            return {"ok": False, "error": "Sailor not found"}, 404

        if resolved_club_id is None:
            session_dict.pop("sailor_club_id", None)
        else:
            session_dict["sailor_club_id"] = str(resolved_club_id)

        return {"ok": True}, 200
    except Exception as e:
        return error_payload_for_exception(e)


# ---------------------------------------------------------------------------
# Lookup lists
# ---------------------------------------------------------------------------

def mobile_clubs(db):
    try:
        with db.engine.connect() as conn:
            rows = get_all_clubs(conn)
        return {"ok": True, "clubs": [dict(row) for row in rows]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_series(db, club_id, sailor_id):
    if not club_id:
        return {"ok": True, "series": []}, 200
    try:
        with db.engine.connect() as conn:
            rows = get_series_for_club(conn, club_id)
        return {"ok": True, "series": [dict(row) for row in rows]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_boats(db, sailor_id):
    try:
        with db.engine.connect() as conn:
            boats = get_sailor_boats(conn, sailor_id)
        return {"ok": True, "boats": [dict(b) for b in boats]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_boat_classes(db):
    try:
        with db.engine.connect() as conn:
            rows = get_boat_classes(conn)
        return {"ok": True, "classes": [dict(r) for r in rows]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_create_boat(db, sailor_id, payload):
    try:
        validated = validate_mobile_create_boat_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    sail_number = validated["sail_number"]
    boat_class_id = validated["boat_class_id"]

    try:
        with db.engine.begin() as conn:
            class_row = get_boat_class(conn, boat_class_id)
            if not class_row:
                return {"ok": False, "error": "Boat class not found"}, 404
            boat_key = insert_boat(conn, class_row["key"], sailor_id, sail_number)

        return {
            "ok": True,
            "boat": {
                "boat_key": boat_key,
                "boat_class_id": class_row["key"],
                "sail_number": sail_number,
                "boat_name": class_row["boat_name"],
                "handicap": class_row["handicap"],
            },
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_delete_boat(db, sailor_id, boat_key):
    try:
        with db.engine.begin() as conn:
            result = delete_boat(conn, boat_key, sailor_id)
            if result.rowcount == 0:
                return {"ok": False, "error": "Boat not found"}, 404
        return {"ok": True}, 200
    except Exception as e:
        return error_payload_for_exception(e)


# ---------------------------------------------------------------------------
# Upcoming races & dashboard
# ---------------------------------------------------------------------------

def mobile_upcoming_races(db, club_id, sailor_id):
    if not club_id:
        return {"ok": True, "races": []}, 200
    try:
        with db.engine.connect() as conn:
            races = get_upcoming_races(conn, club_id, sailor_id)
        return {"ok": True, "races": [dict(r) for r in races]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_dashboard(db, sailor_id, session_dict):
    try:
        with db.engine.connect() as conn:
            club_id = session_dict.get("sailor_club_id")
            if not club_id:
                club_id = resolve_sailor_club_id(conn, sailor_id)
                if club_id:
                    session_dict["sailor_club_id"] = str(club_id)

            if not club_id:
                return {
                    "ok": True,
                    "upcoming_races": [],
                    "completed_races": [],
                    "latest_result": None,
                    "series_positions": [],
                }, 200

            upcoming, completed, _day, latest_day_rows, positions = get_dashboard_data(conn, club_id, sailor_id)

        latest_day_results = [
            {
                "race_id": row["race_id"],
                "race_no": row["race_no"],
                "series_name": row["series_name"],
                "started_at": row["started_at"],
                "sailor": row["sailor"],
                "boat": row["boat"],
                "sail_number": row["sail_number"],
                "position": row["position"],
                "elapsed_time": _secs_to_hms(row["elapsed_sec"]),
                "corrected_time": _secs_to_hms(row["corrected_sec"]),
            }
            for row in latest_day_rows
        ]

        return {
            "ok": True,
            "upcoming_races": [dict(r) for r in upcoming],
            "completed_races": [dict(r) for r in completed],
            "latest_day_results": latest_day_results,
            "latest_result": latest_day_results[0] if latest_day_results else None,
            "series_positions": [dict(r) for r in positions],
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_series_standings(db, sailor_id, session_dict):
    try:
        with db.engine.connect() as conn:
            club_id = session_dict.get("sailor_club_id")
            if not club_id:
                club_id = resolve_sailor_club_id(conn, sailor_id)
                if club_id:
                    session_dict["sailor_club_id"] = str(club_id)

            if not club_id:
                return {"ok": True, "standings": []}, 200

            rows = get_series_standings(conn, club_id)

        return {"ok": True, "standings": [dict(r) for r in rows]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


# ---------------------------------------------------------------------------
# Race join & results
# ---------------------------------------------------------------------------

def mobile_join_race(db, race_id, club_id, sailor_id, payload):
    try:
        validated = validate_mobile_join_race_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    boat_key = validated["boat_key"]

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_join(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            if race_row["status"] == "finished":
                return {"ok": False, "error": "Race already finished"}, 409
            if not race_row["started_at"]:
                return {"ok": False, "error": "Race has no scheduled date/time"}, 409

            now_ts = datetime.now()
            if not (now_ts <= race_row["started_at"] < now_ts + timedelta(days=7)):
                return {"ok": False, "error": "Race is not open for entry (outside next 7 days)"}, 409

            boat_row = get_boat_for_join(conn, boat_key, sailor_id, club_id)
            if not boat_row:
                return {"ok": False, "error": "Boat not found for sailor"}, 404

            if check_race_entry_exists(conn, race_id, boat_key):
                return {"ok": True, "joined": True, "message": "Already joined"}, 200

            insert_race_entry_for_join(conn, race_id, boat_row)

        return {"ok": True, "joined": True}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_race_results(db, race_id, club_id, sailor_id):
    try:
        with db.engine.connect() as conn:
            if not get_race_exists_for_club(conn, race_id, club_id):
                return {"ok": False, "error": "Race not found"}, 404
            my_results = get_my_race_results(conn, race_id, sailor_id)
            leaderboard = get_race_leaderboard(conn, race_id)

        return {
            "ok": True,
            "my_results": [
                {
                    "entry_id": r["entry_id"],
                    "sailor": r["sailor"],
                    "boat": r["boat"],
                    "sail_number": r["sail_number"],
                    "position": r["position"],
                    "elapsed_time": _secs_to_hms(r["elapsed_sec"]),
                    "corrected_time": _secs_to_hms(r["corrected_sec"]),
                }
                for r in my_results
            ],
            "leaderboard": [
                {
                    "sailor": r["sailor"],
                    "boat": r["boat"],
                    "sail_number": r["sail_number"],
                    "position": r["position"],
                    "corrected_time": _secs_to_hms(r["corrected_sec"]),
                }
                for r in leaderboard
            ],
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


# ---------------------------------------------------------------------------
# Mobile race control
# ---------------------------------------------------------------------------

def mobile_control_upcoming_races(db, sailor_user_id, sailor_id, session_dict, sailor_has_active_role):
    try:
        with db.engine.connect() as conn:
            club_id = session_dict.get("sailor_club_id")
            if not club_id:
                club_id = resolve_sailor_club_id(conn, sailor_id)
                if club_id:
                    session_dict["sailor_club_id"] = str(club_id)

            if not club_id:
                return {"ok": True, "races": [], "can_race_control": False}, 200

            is_mobile_admin = sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, "club_admin")

            if is_mobile_admin:
                rows = get_control_upcoming_races_admin(conn, club_id)
            else:
                rows = get_control_upcoming_races_duty(conn, club_id, sailor_id)

        return {
            "ok": True,
            "races": [dict(r) for r in rows],
            "can_race_control": bool(is_mobile_admin or rows),
        }, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_control_entries(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row, entries = get_control_race_and_entries(conn, race_id, club_id)
        if race_row is None:
            return {"ok": False, "error": "Race not found"}, 404
        return {"ok": True, "race": dict(race_row), "entries": [dict(r) for r in entries]}, 200
    except Exception as e:
        return error_payload_for_exception(e)


def mobile_control_summary(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row, results_rows = get_control_summary(conn, race_id, club_id)
        if race_row is None:
            return {"ok": False, "error": "Race not found"}, 404

        started_at = race_row["started_at"]
        ended_at = race_row["ended_at"]
        duration_sec = int((ended_at - started_at).total_seconds()) if started_at and ended_at else None

        race_info = {
            "race_no": race_row["race_no"],
            "club_name": race_row["club_name"],
            "series_name": race_row["series_name"],
            "started_at": started_at.strftime("%H:%M:%S") if started_at else None,
            "date": started_at.strftime("%d %B %Y") if started_at else None,
            "duration": _secs_to_hms(duration_sec),
        }

        results = [
            {
                "entry_id": row["entry_id"],
                "sailor": row["sailor"],
                "boat": row["boat"],
                "sail_number": row["sail_number"],
                "handicap": row["handicap"],
                "lap_count": int(row["lap_count"]) if row["lap_count"] else 0,
                "elapsed_time": _secs_to_hms(row["final_elapsed_sec"]),
                "corrected_time": _secs_to_hms(row["final_corrected_sec"]),
                "position": row["final_position"],
                "dnf": row["final_position"] is None,
            }
            for row in results_rows
        ]

        return {"ok": True, "race": race_info, "results": results}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
