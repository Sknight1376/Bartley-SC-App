from datetime import date, datetime, time, timedelta

from services.schema_validation import (
    validate_series_basic_payload,
    validate_series_exception_payload,
    validate_series_rule_payload,
    validate_series_scoring_payload,
    validate_series_update_payload,
)
from services.series_repository import (
    delete_series_exception,
    delete_series_rule,
    delete_series_scoring_discard_rules,
    fetch_series_rules,
    find_series_by_name_year,
    get_series_by_id,
    get_series_scoring,
    get_series_year,
    get_max_race_no_for_series,
    insert_race,
    insert_series,
    insert_series_exception,
    insert_series_rule,
    insert_series_scoring_discard_rule,
    list_series_exceptions,
    list_series_manage_rows,
    list_series_races,
    list_series_scoring_discard_rules,
    set_series_year,
    update_series,
    update_series_exception,
    update_series_rule,
    upsert_series_scoring_low_point,
)


def list_series_rules(db, series_id, club_id, ensure_series_schedule_tables, check_series_access):
    try:
        with db.engine.connect() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            rows = fetch_series_rules(conn, series_id)

        rules = []
        for row in rows:
            item = dict(row)
            if item.get("start_time") is not None:
                item["start_time"] = item["start_time"].strftime("%H:%M")
            if item.get("valid_from") is not None:
                item["valid_from"] = item["valid_from"].isoformat()
            if item.get("valid_to") is not None:
                item["valid_to"] = item["valid_to"].isoformat()
            rules.append(item)

        return {"ok": True, "rules": rules}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def create_series_rule(
    db,
    payload,
    series_id,
    club_id,
    ensure_series_schedule_tables,
    check_series_access,
    parse_weekday,
    parse_time_hh_mm,
    parse_time_list_hh_mm,
    parse_date_yyyy_mm_dd,
    calculate_rule_end_date,
    recompute_series_rule_end_dates,
):
    try:
        values = validate_series_rule_payload(
            payload,
            parse_weekday,
            parse_time_hh_mm,
            parse_time_list_hh_mm,
            parse_date_yyyy_mm_dd,
            calculate_rule_end_date,
        )

        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            set_series_year(conn, series_id, club_id, values["valid_from"].year)
            rule_id = insert_series_rule(
                conn,
                series_id,
                {
                    **values,
                    "target_race_count": values["target_race_count"] if values["target_race_count"] > 0 else None,
                },
            )
            recompute_series_rule_end_dates(conn, series_id)

        return {"ok": True, "rule_id": rule_id}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def create_series_basic(db, club_id, payload):
    try:
        validated = validate_series_basic_payload(payload, date.today().year)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    year = validated["year"]
    name = validated["name"]

    try:
        with db.engine.begin() as conn:
            exists = find_series_by_name_year(conn, club_id, name, year)
            if exists:
                return {"ok": False, "error": "Series already exists for this club/year"}, 409
            series_id = insert_series(conn, year, name, club_id)
        return {"ok": True, "series_id": series_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def list_series(db, club_id, ensure_series_schedule_tables):
    try:
        with db.engine.connect() as conn:
            ensure_series_schedule_tables(conn)
            rows = list_series_manage_rows(conn, club_id)
        return {"ok": True, "series": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def get_series(db, series_id, club_id):
    try:
        with db.engine.connect() as conn:
            row = get_series_by_id(conn, series_id, club_id)
        if not row:
            return {"ok": False, "error": "Series not found"}, 404
        return {"ok": True, "series": dict(row)}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def create_series_with_schedule(db, club_id, payload):
    try:
        validated_basic = validate_series_basic_payload(payload, date.today().year)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    year = validated_basic["year"]
    name = validated_basic["name"]
    race_count = int(payload.get("race_count") or 0)
    day_of_week = (payload.get("day_of_week") or "Saturday").strip().lower()
    start_hour = int(payload.get("start_hour") or 11)
    start_minute = int(payload.get("start_minute") or 0)
    races_per_day = int(payload.get("races_per_day") or 1)
    start_date_raw = (payload.get("start_date") or "").strip()

    if race_count <= 0:
        return {"ok": False, "error": "race_count must be greater than 0"}, 400
    if races_per_day <= 0:
        return {"ok": False, "error": "races_per_day must be greater than 0"}, 400
    if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
        return {"ok": False, "error": "Invalid start time"}, 400

    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    target_weekday = weekday_map.get(day_of_week)
    if target_weekday is None:
        return {"ok": False, "error": "Invalid day_of_week"}, 400

    try:
        base_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date() if start_date_raw else datetime.now().date()
    except Exception:
        return {"ok": False, "error": "start_date must be YYYY-MM-DD"}, 400

    try:
        with db.engine.begin() as conn:
            exists = find_series_by_name_year(conn, club_id, name, year)
            if exists:
                return {"ok": False, "error": "Series already exists for this club/year"}, 409

            series_id = insert_series(conn, year, name, club_id)
            max_race_no = get_max_race_no_for_series(conn, series_id)

            days_to_add = (target_weekday - base_date.weekday()) % 7
            next_race_date = base_date + timedelta(days=days_to_add)

            created = 0
            race_no = int(max_race_no)
            while created < race_count:
                for slot in range(races_per_day):
                    if created >= race_count:
                        break

                    race_no += 1
                    scheduled_at = datetime.combine(
                        next_race_date,
                        time(hour=start_hour, minute=start_minute),
                    ) + timedelta(minutes=slot * 10)

                    insert_race(conn, club_id, series_id, race_no, scheduled_at)
                    created += 1

                next_race_date = next_race_date + timedelta(days=7)

        return {"ok": True, "series_id": series_id, "scheduled_races": race_count}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def update_series_metadata(db, series_id, club_id, payload):
    try:
        validated = validate_series_update_payload(payload)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    year = validated["year"]
    name = validated["name"]

    try:
        with db.engine.begin() as conn:
            if year is None:
                existing_year = get_series_year(conn, series_id, club_id)
                year = existing_year or str(date.today().year)
            updated = update_series(conn, series_id, club_id, year, name)

        if updated.rowcount == 0:
            return {"ok": False, "error": "Series not found"}, 404
        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def update_rule(
    db,
    payload,
    series_id,
    rule_id,
    club_id,
    ensure_series_schedule_tables,
    check_series_access,
    parse_weekday,
    parse_time_hh_mm,
    parse_time_list_hh_mm,
    parse_date_yyyy_mm_dd,
    calculate_rule_end_date,
    recompute_series_rule_end_dates,
):
    try:
        values = validate_series_rule_payload(
            payload,
            parse_weekday,
            parse_time_hh_mm,
            parse_time_list_hh_mm,
            parse_date_yyyy_mm_dd,
            calculate_rule_end_date,
        )

        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            set_series_year(conn, series_id, club_id, values["valid_from"].year)
            updated = update_series_rule(
                conn,
                rule_id,
                series_id,
                {
                    **values,
                    "target_race_count": values["target_race_count"] if values["target_race_count"] > 0 else None,
                },
            )

            if updated.rowcount == 0:
                return {"ok": False, "error": "Rule not found"}, 404

            recompute_series_rule_end_dates(conn, series_id)

        return {"ok": True, "rule_id": rule_id}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def delete_rule(db, series_id, rule_id, club_id, ensure_series_schedule_tables, check_series_access):
    try:
        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404
            deleted = delete_series_rule(conn, rule_id, series_id)

        if deleted.rowcount == 0:
            return {"ok": False, "error": "Rule not found"}, 404
        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def list_exceptions(db, series_id, club_id, ensure_series_schedule_tables, check_series_access):
    try:
        with db.engine.connect() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404
            rows = list_series_exceptions(conn, series_id)
        return {"ok": True, "exceptions": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def create_exception(
    db,
    payload,
    series_id,
    club_id,
    ensure_series_schedule_tables,
    check_series_access,
    parse_date_yyyy_mm_dd,
    recompute_series_rule_end_dates,
):
    try:
        validated = validate_series_exception_payload(payload, parse_date_yyyy_mm_dd)
        exception_date = validated["exception_date"]
        note = validated["note"]
        is_active = validated["is_active"]
        original_start_at = datetime.combine(exception_date, time(0, 0))

        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            exception_id = insert_series_exception(
                conn,
                series_id,
                exception_date,
                original_start_at,
                note,
                is_active,
            )
            recompute_series_rule_end_dates(conn, series_id)

        return {"ok": True, "exception_id": exception_id}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def update_exception(
    db,
    payload,
    series_id,
    exception_id,
    club_id,
    ensure_series_schedule_tables,
    check_series_access,
    parse_date_yyyy_mm_dd,
    recompute_series_rule_end_dates,
):
    try:
        validated = validate_series_exception_payload(payload, parse_date_yyyy_mm_dd)
        exception_date = validated["exception_date"]
        note = validated["note"]
        is_active = validated["is_active"]
        original_start_at = datetime.combine(exception_date, time(0, 0))

        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            updated = update_series_exception(
                conn,
                exception_id,
                series_id,
                exception_date,
                original_start_at,
                note,
                is_active,
            )
            if updated.rowcount == 0:
                return {"ok": False, "error": "Exception not found"}, 404

            recompute_series_rule_end_dates(conn, series_id)

        return {"ok": True, "exception_id": exception_id}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def delete_exception(
    db,
    series_id,
    exception_id,
    club_id,
    ensure_series_schedule_tables,
    check_series_access,
    recompute_series_rule_end_dates,
):
    try:
        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            deleted = delete_series_exception(conn, exception_id, series_id)
            if deleted.rowcount == 0:
                return {"ok": False, "error": "Exception not found"}, 404

            recompute_series_rule_end_dates(conn, series_id)

        return {"ok": True}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def get_scoring(db, series_id, club_id, ensure_series_schedule_tables, check_series_access):
    try:
        with db.engine.connect() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            row = get_series_scoring(conn, series_id)
            discard_rows = list_series_scoring_discard_rules(conn, series_id)

        scoring = dict(row) if row else {"scoring_system": "low_point", "discard_rules": []}
        scoring["scoring_system"] = "low_point"
        scoring["discard_rules"] = [dict(r) for r in discard_rows]
        scoring.pop("races_to_count", None)
        scoring.pop("discard_after_races", None)
        scoring.pop("discards_allowed", None)

        return {"ok": True, "scoring": scoring}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def save_scoring(db, payload, series_id, club_id, ensure_series_schedule_tables, check_series_access):
    try:
        normalized = validate_series_scoring_payload(payload)["discard_rules"]

        with db.engine.begin() as conn:
            ensure_series_schedule_tables(conn)
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404

            upsert_series_scoring_low_point(conn, series_id)
            delete_series_scoring_discard_rules(conn, series_id)

            for item in normalized:
                insert_series_scoring_discard_rule(
                    conn,
                    series_id,
                    item["discard_count"],
                    item["after_races"],
                )

        return {"ok": True}, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def generate_series_schedule(
    db,
    payload,
    series_id,
    club_id,
    parse_date_yyyy_mm_dd,
    check_series_access,
    generate_series_races,
):
    try:
        from_raw = (payload.get("from_date") or "").strip()
        to_raw = (payload.get("to_date") or "").strip()
        from_date = parse_date_yyyy_mm_dd(from_raw, "from_date") if from_raw else date.today()
        to_date = parse_date_yyyy_mm_dd(to_raw, "to_date") if to_raw else (from_date + timedelta(days=120))

        if to_date < from_date:
            return {"ok": False, "error": "to_date cannot be before from_date"}, 400

        with db.engine.begin() as conn:
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404
            summary = generate_series_races(conn, series_id, club_id, from_date, to_date)

        return {
            "ok": True,
            "series_id": series_id,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            **summary,
        }, 200
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def list_series_races_view(db, series_id, club_id, check_series_access):
    try:
        with db.engine.connect() as conn:
            if not check_series_access(conn, series_id, club_id):
                return {"ok": False, "error": "Series not found"}, 404
            rows = list_series_races(conn, series_id)

        races = []
        for row in rows:
            item = dict(row)
            if item.get("started_at") is not None:
                item["started_at"] = item["started_at"].isoformat()
            races.append(item)

        return {"ok": True, "races": races}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
