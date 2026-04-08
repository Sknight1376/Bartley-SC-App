from datetime import datetime

from services.race_control_repository import (
    clear_race_entries_for_race,
    delete_entry,
    delete_entry_laps,
    delete_lap,
    finish_race,
    get_entry_for_race,
    get_lap_count_for_entry,
    get_lap_for_race,
    list_race_entries,
    get_race_for_club,
    get_race_summary_header,
    get_race_summary_results,
    get_selected_race_for_start,
    get_next_race_no_for_series,
    insert_lap,
    insert_race_start_row,
    insert_race_entry,
    lock_race_results,
    race_entry_exists,
    resolve_boatkey,
    resolve_boatkey_for_start,
    set_race_active,
    unlock_race_results,
    update_lap,
)
from services.schema_validation import validate_lap_payload


def ensure_results_editable(race_row, race_is_locked):
    if race_is_locked(race_row):
        return False, "Results are locked for this race"
    return True, None


def web_start_race(
    db,
    payload,
    race_data,
    session_club_id,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    club_id = payload.get("club_id") or race_data.get("club_id") or session_club_id
    series_id = payload.get("series_id") or race_data.get("series_id")
    selected_race_id = payload.get("race_id") or race_data.get("race_id")
    entries = payload.get("entries") or race_data.get("entries") or []
    source_mode = (payload.get("source_mode") or "live").strip().lower()
    if source_mode not in ("live", "retrospective"):
        source_mode = "live"
    reason = (payload.get("reason") or "Web race start").strip() or "Web race start"

    if not club_id or not series_id:
        return {"ok": False, "error": "Missing club_id or series_id"}, 400
    if str(club_id) != str(session_club_id):
        return {"ok": False, "error": "Forbidden"}, 403
    if not entries:
        return {"ok": False, "error": "No entries provided"}, 400

    if race_data.get("race_id") and race_data.get("status") == "active":
        # Do not trust stale session entries for an active race. Reload from DB so
        # clients always receive stable persisted `entry_id` values.
        try:
            with db.engine.connect() as conn:
                race_row = get_race_for_club(conn, race_data.get("race_id"), club_id)
                if race_row:
                    persisted = []
                    for row in list_race_entries(conn, race_data.get("race_id")):
                        persisted.append(
                            {
                                "entry_id": row["entry_id"],
                                "sailor": row["sailor"],
                                "boat": row["boat"],
                                "sailNumber": row["sail_number"],
                                "handicap": row["handicap"],
                                "key": row["boatkey"],
                            }
                        )

                    return {
                        "ok": True,
                        "race_id": race_data.get("race_id"),
                        "race_no": race_data.get("race_no"),
                        "entries": persisted,
                    }, 200
        except Exception:
            # Fall through to normal start flow if DB lookup fails unexpectedly.
            pass

    race_id = None
    race_no = None
    persisted_entries = []

    try:
        with db.engine.begin() as conn:
            if selected_race_id:
                selected = get_selected_race_for_start(conn, selected_race_id, club_id, series_id)
                if not selected:
                    return {"ok": False, "error": "Selected race not found for this club/series"}, 404
                if race_is_locked(selected):
                    return {"ok": False, "error": "Results are locked for this race"}, 409
                if selected["status"] == "finished":
                    return {"ok": False, "error": "Selected race is already finished"}, 409

                race_id = selected["key"]
                race_no = selected["race_no"]

                set_race_active(conn, race_id, source_mode)
                clear_race_entries_for_race(conn, race_id)
            else:
                race_no = get_next_race_no_for_series(conn, series_id)
                race_id = insert_race_start_row(conn, club_id, series_id, race_no, source_mode)

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=source_mode,
            )

            for entry in entries:
                raw_boatkey = entry.get("key")
                boatkey = None
                if raw_boatkey not in (None, ""):
                    try:
                        boatkey = int(raw_boatkey)
                    except (TypeError, ValueError):
                        boatkey = None

                if boatkey is None:
                    club_id_int = None
                    try:
                        club_id_int = int(club_id)
                    except (TypeError, ValueError):
                        club_id_int = None

                    boatkey = resolve_boatkey_for_start(
                        conn,
                        entry.get("sailor"),
                        entry.get("sailNumber"),
                        club_id_int,
                    )

                if boatkey is None:
                    return {
                        "ok": False,
                        "error": f"Missing/invalid boat key for entry: {entry.get('sailor', 'unknown')} ({entry.get('sailNumber', 'no sail #')}). Re-add this sailor/boat from the entry screen.",
                        "race_id": race_id,
                        "race_no": race_no,
                        "entries": persisted_entries,
                    }, 400

                handicap_raw = entry.get("handicap")
                handicap = None
                if handicap_raw not in (None, "", "N/A"):
                    try:
                        handicap = int(float(handicap_raw))
                    except (TypeError, ValueError):
                        handicap = None

                entry_id = insert_race_entry(
                    conn,
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
                    },
                )

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

        return {"ok": True, "race_id": race_id, "race_no": race_no, "entries": persisted_entries}, 200
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "race_id": race_id,
            "race_no": race_no,
            "entries": persisted_entries,
        }, 500


def web_race_summary(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_summary_header(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            results_rows = get_race_summary_results(conn, race_id)

        def secs_to_hms(s):
            if s is None:
                return None
            s = int(s)
            return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

        started_at = race_row["started_at"]
        ended_at = race_row["ended_at"]
        duration_sec = int((ended_at - started_at).total_seconds()) if started_at and ended_at else None

        race_info = {
            "race_no": race_row["race_no"],
            "club_name": race_row["club_name"],
            "series_name": race_row["series_name"],
            "started_at": started_at.strftime("%H:%M:%S") if started_at else None,
            "date": started_at.strftime("%d %B %Y") if started_at else None,
            "duration": secs_to_hms(duration_sec),
        }

        results = [
            {
                "entry_id": row["entry_id"],
                "sailor": row["sailor"],
                "boat": row["boat"],
                "sail_number": row["sail_number"],
                "handicap": row["handicap"],
                "lap_count": int(row["lap_count"]) if row["lap_count"] else 0,
                "elapsed_time": secs_to_hms(row["final_elapsed_sec"]),
                "corrected_time": secs_to_hms(row["final_corrected_sec"]),
                "position": row["final_position"],
                "dnf": row["final_position"] is None,
            }
            for row in results_rows
        ]

        return {"ok": True, "race": race_info, "results": results}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def mobile_control_start(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    source_mode = (payload.get("source_mode") or "live").strip().lower()
    if source_mode not in ("live", "retrospective"):
        source_mode = "live"
    reason = (payload.get("reason") or "Mobile race start").strip() or "Mobile race start"

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409
            if race_row["status"] == "finished":
                return {"ok": False, "error": "Race already finished"}, 409

            set_race_active(conn, race_id, source_mode)

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=source_mode,
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="race_started",
                reason=reason,
                before_obj={"status": race_row["status"], "results_status": race_row["results_status"]},
                after_obj={"status": "active", "results_status": "draft", "source_mode": source_mode},
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def mobile_control_lap(
    db,
    race_id,
    club_id,
    payload,
    actor,
    parse_hms_to_seconds,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    try:
        lap = validate_lap_payload(payload, parse_hms_to_seconds)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409
            if race_row["status"] == "finished":
                return {"ok": False, "error": "Race already finished"}, 409

            if not race_entry_exists(conn, lap["entry_id"], race_id):
                return {"ok": False, "error": "Race entry not found"}, 404

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason="Mobile lap recorded",
                status="draft",
                source_mode=race_row.get("source_mode") or "live",
            )

            insert_lap(
                conn,
                {
                    "race_entry_id": lap["entry_id"],
                    "lap_number": lap["lap_number"],
                    "is_finish": lap["is_finish"],
                    "elapsed_sec": lap["elapsed_sec"],
                    "corrected_sec": lap["corrected_sec"],
                    "position": lap["position"],
                    "created_by_user": actor.get("created_by_user"),
                    "created_by_type": actor.get("created_by_type"),
                    "source": race_row.get("source_mode") or "live",
                    "revision_id": revision_id,
                },
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="lap",
                entity_id=lap["entry_id"],
                action="lap_added",
                after_obj={
                    "entry_id": lap["entry_id"],
                    "lap_number": lap["lap_number"],
                    "is_finish": lap["is_finish"],
                    "elapsed_sec": lap["elapsed_sec"],
                    "corrected_sec": lap["corrected_sec"],
                    "position": lap["position"],
                },
                revision_id=revision_id,
            )

        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def mobile_control_finish(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Mobile race finish").strip() or "Mobile race finish"
    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            updated = finish_race(conn, race_id, club_id)

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="published",
                source_mode=race_row.get("source_mode") or "live",
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="race_finished",
                reason=reason,
                before_obj={"status": race_row["status"], "results_status": race_row["results_status"]},
                after_obj={"status": "finished", "results_status": "published"},
                revision_id=revision_id,
            )

        if updated.rowcount == 0:
            return {"ok": False, "error": "Race not found"}, 404

        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def web_record_lap(
    db,
    race_id,
    club_id,
    payload,
    actor,
    parse_hms_to_seconds,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    try:
        lap = validate_lap_payload(payload, parse_hms_to_seconds)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409
            if race_row["status"] == "finished":
                return {"ok": False, "error": "Race already finished"}, 409

            if not race_entry_exists(conn, lap["entry_id"], race_id):
                return {"ok": False, "error": "Race entry not found"}, 404

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason="Web lap recorded",
                status="draft",
                source_mode=race_row.get("source_mode") or "live",
            )

            insert_lap(
                conn,
                {
                    "race_entry_id": lap["entry_id"],
                    "lap_number": lap["lap_number"],
                    "is_finish": lap["is_finish"],
                    "elapsed_sec": lap["elapsed_sec"],
                    "corrected_sec": lap["corrected_sec"],
                    "position": lap["position"],
                    "created_by_user": actor.get("created_by_user"),
                    "created_by_type": actor.get("created_by_type"),
                    "source": race_row.get("source_mode") or "live",
                    "revision_id": revision_id,
                },
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="lap",
                entity_id=lap["entry_id"],
                action="lap_added",
                after_obj={
                    "entry_id": lap["entry_id"],
                    "lap_number": lap["lap_number"],
                    "is_finish": lap["is_finish"],
                    "elapsed_sec": lap["elapsed_sec"],
                    "corrected_sec": lap["corrected_sec"],
                    "position": lap["position"],
                },
                revision_id=revision_id,
            )

        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def web_finish_race(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Web race finish").strip() or "Web race finish"
    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            updated = finish_race(conn, race_id, club_id)

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="published",
                source_mode=race_row.get("source_mode") or "live",
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="race_finished",
                reason=reason,
                before_obj={"status": race_row["status"], "results_status": race_row["results_status"]},
                after_obj={"status": "finished", "results_status": "published"},
                revision_id=revision_id,
            )

        if updated.rowcount == 0:
            return {"ok": False, "error": "Race not found"}, 404

        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def lock_results(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Results locked").strip() or "Results locked"
    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            if race_is_locked(race_row):
                return {"ok": True, "race_id": race_id, "results_status": "locked"}, 200

            updated = lock_race_results(conn, race_id, club_id, actor.get("created_by_user"))
            if updated.rowcount == 0:
                return {"ok": False, "error": "Race not found"}, 404

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="locked",
                source_mode=race_row.get("source_mode") or "live",
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="results_locked",
                reason=reason,
                before_obj={"results_status": race_row.get("results_status")},
                after_obj={"results_status": "locked"},
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "results_status": "locked"}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def unlock_results(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "").strip()
    if not reason:
        return {"ok": False, "error": "reason is required to unlock results"}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            if not race_is_locked(race_row):
                return {"ok": False, "error": "Race results are not locked"}, 409

            unlocked_at = datetime.utcnow()
            updated = unlock_race_results(conn, race_id, club_id)
            if updated.rowcount == 0:
                return {"ok": False, "error": "Race not found"}, 404

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="published",
                source_mode=race_row.get("source_mode") or "live",
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="race",
                entity_id=race_id,
                action="results_unlocked",
                reason=reason,
                before_obj={
                    "results_status": race_row.get("results_status"),
                    "results_locked_at": race_row.get("results_locked_at").isoformat() if race_row.get("results_locked_at") else None,
                },
                after_obj={
                    "results_status": "published",
                    "unlocked_at": unlocked_at.isoformat(),
                    "unlocked_by": actor.get("actor_user_id"),
                },
                revision_id=revision_id,
            )

        return {
            "ok": True,
            "race_id": race_id,
            "results_status": "published",
            "unlock": {
                "reason": reason,
                "actor_user_id": actor.get("actor_user_id"),
                "timestamp": unlocked_at.isoformat(),
            },
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


# ---------------------------------------------------------------------------
# Race entry management
# ---------------------------------------------------------------------------

def add_race_entry(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Entry added").strip() or "Entry added"

    sailor = (payload.get("sailor") or "").strip()
    boat = (payload.get("boat") or "").strip()
    sail_number = (payload.get("sail_number") or payload.get("sailNumber") or "").strip()
    if not sailor or not boat or not sail_number:
        return {"ok": False, "error": "sailor, boat, and sail_number are required"}, 400

    raw_boatkey = payload.get("boatkey") or payload.get("key")
    boatkey = None
    if raw_boatkey not in (None, "", "null"):
        try:
            boatkey = int(raw_boatkey)
        except (TypeError, ValueError):
            return {"ok": False, "error": "Invalid boatkey"}, 400

    handicap_raw = payload.get("handicap")
    handicap = None
    if handicap_raw not in (None, "", "N/A"):
        try:
            handicap = int(float(handicap_raw))
        except (TypeError, ValueError):
            return {"ok": False, "error": "Invalid handicap"}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            if boatkey is None:
                boatkey = resolve_boatkey(conn, club_id, sailor, sail_number)
                if boatkey is None:
                    return {"ok": False, "error": "Unable to resolve boatkey"}, 400

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=race_row.get("source_mode") or "retrospective",
            )

            entry_id = insert_race_entry(
                conn,
                {
                    "race_id": race_id,
                    "boatkey": boatkey,
                    "sailor": sailor,
                    "boat": boat,
                    "sail_number": sail_number,
                    "handicap": handicap,
                    "created_by_user": actor.get("created_by_user"),
                    "created_by_type": actor.get("created_by_type"),
                    "source": race_row.get("source_mode") or "retrospective",
                    "revision_id": revision_id,
                },
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="entry",
                entity_id=entry_id,
                action="entry_added",
                reason=reason,
                after_obj={
                    "entry_id": entry_id,
                    "sailor": sailor,
                    "boat": boat,
                    "sail_number": sail_number,
                    "handicap": handicap,
                },
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "entry_id": entry_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def remove_race_entry(
    db,
    race_id,
    entry_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Entry removed").strip() or "Entry removed"

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            entry_row = get_entry_for_race(conn, entry_id, race_id)
            if not entry_row:
                return {"ok": False, "error": "Entry not found"}, 404

            lap_count = get_lap_count_for_entry(conn, entry_id)

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=race_row.get("source_mode") or "retrospective",
            )

            delete_entry_laps(conn, entry_id)
            delete_entry(conn, entry_id, race_id)

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="entry",
                entity_id=entry_id,
                action="entry_removed",
                reason=reason,
                before_obj={
                    "entry_id": entry_row["key"],
                    "sailor": entry_row["sailor"],
                    "boat": entry_row["boat"],
                    "sail_number": entry_row["sail_number"],
                    "handicap": entry_row["handicap"],
                    "lap_count": int(lap_count or 0),
                },
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "entry_id": entry_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


# ---------------------------------------------------------------------------
# Lap edit / delete
# ---------------------------------------------------------------------------

def edit_race_lap(
    db,
    race_id,
    lap_id,
    club_id,
    payload,
    actor,
    parse_hms_to_seconds,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Lap edited").strip() or "Lap edited"

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            lap_row = get_lap_for_race(conn, lap_id, race_id)
            if not lap_row:
                return {"ok": False, "error": "Lap not found"}, 404

            elapsed_sec = lap_row["elapsed_sec"]
            corrected_sec = lap_row["corrected_sec"]
            position = lap_row["position"]
            lap_number = lap_row["lap_number"]
            is_finish = lap_row["is_finish"]

            if "elapsed_time" in payload and payload.get("elapsed_time") not in (None, "", "N/A"):
                elapsed_sec = parse_hms_to_seconds(payload.get("elapsed_time"))
            if "corrected_time" in payload:
                ct = payload.get("corrected_time")
                corrected_sec = parse_hms_to_seconds(ct) if ct not in (None, "", "N/A") else None
            if "position" in payload:
                p = payload.get("position")
                position = int(p) if p not in (None, "", "N/A") else None
            if "lap_number" in payload and payload.get("lap_number") not in (None, ""):
                lap_number = int(payload.get("lap_number"))
            if "is_finish" in payload:
                is_finish = bool(payload.get("is_finish"))

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=race_row.get("source_mode") or "retrospective",
            )

            update_lap(
                conn,
                lap_id,
                {
                    "lap_number": lap_number,
                    "is_finish": is_finish,
                    "elapsed_sec": elapsed_sec,
                    "corrected_sec": corrected_sec,
                    "position": position,
                    "created_by_user": actor.get("created_by_user"),
                    "created_by_type": actor.get("created_by_type"),
                    "revision_id": revision_id,
                },
            )

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="lap",
                entity_id=lap_id,
                action="lap_edited",
                reason=reason,
                before_obj={
                    "lap_number": lap_row["lap_number"],
                    "is_finish": lap_row["is_finish"],
                    "elapsed_sec": lap_row["elapsed_sec"],
                    "corrected_sec": lap_row["corrected_sec"],
                    "position": lap_row["position"],
                },
                after_obj={
                    "lap_number": lap_number,
                    "is_finish": is_finish,
                    "elapsed_sec": elapsed_sec,
                    "corrected_sec": corrected_sec,
                    "position": position,
                },
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "lap_id": lap_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def delete_race_lap(
    db,
    race_id,
    lap_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Lap deleted").strip() or "Lap deleted"

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            editable, error = ensure_results_editable(race_row, race_is_locked)
            if not editable:
                return {"ok": False, "error": error}, 409

            lap_row = get_lap_for_race(conn, lap_id, race_id)
            if not lap_row:
                return {"ok": False, "error": "Lap not found"}, 404

            revision_id = create_race_revision(
                conn,
                race_id,
                actor,
                reason=reason,
                status="draft",
                source_mode=race_row.get("source_mode") or "retrospective",
            )

            delete_lap(conn, lap_id)

            write_race_audit(
                conn,
                race_id,
                actor,
                entity_type="lap",
                entity_id=lap_id,
                action="lap_deleted",
                reason=reason,
                before_obj={
                    "lap_number": lap_row["lap_number"],
                    "is_finish": lap_row["is_finish"],
                    "elapsed_sec": lap_row["elapsed_sec"],
                    "corrected_sec": lap_row["corrected_sec"],
                    "position": lap_row["position"],
                },
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "lap_id": lap_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
