from services.mobile_repository import resolve_sailor_club_id, get_assigned_race_ids


def build_control_access_response(db, session_dict, sailor_has_active_role):
    sailor_user_id = session_dict.get("sailor_user_id")
    sailor_id = session_dict.get("sailor_id")
    club_id = session_dict.get("sailor_club_id")

    if not sailor_user_id or not sailor_id:
        return {"ok": False, "error": "Unauthorized"}, 401

    try:
        with db.engine.connect() as conn:
            if not club_id:
                club_id = resolve_sailor_club_id(conn, sailor_id)
                if club_id:
                    session_dict["sailor_club_id"] = str(club_id)

            if not club_id:
                return {"ok": True, "can_race_control": False, "assigned_race_ids": []}, 200

            is_mobile_admin = sailor_has_active_role(conn, sailor_user_id, sailor_id, club_id, "club_admin")
            assigned_race_ids = get_assigned_race_ids(conn, club_id, sailor_id)

        return {
            "ok": True,
            "can_race_control": bool(is_mobile_admin or assigned_race_ids),
            "is_mobile_admin": bool(is_mobile_admin),
            "assigned_race_ids": assigned_race_ids,
        }, 200
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
