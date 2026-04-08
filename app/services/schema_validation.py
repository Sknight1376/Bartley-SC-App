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

    try:
        entry_id = int(entry_id)
        lap_number = int(lap_number)
    except (TypeError, ValueError):
        raise ValueError("entry_id and lap_number must be integers")

    if entry_id <= 0 or lap_number <= 0:
        raise ValueError("entry_id and lap_number must be > 0")

    elapsed_sec = parse_hms_to_seconds(elapsed_time)
    corrected_sec = parse_hms_to_seconds(corrected_time) if corrected_time and corrected_time != "N/A" else None

    normalized_position = None
    if position not in (None, "", "N/A"):
        try:
            normalized_position = int(position)
        except (TypeError, ValueError):
            raise ValueError("position must be an integer when provided")
        if normalized_position <= 0:
            raise ValueError("position must be > 0")

    return {
        "entry_id": entry_id,
        "lap_number": lap_number,
        "elapsed_sec": elapsed_sec,
        "corrected_sec": corrected_sec,
        "position": normalized_position,
        "is_finish": is_finish,
    }


def validate_race_start_payload(payload):
    club_id = payload.get("club_id")
    series_id = payload.get("series_id")
    selected_race_id = payload.get("race_id")
    entries = payload.get("entries")

    if club_id in (None, ""):
        raise ValueError("club_id is required")
    if series_id in (None, ""):
        raise ValueError("series_id is required")

    try:
        club_id = int(club_id)
        series_id = int(series_id)
    except (TypeError, ValueError):
        raise ValueError("club_id and series_id must be integers")

    race_id = None
    if selected_race_id not in (None, ""):
        try:
            race_id = int(selected_race_id)
        except (TypeError, ValueError):
            raise ValueError("race_id must be an integer when provided")

    if entries is not None and not isinstance(entries, list):
        raise ValueError("entries must be an array when provided")

    source_mode = (payload.get("source_mode") or "live").strip().lower()
    if source_mode not in ("live", "retrospective"):
        raise ValueError("source_mode must be 'live' or 'retrospective'")

    reason = (payload.get("reason") or "Web race start").strip() or "Web race start"

    return {
        "club_id": club_id,
        "series_id": series_id,
        "race_id": race_id,
        "entries": entries,
        "source_mode": source_mode,
        "reason": reason,
    }


def validate_control_start_payload(payload, default_reason):
    source_mode = (payload.get("source_mode") or "live").strip().lower()
    if source_mode not in ("live", "retrospective"):
        raise ValueError("source_mode must be 'live' or 'retrospective'")

    reason = (payload.get("reason") or default_reason).strip() or default_reason
    return {"source_mode": source_mode, "reason": reason}


def validate_race_entry_payload(payload):
    sailor = (payload.get("sailor") or "").strip()
    boat = (payload.get("boat") or "").strip()
    sail_number = (payload.get("sail_number") or payload.get("sailNumber") or "").strip()
    reason = (payload.get("reason") or "Entry added").strip() or "Entry added"

    if not sailor or not boat or not sail_number:
        raise ValueError("sailor, boat, and sail_number are required")

    raw_boatkey = payload.get("boatkey") or payload.get("key")
    boatkey = None
    if raw_boatkey not in (None, "", "null"):
        try:
            boatkey = int(raw_boatkey)
        except (TypeError, ValueError):
            raise ValueError("Invalid boatkey")

    handicap_raw = payload.get("handicap")
    handicap = None
    if handicap_raw not in (None, "", "N/A"):
        try:
            handicap = int(float(handicap_raw))
        except (TypeError, ValueError):
            raise ValueError("Invalid handicap")

    return {
        "sailor": sailor,
        "boat": boat,
        "sail_number": sail_number,
        "boatkey": boatkey,
        "handicap": handicap,
        "reason": reason,
    }


def validate_race_finish_payload(payload, default_reason):
    reason = (payload.get("reason") or default_reason).strip() or default_reason
    return {"reason": reason}


def validate_mobile_login_payload(payload):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        raise ValueError("Missing username or password")
    return {"username": username, "password": password}


def validate_mobile_register_payload(payload):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    club_id = payload.get("club_id")

    if not username or not password or not first_name:
        raise ValueError("username, password, and first_name are required")

    return {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "club_id": club_id,
    }


def validate_mobile_profile_update_payload(payload):
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    club_id = payload.get("club_id")
    if not first_name:
        raise ValueError("first_name is required")
    return {"first_name": first_name, "last_name": last_name, "club_id": club_id}


def validate_mobile_create_boat_payload(payload):
    boat_class_id = payload.get("boat_class_id")
    sail_number = (payload.get("sail_number") or "").strip()
    if not boat_class_id or not sail_number:
        raise ValueError("boat_class_id and sail_number are required")
    return {"boat_class_id": boat_class_id, "sail_number": sail_number}


def validate_mobile_join_race_payload(payload):
    boat_key = payload.get("boat_key")
    if not boat_key:
        raise ValueError("boat_key is required")
    return {"boat_key": boat_key}


def validate_member_payload(payload):
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    if not first_name:
        raise ValueError("first_name is required")
    return {"first_name": first_name, "last_name": last_name}


def validate_member_boat_payload(payload):
    handicap_key = payload.get("handicap_key")
    sail_number = (payload.get("sail_number") or "").strip()
    if not handicap_key or not sail_number:
        raise ValueError("handicap_key and sail_number are required")
    return {"handicap_key": handicap_key, "sail_number": sail_number}


def validate_series_basic_payload(payload, default_year):
    year = (payload.get("year") or "").strip() or str(default_year)
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Series name is required")
    return {"year": year, "name": name}


def validate_series_update_payload(payload):
    year = (payload.get("year") or "").strip() or None
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Series name is required")
    return {"year": year, "name": name}


def validate_series_exception_payload(payload, parse_date_yyyy_mm_dd):
    ex_date_raw = (payload.get("exception_date") or "").strip()
    note = (payload.get("note") or "").strip() or None
    is_active = bool(payload.get("is_active", True))
    if not ex_date_raw:
        raise ValueError("exception_date is required")
    exception_date = parse_date_yyyy_mm_dd(ex_date_raw, "exception_date")
    return {
        "exception_date": exception_date,
        "note": note,
        "is_active": is_active,
    }


def validate_series_scoring_payload(payload):
    discard_rules = payload.get("discard_rules") or []
    normalized = []
    seen_counts = set()

    for item in discard_rules:
        discard_count = int(item.get("discard_count"))
        after_races = int(item.get("after_races"))

        if discard_count < 1:
            raise ValueError("discard_count must be >= 1")
        if after_races < 1:
            raise ValueError("after_races must be >= 1")
        if discard_count in seen_counts:
            raise ValueError("duplicate discard_count values are not allowed")

        seen_counts.add(discard_count)
        normalized.append({"discard_count": discard_count, "after_races": after_races})

    normalized.sort(key=lambda x: x["discard_count"])
    prev_after = 0
    for idx, item in enumerate(normalized, start=1):
        if item["discard_count"] != idx:
            raise ValueError("discard_count must be sequential starting at 1")
        if item["after_races"] <= prev_after:
            raise ValueError("after_races must increase for each discard rule")
        prev_after = item["after_races"]

    return {"discard_rules": normalized}
