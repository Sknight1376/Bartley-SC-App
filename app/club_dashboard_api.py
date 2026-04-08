import csv
import io
from datetime import date, timedelta

from services.club_dashboard_repository import (
    get_boat_class_usage,
    get_duty_roster_rows,
    get_export_results_rows,
    get_handicap_recommendation_rows,
    get_race_calendar_rows,
    get_results_review_queue_rows,
    get_sailors_with_boats,
    race_belongs_to_club,
)


def _parse_date_yyyy_mm_dd(raw):
    value = (raw or "").strip()
    if not value:
        return None
    return date.fromisoformat(value)


def _secs_to_hms(value):
    if value is None:
        return ""
    s = int(value)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def _to_bool(value):
    return str(value or "").strip().lower() in ("1", "true", "yes", "y", "dnf")


def dashboard_sailors_boats(db, club_id):
    try:
        with db.engine.connect() as conn:
            rows = get_sailors_with_boats(conn, club_id)
            classes = get_boat_class_usage(conn, club_id)

        sailors_by_id = {}
        for row in rows:
            sid = row["sailor_id"]
            if sid not in sailors_by_id:
                full_name = row.get("fullname") or ""
                if not full_name.strip():
                    full_name = f"{row.get('firstname') or ''} {row.get('surname') or ''}".strip()
                sailors_by_id[sid] = {
                    "sailor_id": sid,
                    "name": full_name,
                    "boats": [],
                }
            if row.get("boatkey"):
                sailors_by_id[sid]["boats"].append(
                    {
                        "boatkey": row.get("boatkey"),
                        "sail_number": row.get("sail_number"),
                        "boat_class": row.get("boat_class"),
                        "handicap": row.get("handicap"),
                    }
                )

        payload = {
            "ok": True,
            "sailors": list(sailors_by_id.values()),
            "boat_classes": [dict(r) for r in classes],
        }
        return payload, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_race_calendar(db, club_id, args):
    try:
        from_date = _parse_date_yyyy_mm_dd(args.get("from_date")) or date.today() - timedelta(days=14)
        to_date = _parse_date_yyyy_mm_dd(args.get("to_date")) or date.today() + timedelta(days=90)
        limit = int(args.get("limit") or 200)
        if to_date < from_date:
            return {"ok": False, "error": "to_date cannot be before from_date"}, 400

        with db.engine.connect() as conn:
            rows = get_race_calendar_rows(conn, club_id, from_date, to_date, limit=limit)

        return {
            "ok": True,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "races": [dict(r) for r in rows],
        }, 200
    except ValueError:
        return {"ok": False, "error": "Invalid query parameters"}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_duty_roster(db, club_id, args):
    try:
        from_date = _parse_date_yyyy_mm_dd(args.get("from_date")) or date.today() - timedelta(days=14)
        to_date = _parse_date_yyyy_mm_dd(args.get("to_date")) or date.today() + timedelta(days=90)
        limit = int(args.get("limit") or 300)
        if to_date < from_date:
            return {"ok": False, "error": "to_date cannot be before from_date"}, 400

        with db.engine.connect() as conn:
            rows = get_duty_roster_rows(conn, club_id, from_date, to_date, limit=limit)

        return {
            "ok": True,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "duties": [dict(r) for r in rows],
        }, 200
    except ValueError:
        return {"ok": False, "error": "Invalid query parameters"}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_results_review_queue(db, club_id, args):
    try:
        limit = int(args.get("limit") or 200)
        with db.engine.connect() as conn:
            rows = get_results_review_queue_rows(conn, club_id, limit)
        return {"ok": True, "queue": [dict(r) for r in rows]}, 200
    except ValueError:
        return {"ok": False, "error": "Invalid query parameters"}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_handicap_recommendations(db, club_id, args):
    try:
        limit = int(args.get("limit") or 200)
        with db.engine.connect() as conn:
            rows = get_handicap_recommendation_rows(conn, club_id, limit)

        recommendations = []
        for row in rows:
            item = dict(row)
            action = item.get("action") or ""
            if action.endswith("_approved"):
                item["decision"] = "approved"
            elif action.endswith("_rejected"):
                item["decision"] = "rejected"
            else:
                item["decision"] = "pending"
            recommendations.append(item)

        return {"ok": True, "recommendations": recommendations}, 200
    except ValueError:
        return {"ok": False, "error": "Invalid query parameters"}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_export_results_csv(db, club_id, race_id):
    try:
        with db.engine.connect() as conn:
            if not race_belongs_to_club(conn, race_id, club_id):
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_export_results_rows(conn, race_id)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "entry_id",
            "sailor",
            "boat",
            "sail_number",
            "handicap",
            "elapsed_time",
            "corrected_time",
            "position",
            "dnf",
        ])

        for row in rows:
            writer.writerow([
                row.get("entry_id"),
                row.get("sailor"),
                row.get("boat"),
                row.get("sail_number"),
                row.get("handicap"),
                _secs_to_hms(row.get("elapsed_sec")),
                _secs_to_hms(row.get("corrected_sec")),
                row.get("position") or "",
                "true" if row.get("dnf") else "false",
            ])

        return {
            "ok": True,
            "filename": f"race_{race_id}_results.csv",
            "csv": buffer.getvalue(),
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def parse_paper_csv(file_storage):
    if not file_storage:
        raise ValueError("CSV file is required")

    raw = file_storage.read()
    text_data = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text_data))

    required = {"sailor", "boat", "sail_number"}
    header = {h.strip() for h in (reader.fieldnames or [])}
    if not required.issubset(header):
        missing = ", ".join(sorted(required - header))
        raise ValueError(f"CSV missing required columns: {missing}")

    entries = []
    for idx, row in enumerate(reader):
        sailor = (row.get("sailor") or "").strip()
        boat = (row.get("boat") or "").strip()
        sail_number = (row.get("sail_number") or row.get("sailNumber") or "").strip()
        if not sailor or not boat or not sail_number:
            continue

        handicap_raw = (row.get("handicap") or "").strip()
        elapsed_time = (row.get("elapsed_time") or row.get("elapsedTime") or "").strip()
        corrected_time = (row.get("corrected_time") or row.get("correctedTime") or "").strip()
        position_raw = (row.get("position") or "").strip()
        dnf_raw = (row.get("dnf") or "").strip()
        boatkey_raw = (row.get("boatkey") or row.get("key") or "").strip()
        lap_number_raw = (row.get("lap_number") or "").strip()

        item = {
            "sailor": sailor,
            "boat": boat,
            "sailNumber": sail_number,
            "dnf": _to_bool(dnf_raw),
        }

        if handicap_raw:
            try:
                item["handicap"] = int(float(handicap_raw))
            except (TypeError, ValueError):
                raise ValueError(f"Row {idx + 2}: invalid handicap")

        if elapsed_time:
            item["elapsed_time"] = elapsed_time
        if corrected_time:
            item["corrected_time"] = corrected_time
        if position_raw:
            try:
                item["position"] = int(position_raw)
            except (TypeError, ValueError):
                raise ValueError(f"Row {idx + 2}: invalid position")

        if boatkey_raw:
            try:
                item["key"] = int(boatkey_raw)
            except (TypeError, ValueError):
                raise ValueError(f"Row {idx + 2}: invalid boatkey")

        if lap_number_raw:
            try:
                item["lap_number"] = int(lap_number_raw)
            except (TypeError, ValueError):
                raise ValueError(f"Row {idx + 2}: invalid lap_number")

        entries.append(item)

    if not entries:
        raise ValueError("No valid rows found in CSV")
    return entries


def dashboard_import_csv_preview(file_storage):
    try:
        entries = parse_paper_csv(file_storage)
        return {"ok": True, "count": len(entries), "entries": entries}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def dashboard_import_csv_apply(
    db,
    race_id,
    club_id,
    file_storage,
    actor,
    save_retrospective_draft,
    parse_hms_to_seconds,
    race_is_locked,
    create_race_revision,
    write_race_audit,
):
    preview_payload, preview_status = dashboard_import_csv_preview(file_storage)
    if preview_status != 200:
        return preview_payload, preview_status

    payload = {
        "entries": preview_payload["entries"],
        "replace_existing": True,
        "reason": "CSV import from club dashboard",
    }

    return save_retrospective_draft(
        db,
        race_id,
        payload,
        club_id,
        actor,
        parse_hms_to_seconds,
        race_is_locked,
        create_race_revision,
        write_race_audit,
    )
