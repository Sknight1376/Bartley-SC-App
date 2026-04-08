from services.retrospective_repository import (
    check_series_for_club,
    delete_all_entries,
    delete_all_entry_laps,
    get_next_race_no,
    get_preview_entries,
    get_race_for_preview,
    insert_retrospective_entry,
    insert_retrospective_lap,
    insert_retrospective_race,
    list_retrospective_races as _list_races,
    publish_race_results as _publish,
    resolve_boatkey,
    set_race_to_draft,
)
from services.race_control_repository import get_race_for_club


def _secs_to_hms(s):
    if s is None:
        return None
    s = int(s)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def list_retrospective_races(
    db,
    club_id,
    series_id_raw,
    from_raw,
    to_raw,
    parse_date_yyyy_mm_dd,
):
    try:
        from_date = parse_date_yyyy_mm_dd(from_raw, "from_date") if from_raw else None
        to_date = parse_date_yyyy_mm_dd(to_raw, "to_date") if to_raw else None
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    if from_date and to_date and to_date < from_date:
        return {"ok": False, "error": "to_date cannot be before from_date"}, 400

    series_id = None
    if series_id_raw not in (None, "", "null"):
        try:
            series_id = int(series_id_raw)
        except (TypeError, ValueError):
            return {"ok": False, "error": "Invalid series_id"}, 400

    try:
        with db.engine.connect() as conn:
            rows = _list_races(conn, club_id, series_id, from_date, to_date)
        return {"ok": True, "races": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def create_retrospective_race(
    db,
    payload,
    club_id,
    actor,
    parse_iso_datetime,
    create_race_revision,
    write_race_audit,
):
    from datetime import datetime

    series_id = payload.get("series_id")
    race_no = payload.get("race_no")
    reason = (payload.get("reason") or "Create retrospective race").strip() or "Create retrospective race"

    if series_id in (None, "", "null"):
        return {"ok": False, "error": "series_id is required"}, 400

    try:
        started_at = parse_iso_datetime(payload.get("started_at"), "started_at")
        ended_at = parse_iso_datetime(payload.get("ended_at"), "ended_at")
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    if started_at is None:
        started_at = datetime.utcnow()
    if ended_at is None:
        ended_at = started_at
    if ended_at < started_at:
        return {"ok": False, "error": "ended_at cannot be before started_at"}, 400

    try:
        with db.engine.begin() as conn:
            if not check_series_for_club(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            if race_no in (None, "", "null"):
                resolved_race_no = get_next_race_no(conn, series_id)
            else:
                resolved_race_no = int(race_no)

            race_id = insert_retrospective_race(
                conn,
                {
                    "club_id": club_id,
                    "series_id": series_id,
                    "race_no": resolved_race_no,
                    "started_at": started_at,
                    "ended_at": ended_at,
                },
            )

            revision_id = create_race_revision(
                conn, race_id, actor,
                reason=reason, status="draft", source_mode="retrospective",
            )
            write_race_audit(
                conn, race_id, actor,
                entity_type="race", entity_id=race_id,
                action="retrospective_race_created", reason=reason,
                after_obj={
                    "status": "finished",
                    "results_status": "draft",
                    "source_mode": "retrospective",
                    "race_no": resolved_race_no,
                },
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "race_no": resolved_race_no, "results_status": "draft"}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def save_retrospective_draft(
    db,
    race_id,
    payload,
    club_id,
    actor,
    parse_hms_to_seconds,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    entries = payload.get("entries") or []
    replace_existing = bool(payload.get("replace_existing", True))
    reason = (payload.get("reason") or "Save retrospective draft").strip() or "Save retrospective draft"

    if not isinstance(entries, list):
        return {"ok": False, "error": "entries must be an array"}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            if race_is_locked(race_row):
                return {"ok": False, "error": "Results are locked for this race"}, 409

            set_race_to_draft(conn, race_id, club_id)

            revision_id = create_race_revision(
                conn, race_id, actor,
                reason=reason, status="draft", source_mode="retrospective",
            )

            if replace_existing:
                delete_all_entry_laps(conn, race_id)
                delete_all_entries(conn, race_id)

            saved_entries = 0
            saved_finishes = 0

            for idx, row in enumerate(entries):
                sailor = (row.get("sailor") or "").strip()
                boat = (row.get("boat") or "").strip()
                sail_number = (row.get("sail_number") or row.get("sailNumber") or "").strip()
                if not sailor or not boat or not sail_number:
                    return {"ok": False, "error": f"entries[{idx}] missing sailor/boat/sail_number"}, 400

                raw_boatkey = row.get("boatkey") or row.get("key")
                boatkey = None
                if raw_boatkey not in (None, "", "null"):
                    try:
                        boatkey = int(raw_boatkey)
                    except (TypeError, ValueError):
                        return {"ok": False, "error": f"entries[{idx}] invalid boatkey"}, 400

                if boatkey is None:
                    boatkey = resolve_boatkey(conn, club_id, sailor, sail_number)
                if boatkey is None:
                    return {
                        "ok": False,
                        "error": f"entries[{idx}] could not resolve boatkey for {sailor} ({sail_number})",
                    }, 400

                handicap_raw = row.get("handicap")
                handicap = None
                if handicap_raw not in (None, "", "N/A"):
                    try:
                        handicap = int(float(handicap_raw))
                    except (TypeError, ValueError):
                        return {"ok": False, "error": f"entries[{idx}] invalid handicap"}, 400

                entry_id = insert_retrospective_entry(
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
                        "revision_id": revision_id,
                    },
                )
                saved_entries += 1

                dnf = bool(row.get("dnf", False))
                elapsed_time = (row.get("elapsed_time") or row.get("elapsedTime") or "").strip()
                corrected_time = (row.get("corrected_time") or row.get("correctedTime") or "").strip()
                position_raw = row.get("position")

                if not dnf and elapsed_time:
                    try:
                        elapsed_sec = parse_hms_to_seconds(elapsed_time)
                    except Exception:
                        return {"ok": False, "error": f"entries[{idx}] invalid elapsed_time"}, 400

                    corrected_sec = None
                    if corrected_time and corrected_time != "N/A":
                        try:
                            corrected_sec = parse_hms_to_seconds(corrected_time)
                        except Exception:
                            return {"ok": False, "error": f"entries[{idx}] invalid corrected_time"}, 400

                    position = None
                    if position_raw not in (None, "", "N/A"):
                        try:
                            position = int(position_raw)
                        except (TypeError, ValueError):
                            return {"ok": False, "error": f"entries[{idx}] invalid position"}, 400

                    lap_number = row.get("lap_number") or 1
                    try:
                        lap_number = int(lap_number)
                    except (TypeError, ValueError):
                        return {"ok": False, "error": f"entries[{idx}] invalid lap_number"}, 400

                    insert_retrospective_lap(
                        conn,
                        {
                            "race_entry_id": entry_id,
                            "lap_number": lap_number,
                            "elapsed_sec": elapsed_sec,
                            "corrected_sec": corrected_sec,
                            "position": position,
                            "created_by_user": actor.get("created_by_user"),
                            "created_by_type": actor.get("created_by_type"),
                            "revision_id": revision_id,
                        },
                    )
                    saved_finishes += 1

            write_race_audit(
                conn, race_id, actor,
                entity_type="race", entity_id=race_id,
                action="retrospective_result_imported", reason=reason,
                after_obj={
                    "entry_count": saved_entries,
                    "finish_count": saved_finishes,
                    "results_status": "draft",
                },
                revision_id=revision_id,
            )

        return {
            "ok": True,
            "race_id": race_id,
            "results_status": "draft",
            "saved_entries": saved_entries,
            "saved_finishes": saved_finishes,
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def preview_retrospective_results(db, race_id, club_id, race_is_locked):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_preview(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404

            rows = get_preview_entries(conn, race_id)

        results = [
            {
                "entry_id": row["entry_id"],
                "sailor": row["sailor"],
                "boat": row["boat"],
                "sail_number": row["sail_number"],
                "handicap": row["handicap"],
                "elapsed_time": _secs_to_hms(row["elapsed_sec"]),
                "corrected_time": _secs_to_hms(row["corrected_sec"]),
                "position": row["position"],
                "dnf": row["position"] is None,
            }
            for row in rows
        ]

        preview = dict(race_row)
        preview["is_locked"] = race_is_locked(race_row)
        return {"ok": True, "race": preview, "results": results}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def publish_race_results(
    db,
    race_id,
    club_id,
    payload,
    actor,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    reason = (payload.get("reason") or "Publish results").strip() or "Publish results"

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            if race_is_locked(race_row):
                return {"ok": False, "error": "Results are locked for this race"}, 409

            _publish(conn, race_id, club_id)

            revision_id = create_race_revision(
                conn, race_id, actor,
                reason=reason, status="published",
                source_mode=race_row.get("source_mode") or "retrospective",
            )
            write_race_audit(
                conn, race_id, actor,
                entity_type="race", entity_id=race_id,
                action="results_published", reason=reason,
                before_obj={"results_status": race_row.get("results_status")},
                after_obj={"results_status": "published"},
                revision_id=revision_id,
            )

        return {"ok": True, "race_id": race_id, "results_status": "published"}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
