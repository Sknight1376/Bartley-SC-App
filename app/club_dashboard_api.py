import csv
import io
from datetime import date, timedelta

from services.club_dashboard_repository import (
    get_club_summary_stats,
    get_boat_class_usage,
    get_duty_roster_rows,
    get_export_results_rows,
    get_handicap_recommendation_rows,
    get_latest_race_results_rows,
    get_race_calendar_rows,
    get_results_review_queue_rows,
    get_sailors_with_boats,
    get_series_results_rows,
    race_belongs_to_club,
)
from services.error_responses import error_payload_for_exception


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


def _normalize_rows_to_max_laps(rows, lap_key="lap_count", elapsed_key="elapsed_sec", corrected_key="corrected_sec"):
    lap_values = [int(row.get(lap_key) or 0) for row in rows if int(row.get(lap_key) or 0) > 0]
    max_laps = max(lap_values, default=0)
    target_laps = max_laps
    if target_laps <= 1:
        return [dict(row) for row in rows]

    normalized = []
    for row in rows:
        item = dict(row)
        laps = max(int(item.get(lap_key) or 0), 1)
        if elapsed_key and item.get(elapsed_key) is not None:
            item[elapsed_key] = round(float(item[elapsed_key]) * target_laps / laps)
        if corrected_key and item.get(corrected_key) is not None:
            item[corrected_key] = round(float(item[corrected_key]) * target_laps / laps)
        normalized.append(item)
    return normalized


def _normalize_rows_by_race(rows, race_key="race_id", lap_key="lap_count", elapsed_key="elapsed_sec", corrected_key="corrected_sec"):
    grouped = {}
    for row in rows:
        grouped.setdefault(row.get(race_key), []).append(row)

    normalized = []
    for race_rows in grouped.values():
        normalized.extend(_normalize_rows_to_max_laps(race_rows, lap_key, elapsed_key, corrected_key))
    return normalized


def _format_series_points(value):
    if value is None:
        return ""
    score = float(value)
    if score.is_integer():
        return f"{int(score)}.0"
    return f"{score:.1f}"


def _group_series_results(rows):
    grouped = {}

    for row in rows:
        sid = row.get("series_id")
        item = grouped.setdefault(
            sid,
            {
                "series_id": sid,
                "series_name": row.get("series_name"),
                "latest_started_at": row.get("latest_started_at"),
                "race_count": int(row.get("race_count") or 0),
                "discard_count": int(row.get("discard_count") or 0),
                "results": [],
                "races": [],
                "race_sections": [],
                "_race_map": {},
                "_sailor_map": {},
            },
        )
        item["discard_count"] = max(int(item.get("discard_count") or 0), int(row.get("discard_count") or 0))

        race_id = row.get("race_id")
        race = item["_race_map"].setdefault(
            race_id,
            {
                "race_id": race_id,
                "race_no": row.get("race_no"),
                "started_at": row.get("started_at"),
                "entry_count": 0,
                "results": [],
            },
        )
        race["entry_count"] += 1
        race["results"].append(
            {
                "rank": row.get("finish_pos"),
                "sailor_name": row.get("sailor_name"),
                "boat_name": row.get("boat_name"),
                "sail_number": row.get("sail_number"),
                "elapsed_time": _secs_to_hms(row.get("elapsed_sec")),
                "corrected_time": _secs_to_hms(row.get("corrected_sec")),
                "did_not_finish": bool(row.get("did_not_finish")),
            }
        )

        sailor_key = row.get("sailor_id") or f"name:{row.get('sailor_name')}"
        sailor = item["_sailor_map"].setdefault(
            sailor_key,
            {
                "sailor_id": row.get("sailor_id"),
                "sailor_name": row.get("sailor_name"),
                "boat_name": row.get("boat_name"),
                "race_lookup": {},
            },
        )
        sailor["race_lookup"][race_id] = {
            "finish_pos": row.get("finish_pos"),
            "did_not_finish": bool(row.get("did_not_finish")),
        }

    output = []
    for item in grouped.values():
        races = sorted(
            item["_race_map"].values(),
            key=lambda r: (r.get("started_at") or date.min, int(r.get("race_no") or 0), int(r.get("race_id") or 0)),
        )
        series_entry_count = len(item["_sailor_map"])

        race_headers = []
        for race in races:
            race_headers.append(
                {
                    "race_id": race.get("race_id"),
                    "race_no": race.get("race_no"),
                    "started_at": race.get("started_at"),
                    "label": f"R{race.get('race_no')}",
                }
            )

            sorted_results = []
            for result in race.get("results", []):
                if result.get("rank") is not None:
                    points_value = float(result.get("rank"))
                    result_text = _format_series_points(points_value)
                else:
                    points_value = float((race.get("entry_count") or 0) + 1)
                    suffix = "DNF" if result.get("did_not_finish") else "DNC"
                    result_text = f"{_format_series_points(points_value)} {suffix}"

                sorted_results.append(
                    {
                        "rank": result.get("rank"),
                        "rank_text": _format_series_points(result.get("rank")) if result.get("rank") is not None else "",
                        "sailor_name": result.get("sailor_name"),
                        "boat_name": result.get("boat_name"),
                        "sail_number": result.get("sail_number"),
                        "elapsed_time": result.get("elapsed_time"),
                        "corrected_time": result.get("corrected_time"),
                        "points": result_text,
                    }
                )

            race["results"] = sorted(
                sorted_results,
                key=lambda r: (r.get("rank") is None, float(r.get("rank") or 999999), r.get("sailor_name") or ""),
            )

        standings = []
        status_priority = {"finish": 0, "dnf": 1, "dnc": 2}

        for sailor in item["_sailor_map"].values():
            races_completed = 0
            race_results = []

            for race in races:
                race_default_points = float((race.get("entry_count") or 0) + 1)
                series_default_points = float(series_entry_count + 1)
                cell = sailor["race_lookup"].get(race.get("race_id"))

                if cell and cell.get("finish_pos") is not None:
                    score = float(cell.get("finish_pos"))
                    races_completed += 1
                    race_results.append(
                        {
                            "race_id": race.get("race_id"),
                            "score": score,
                            "text": _format_series_points(score),
                            "status": "finish",
                            "discarded": False,
                        }
                    )
                elif cell and cell.get("did_not_finish"):
                    race_results.append(
                        {
                            "race_id": race.get("race_id"),
                            "score": race_default_points,
                            "text": f"{_format_series_points(race_default_points)} DNF",
                            "status": "dnf",
                            "discarded": False,
                        }
                    )
                else:
                    race_results.append(
                        {
                            "race_id": race.get("race_id"),
                            "score": series_default_points,
                            "text": f"{_format_series_points(series_default_points)} DNC",
                            "status": "dnc",
                            "discarded": False,
                        }
                    )

            discard_slots = min(int(item.get("discard_count") or 0), len(race_results))
            discard_order = sorted(
                enumerate(race_results),
                key=lambda pair: (float(pair[1].get("score") or 0), status_priority.get(pair[1].get("status"), 0), pair[0]),
                reverse=True,
            )
            discard_indexes = {idx for idx, _ in discard_order[:discard_slots]}

            total_points = 0.0
            for idx, result in enumerate(race_results):
                if idx in discard_indexes:
                    result["discarded"] = True
                    result["text"] = f"({result['text']})"
                else:
                    total_points += float(result.get("score") or 0)

            standings.append(
                {
                    "sailor_id": sailor.get("sailor_id"),
                    "sailor_name": sailor.get("sailor_name"),
                    "boat_name": sailor.get("boat_name"),
                    "points": round(total_points, 1),
                    "points_text": _format_series_points(total_points),
                    "races_completed": races_completed,
                    "race_results": race_results,
                }
            )

        standings.sort(key=lambda r: (float(r.get("points") or 999999), -int(r.get("races_completed") or 0), r.get("sailor_name") or ""))
        for idx, standing in enumerate(standings, start=1):
            standing["rank"] = idx

        item["results"] = standings
        item["races"] = race_headers
        item["race_sections"] = [
            {
                "race_id": race.get("race_id"),
                "race_no": race.get("race_no"),
                "started_at": race.get("started_at"),
                "entry_count": race.get("entry_count"),
                "results": race.get("results", []),
            }
            for race in races
        ]
        item.pop("_race_map", None)
        item.pop("_sailor_map", None)
        output.append(item)

    return sorted(
        output,
        key=lambda s: (s.get("latest_started_at") or date.min, s.get("series_name") or ""),
        reverse=True,
    )


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
                    full_name = f"Sailor #{sid}"
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
        return error_payload_for_exception(exc)


def dashboard_landing_overview(db, club_id):
    try:
        with db.engine.connect() as conn:
            latest_rows = _normalize_rows_by_race(get_latest_race_results_rows(conn, club_id))
            stats = get_club_summary_stats(conn, club_id)
            series_rows = get_series_results_rows(conn, club_id)

        latest_results = []
        for row in latest_rows:
            latest_results.append(
                {
                    "race_id": row.get("race_id"),
                    "race_no": row.get("race_no"),
                    "series_name": row.get("series_name"),
                    "started_at": row.get("started_at"),
                    "sailor": row.get("sailor"),
                    "boat": row.get("boat"),
                    "sail_number": row.get("sail_number"),
                    "position": row.get("position"),
                    "corrected_time": _secs_to_hms(row.get("corrected_sec")),
                }
            )

        series_groups = _group_series_results(series_rows)
        latest_series = series_groups[0] if series_groups else None

        return {
            "ok": True,
            "latest_results": latest_results,
            "latest_series": latest_series,
            "summary": dict(stats or {}),
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


def dashboard_series_results(db, club_id):
    try:
        with db.engine.connect() as conn:
            rows = get_series_results_rows(conn, club_id)
        series_groups = _group_series_results(rows)
        return {
            "ok": True,
            "series": series_groups,
            "latest_series_id": series_groups[0].get("series_id") if series_groups else None,
        }, 200
    except Exception as exc:
        return error_payload_for_exception(exc)


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
        return error_payload_for_exception(exc)


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
        return error_payload_for_exception(exc)


def dashboard_results_review_queue(db, club_id, args):
    try:
        limit = int(args.get("limit") or 200)
        with db.engine.connect() as conn:
            rows = get_results_review_queue_rows(conn, club_id, limit)
        return {"ok": True, "queue": [dict(r) for r in rows]}, 200
    except ValueError:
        return {"ok": False, "error": "Invalid query parameters"}, 400
    except Exception as exc:
        return error_payload_for_exception(exc)


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
        return error_payload_for_exception(exc)


def dashboard_export_results_csv(db, club_id, race_id):
    try:
        with db.engine.connect() as conn:
            if not race_belongs_to_club(conn, race_id, club_id):
                return {"ok": False, "error": "Race not found"}, 404
            rows = _normalize_rows_to_max_laps(get_export_results_rows(conn, race_id))

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
        return error_payload_for_exception(exc)


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
        return error_payload_for_exception(exc)


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
