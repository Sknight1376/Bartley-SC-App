from services.admin_repository import (
    authenticate_club_user,
    check_db_health,
    get_club_id_by_name,
    get_race_audit_rows,
    get_race_revision_rows,
    get_series_id_by_name,
    get_test_race_seed_entries,
    update_club_user_last_login,
)
from services.race_control_repository import get_race_for_club
from services.error_responses import error_payload_for_exception


def health_check(db):
    try:
        with db.engine.connect() as conn:
            check_db_health(conn)
        return {"ok": True, "status": "healthy"}, 200
    except Exception as exc:
        payload, status = error_payload_for_exception(exc)
        payload["status"] = "unhealthy"
        return payload, status


def admin_login(db, payload, grant_club_role):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return {"ok": False, "error": "Missing username or password"}, 400

    try:
        with db.engine.begin() as conn:
            user_row = authenticate_club_user(conn, username, password)
            if user_row:
                update_club_user_last_login(conn, user_row["user_id"])
                grant_club_role(conn, user_row["user_id"], user_row["club_id"], "club_admin", user_row["user_id"])

        if not user_row:
            return {"ok": False, "error": "Invalid username or password"}, 401

        return {
            "ok": True,
            "user_id": user_row["user_id"],
            "club_id": str(user_row["club_id"]),
            "club_name": user_row["club_name"],
            "username": user_row["username"],
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


def load_test_race_session_seed(db):
    try:
        with db.engine.connect() as conn:
            club_id = get_club_id_by_name(conn, "Test Club")
            series_id = get_series_id_by_name(conn, "Test Series")
            rows = get_test_race_seed_entries(conn, club_id)

        entries = [
            {
                "key": str(row["boatkey"]),
                "boat": row["boat"],
                "sailor": row["sailor"],
                "handicap": row["handicap"],
                "sailNumber": row["sail_number"],
            }
            for row in rows
        ]

        if not entries:
            entries = [
                {"key": "1", "boat": "Laser 1", "sailor": "John Doe", "handicap": 1100, "sailNumber": "123"},
                {"key": "2", "boat": "Laser 2", "sailor": "Jane Smith", "handicap": 1120, "sailNumber": "456"},
                {"key": "3", "boat": "Laser 3", "sailor": "Bob Johnson", "handicap": 1080, "sailNumber": "789"},
            ]

        return {
            "ok": True,
            "race": {
                "club_id": str(club_id) if club_id is not None else "Test Club",
                "series_id": str(series_id) if series_id is not None else "Test Series",
                "entries": entries,
                "status": "not_started",
            },
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


def get_race_audit(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_race_audit_rows(conn, race_id)
        return {"ok": True, "race_id": race_id, "audit": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


def get_race_revisions(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_race_revision_rows(conn, race_id)
        return {"ok": True, "race_id": race_id, "revisions": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


def decide_handicap_recommendation(
    db,
    race_id,
    club_id,
    recommendation_id,
    payload,
    actor,
    create_race_revision,
    write_race_audit,
):
    decision = (payload.get("decision") or "").strip().lower()
    reason = (payload.get("reason") or "").strip()

    if decision not in ("approved", "rejected"):
        return {"ok": False, "error": "decision must be approved or rejected"}, 400
    if not reason:
        return {"ok": False, "error": "reason is required"}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404

            action = (
                "handicap_recommendation_approved"
                if decision == "approved"
                else "handicap_recommendation_rejected"
            )
            revision_id = create_race_revision(
                conn, race_id, actor,
                reason=reason,
                status=race_row.get("results_status") or "draft",
                source_mode=race_row.get("source_mode") or "live",
            )

            write_race_audit(
                conn, race_id, actor,
                entity_type="handicap_recommendation",
                entity_id=recommendation_id,
                action=action,
                reason=reason,
                before_obj={
                    "recommendation_id": recommendation_id,
                    "status": payload.get("previous_status") or "pending",
                },
                after_obj={
                    "recommendation_id": recommendation_id,
                    "status": decision,
                    "notes": payload.get("notes"),
                },
                revision_id=revision_id,
            )

        return {
            "ok": True,
            "race_id": race_id,
            "recommendation_id": recommendation_id,
            "decision": decision,
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)

