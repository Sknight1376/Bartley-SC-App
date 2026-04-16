import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "app"))

import app as app_module
from sqlalchemy import text

DDL_STATEMENTS = [
    'CREATE INDEX IF NOT EXISTS idx_race_club_started ON "RACINGAPP"."RACE" (club, started_at DESC, key DESC)',
    'CREATE INDEX IF NOT EXISTS idx_race_club_status_started ON "RACINGAPP"."RACE" (club, status, started_at DESC, key DESC)',
    'CREATE INDEX IF NOT EXISTS idx_race_entry_race ON "RACINGAPP"."RACE_ENTRY" (race_id)',
    'CREATE INDEX IF NOT EXISTS idx_lap_entry_finish ON "RACINGAPP"."LAP" (race_entry_id, is_finish, lap_number)',
    'CREATE INDEX IF NOT EXISTS idx_sailorcontrol_club ON "RACINGAPP"."SAILORCONTROL" (club)',
    'CREATE INDEX IF NOT EXISTS idx_boatcontrol_sailor ON "RACINGAPP"."BOATCONTROL" (sailor)',
    'CREATE INDEX IF NOT EXISTS idx_boatcontrol_boat ON "RACINGAPP"."BOATCONTROL" (boat)',
    'CREATE INDEX IF NOT EXISTS idx_seriescontrol_club_year_name ON "RACINGAPP"."SERIESCONTROL" (club, year DESC, name)',
    'CREATE INDEX IF NOT EXISTS idx_sailoruser_active_username ON "RACINGAPP"."SAILORUSER" ((LOWER(username))) WHERE is_active = TRUE',
    'CREATE INDEX IF NOT EXISTS idx_clubuser_active_username ON "RACINGAPP"."CLUBUSER" ((LOWER(username))) WHERE is_active = TRUE',
    'CREATE INDEX IF NOT EXISTS idx_race_result_audit_entity_created ON "RACINGAPP"."RACE_RESULT_AUDIT" (entity_type, created_at DESC)',
]


def main():
    with app_module.db.engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            conn.execute(text(ddl))
        conn.execute(text('ANALYZE "RACINGAPP"."RACE"'))
        conn.execute(text('ANALYZE "RACINGAPP"."RACE_ENTRY"'))
        conn.execute(text('ANALYZE "RACINGAPP"."LAP"'))
    print(f"Applied {len(DDL_STATEMENTS)} database hardening statements.")


if __name__ == "__main__":
    main()
