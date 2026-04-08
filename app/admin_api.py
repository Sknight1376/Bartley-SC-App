from services.admin_repository import check_db_health, get_race_audit_rows, get_race_revision_rows
from services.race_control_repository import get_race_for_club


def health_check(db):
    try:
        with db.engine.connect() as conn:
            check_db_health(conn)
        return {"ok": True, "status": "healthy"}, 200
    except Exception as exc:
        return {"ok": False, "status": "unhealthy", "error": str(exc)}, 500


def get_race_audit(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_race_audit_rows(conn, race_id)
        return {"ok": True, "race_id": race_id, "audit": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def get_race_revisions(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_race_revision_rows(conn, race_id)
        return {"ok": True, "race_id": race_id, "revisions": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


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
        return {"ok": False, "error": str(exc)}, 500

