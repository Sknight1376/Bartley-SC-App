from services.duty_repository import (
    delete_duty_assignment,
    get_races_by_date_range,
    get_race_duties,
    get_sailor_for_club,
    get_sailor_user_id,
)
from services.race_control_repository import get_race_for_club


def list_race_duties(db, race_id, club_id):
    try:
        with db.engine.connect() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404
            rows = get_race_duties(conn, race_id)
        return {"ok": True, "race_id": race_id, "duties": [dict(r) for r in rows]}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def assign_race_duty(
    db,
    race_id,
    payload,
    club_id,
    actor,
    parse_iso_datetime,
    resolve_role_id,
    upsert_race_duty_assignment,
    write_race_audit,
):
    sailor_id = payload.get("sailor_id")
    role_code = (payload.get("role_code") or "race_officer").strip()
    duty_type = (payload.get("duty_type") or role_code).strip() or "race_officer"
    status = (payload.get("status") or "assigned").strip() or "assigned"
    notes = (payload.get("notes") or "").strip() or None

    try:
        starts_at = parse_iso_datetime(payload.get("starts_at"), "starts_at")
        ends_at = parse_iso_datetime(payload.get("ends_at"), "ends_at")
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    if not sailor_id:
        return {"ok": False, "error": "sailor_id is required"}, 400

    try:
        sailor_id_int = int(sailor_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Invalid sailor_id"}, 400

    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404

            sailor_row = get_sailor_for_club(conn, sailor_id_int, club_id)
            if not sailor_row:
                return {"ok": False, "error": "Sailor not found"}, 404
            if str(sailor_row["club"]) != str(club_id):
                return {"ok": False, "error": "Sailor does not belong to this club"}, 403

            role_id = resolve_role_id(conn, role_code)
            if not role_id:
                return {"ok": False, "error": "Unknown role_code"}, 400

            sailor_user_id = get_sailor_user_id(conn, sailor_id_int)

            duty_id = upsert_race_duty_assignment(
                conn,
                race_id=race_id,
                sailor_id=sailor_id_int,
                sailor_user_id=sailor_user_id,
                role_id=role_id,
                duty_type=duty_type,
                starts_at=starts_at,
                ends_at=ends_at,
                status=status,
                assigned_by=actor.get("actor_user_id"),
                notes=notes,
            )

            write_race_audit(
                conn, race_id, actor,
                entity_type="duty", entity_id=duty_id,
                action="duty_assigned",
                after_obj={
                    "duty_id": duty_id,
                    "sailor_id": sailor_id_int,
                    "role_code": role_code,
                    "duty_type": duty_type,
                    "status": status,
                },
            )

        return {
            "ok": True,
            "race_id": race_id,
            "duty_id": duty_id,
            "granted_by": actor.get("actor_user_id"),
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def assign_race_duty_by_date(
    db,
    payload,
    club_id,
    actor,
    parse_iso_datetime,
    parse_date_yyyy_mm_dd,
    resolve_role_id,
    upsert_race_duty_assignment,
    write_race_audit,
):
    from datetime import date as _date

    sailor_id = payload.get("sailor_id")
    role_code = (payload.get("role_code") or "race_officer").strip()
    duty_type = (payload.get("duty_type") or role_code).strip() or "race_officer"
    status = (payload.get("status") or "assigned").strip() or "assigned"
    notes = (payload.get("notes") or "").strip() or None

    date_raw = (payload.get("date") or "").strip()
    from_raw = (payload.get("from_date") or "").strip()
    to_raw = (payload.get("to_date") or "").strip()

    try:
        starts_at = parse_iso_datetime(payload.get("starts_at"), "starts_at")
        ends_at = parse_iso_datetime(payload.get("ends_at"), "ends_at")
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    if not sailor_id:
        return {"ok": False, "error": "sailor_id is required"}, 400

    try:
        sailor_id_int = int(sailor_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Invalid sailor_id"}, 400

    try:
        if date_raw:
            from_date = parse_date_yyyy_mm_dd(date_raw, "date")
            to_date = from_date
        else:
            from_date = parse_date_yyyy_mm_dd(from_raw, "from_date") if from_raw else _date.today()
            to_date = parse_date_yyyy_mm_dd(to_raw, "to_date") if to_raw else from_date
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400

    if to_date < from_date:
        return {"ok": False, "error": "to_date cannot be before from_date"}, 400

    try:
        with db.engine.begin() as conn:
            sailor_row = get_sailor_for_club(conn, sailor_id_int, club_id)
            if not sailor_row:
                return {"ok": False, "error": "Sailor not found"}, 404
            if str(sailor_row["club"]) != str(club_id):
                return {"ok": False, "error": "Sailor does not belong to this club"}, 403

            role_id = resolve_role_id(conn, role_code)
            if not role_id:
                return {"ok": False, "error": "Unknown role_code"}, 400

            sailor_user_id = get_sailor_user_id(conn, sailor_id_int)

            race_rows = get_races_by_date_range(conn, club_id, from_date, to_date)

            assigned_race_ids = []
            duty_ids = []
            for race_row in race_rows:
                rid = race_row["key"]
                duty_id = upsert_race_duty_assignment(
                    conn,
                    race_id=rid,
                    sailor_id=sailor_id_int,
                    sailor_user_id=sailor_user_id,
                    role_id=role_id,
                    duty_type=duty_type,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    status=status,
                    assigned_by=actor.get("actor_user_id"),
                    notes=notes,
                )
                assigned_race_ids.append(rid)
                duty_ids.append(duty_id)

                write_race_audit(
                    conn, rid, actor,
                    entity_type="duty", entity_id=duty_id,
                    action="duty_assigned_by_date",
                    after_obj={
                        "duty_id": duty_id,
                        "sailor_id": sailor_id_int,
                        "role_code": role_code,
                        "duty_type": duty_type,
                        "status": status,
                        "from_date": from_date.isoformat(),
                        "to_date": to_date.isoformat(),
                    },
                )

        return {
            "ok": True,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "sailor_id": sailor_id_int,
            "granted_by": actor.get("actor_user_id"),
            "assigned_count": len(assigned_race_ids),
            "assigned_race_ids": assigned_race_ids,
            "duty_ids": duty_ids,
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500


def delete_race_duty(db, race_id, duty_id, club_id, actor, write_race_audit):
    try:
        with db.engine.begin() as conn:
            race_row = get_race_for_club(conn, race_id, club_id)
            if not race_row:
                return {"ok": False, "error": "Race not found"}, 404

            deleted = delete_duty_assignment(conn, duty_id, race_id)
            if deleted.rowcount == 0:
                return {"ok": False, "error": "Duty assignment not found"}, 404

            write_race_audit(
                conn, race_id, actor,
                entity_type="duty", entity_id=duty_id,
                action="duty_removed",
                after_obj={"duty_id": duty_id},
            )

        return {"ok": True, "race_id": race_id, "duty_id": duty_id}, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
