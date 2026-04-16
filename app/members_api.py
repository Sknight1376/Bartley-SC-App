from services.schema_validation import validate_member_boat_payload, validate_member_payload
from services.members_repository import (
    get_boat_catalog,
    get_members_with_boats,
    insert_member,
    insert_member_boat,
    member_exists,
    update_member,
)
from services.members_repository import (
    confirm_app_registration,
    delete_orphaned_sailor,
    get_app_registrations,
    link_app_user_to_member,
)


def members_list(db, club_id):
    if not club_id:
        return {"ok": False, "error": "Unauthorized"}, 401

    try:
        with db.engine.connect() as conn:
            rows = get_members_with_boats(conn, club_id)

        members = {}
        for row in rows:
            sid = str(row["sailor_id"])
            if sid not in members:
                members[sid] = {
                    "id": row["sailor_id"],
                    "full_name": row["fullname"],
                    "first_name": row["firstname"],
                    "last_name": row["lastname"],
                    "boats": [],
                }
                members[sid]["sailor_user_id"] = row["sailor_user_id"]
                members[sid]["app_username"] = row["app_username"]
                members[sid]["app_is_active"] = row["app_is_active"]
                members[sid]["app_last_login"] = (
                    row["app_last_login"].isoformat() if row["app_last_login"] else None
                )
            if row["boat_key"] is not None:
                members[sid]["boats"].append(
                    {
                        "boat_key": row["boat_key"],
                        "boat": row["boat_name"],
                        "sail_number": row["sail_number"],
                        "handicap": row["handicap"],
                    }
                )

        return {"ok": True, "members": list(members.values())}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_create(db, club_id, payload):
    try:
        validated = validate_member_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    first_name = validated["first_name"]
    last_name = validated["last_name"]

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            sailor_id = insert_member(conn, full_name, first_name, last_name or None, club_id)
        return {"ok": True, "member_id": sailor_id}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_update(db, member_id, club_id, payload):
    try:
        validated = validate_member_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    first_name = validated["first_name"]
    last_name = validated["last_name"]

    full_name = f"{first_name} {last_name}".strip()

    try:
        with db.engine.begin() as conn:
            result = update_member(conn, member_id, club_id, full_name, first_name, last_name or None)

        if result.rowcount == 0:
            return {"ok": False, "error": "Member not found"}, 404
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_boat_catalog(db):
    try:
        with db.engine.connect() as conn:
            rows = get_boat_catalog(conn)

        boats = [{"key": r["key"], "boat": r["boat"], "handicap": r["handicap"]} for r in rows]
        return {"ok": True, "boats": boats}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_assign_boat(db, member_id, club_id, payload):
    try:
        validated = validate_member_boat_payload(payload)
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400

    handicap_key = validated["handicap_key"]
    sail_number = validated["sail_number"]

    try:
        with db.engine.begin() as conn:
            if not member_exists(conn, member_id, club_id):
                return {"ok": False, "error": "Member not found"}, 404

            boat_key = insert_member_boat(conn, handicap_key, member_id, sail_number)

        return {"ok": True, "boat_key": boat_key}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_app_registrations(db, club_id):
    if not club_id:
        return {"ok": False, "error": "Unauthorized"}, 401
    try:
        with db.engine.connect() as conn:
            rows = get_app_registrations(conn, club_id)
        result = [
            {
                "sailor_id": r["sailor_id"],
                "full_name": r["fullname"],
                "first_name": r["firstname"],
                "last_name": r["lastname"],
                "sailor_user_id": r["sailor_user_id"],
                "app_username": r["app_username"],
                "registered_at": r["registered_at"].isoformat() if r["registered_at"] else None,
            }
            for r in rows
        ]
        return {"ok": True, "registrations": result}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_confirm_app_user(db, sailor_user_id, club_id):
    if not club_id:
        return {"ok": False, "error": "Unauthorized"}, 401
    try:
        with db.engine.begin() as conn:
            result = confirm_app_registration(conn, sailor_user_id, club_id)
        if result.rowcount == 0:
            return {"ok": False, "error": "Registration not found or already confirmed"}, 404
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


def members_link_app_user(db, sailor_user_id, club_id, payload):
    if not club_id:
        return {"ok": False, "error": "Unauthorized"}, 401
    target_sailor_id = payload.get("target_sailor_id")
    if not target_sailor_id:
        return {"ok": False, "error": "target_sailor_id is required"}, 400
    try:
        with db.engine.begin() as conn:
            old_sailor_id = link_app_user_to_member(conn, sailor_user_id, int(target_sailor_id), club_id)
            if old_sailor_id and int(old_sailor_id) != int(target_sailor_id):
                try:
                    delete_orphaned_sailor(conn, old_sailor_id, club_id)
                except Exception:
                    pass  # cleanup is best-effort; the link itself has already succeeded
        return {"ok": True}, 200
    except ValueError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
