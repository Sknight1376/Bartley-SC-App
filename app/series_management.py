from services.schema_validation import validate_series_rule_payload
from services.series_repository import fetch_series_rules, insert_series_rule, set_series_year


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
