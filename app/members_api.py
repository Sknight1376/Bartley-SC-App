from services.schema_validation import validate_member_boat_payload, validate_member_payload
from services.members_repository import (
    get_boat_catalog,
    get_members_with_boats,
    insert_member,
    insert_member_boat,
    member_exists,
    update_member,
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
