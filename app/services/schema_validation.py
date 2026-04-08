def validate_series_rule_payload(payload, parse_weekday, parse_time_hh_mm, parse_time_list_hh_mm, parse_date_yyyy_mm_dd, calculate_rule_end_date):
    weekday = parse_weekday(payload.get("weekday"))
    start_time = parse_time_hh_mm(payload.get("start_time"), "start_time")
    cadence_weeks = int(payload.get("cadence_weeks") or 1)
    races_per_day = int(payload.get("races_per_day") or 1)
    target_race_count = int(payload.get("race_count") or 0)
    additional_times = parse_time_list_hh_mm(payload.get("additional_start_times"), "additional_start_times")
    valid_from = parse_date_yyyy_mm_dd(payload.get("valid_from"), "valid_from")
    valid_to_raw = (payload.get("valid_to") or "").strip()
    is_active = bool(payload.get("is_active", True))

    valid_to = parse_date_yyyy_mm_dd(valid_to_raw, "valid_to") if valid_to_raw else None

    if cadence_weeks < 1 or races_per_day < 1:
        raise ValueError("cadence_weeks and races_per_day must be > 0")
    if target_race_count < 0:
        raise ValueError("race_count cannot be negative")
    if target_race_count > 0:
        valid_to = calculate_rule_end_date(valid_from, weekday, cadence_weeks, races_per_day, target_race_count)
    if not valid_to:
        raise ValueError("Provide race_count (>0) or valid_to")
    if valid_to and valid_to < valid_from:
        raise ValueError("valid_to cannot be before valid_from")
    if races_per_day > 1 and len(additional_times) != (races_per_day - 1):
        raise ValueError(f"Provide exactly {races_per_day - 1} additional_start_times value(s) in HH:MM")

    return {
        "weekday": weekday,
        "start_time": start_time,
        "cadence_weeks": cadence_weeks,
        "races_per_day": races_per_day,
        "target_race_count": target_race_count,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "is_active": is_active,
        "extra_start_times": ",".join([t.strftime("%H:%M") for t in additional_times]) if additional_times else None,
    }


def validate_lap_payload(payload, parse_hms_to_seconds):
    entry_id = payload.get("entry_id")
    lap_number = payload.get("lap_number")
    elapsed_time = payload.get("elapsed_time")
    corrected_time = payload.get("corrected_time")
    position = payload.get("position")
    is_finish = bool(payload.get("is_finish", False))

    if not all([entry_id, lap_number, elapsed_time]):
        raise ValueError("Missing required lap fields")

    elapsed_sec = parse_hms_to_seconds(elapsed_time)
    corrected_sec = parse_hms_to_seconds(corrected_time) if corrected_time and corrected_time != "N/A" else None

    return {
        "entry_id": entry_id,
        "lap_number": lap_number,
        "elapsed_sec": elapsed_sec,
        "corrected_sec": corrected_sec,
        "position": position,
        "is_finish": is_finish,
    }
