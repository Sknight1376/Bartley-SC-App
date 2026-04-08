from sqlalchemy import create_engine, text

engine = create_engine("postgresql://dwh:DBTTEST@localhost:5432/dwh")

def table_exists(conn, table_name: str) -> bool:
    q = text("SELECT to_regclass(:reg)")
    reg = f'"RACINGAPP"."{table_name}"'
    return conn.execute(q, {"reg": reg}).scalar() is not None

with engine.begin() as conn:
    deleted = {}
    for t in ["SERIES_EXCEPTION", "SERIES_RULE", "RACE", "SERIESCONTROL"]:
        if table_exists(conn, t):
            rc = conn.execute(text(f'DELETE FROM "RACINGAPP"."{t}"'))
            deleted[t] = rc.rowcount
        else:
            deleted[t] = None

print({"ok": True, "deleted": deleted})
