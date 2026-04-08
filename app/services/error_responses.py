from sqlalchemy.exc import DBAPIError, OperationalError


def is_db_disconnect_error(exc):
    if isinstance(exc, (OperationalError, DBAPIError)):
        return True

    message = str(exc).lower()
    markers = (
        "connection to server",
        "could not connect to server",
        "connection refused",
        "server closed the connection",
        "terminating connection",
        "ssl syscall error",
        "connection not open",
    )
    return any(marker in message for marker in markers)


def error_payload_for_exception(exc, fallback_status=500):
    if is_db_disconnect_error(exc):
        return {
            "ok": False,
            "error": "Database unavailable. Please try again shortly.",
            "error_code": "DB_UNAVAILABLE",
        }, 503

    return {"ok": False, "error": str(exc)}, fallback_status
