#!/usr/bin/env python3
import psycopg2

DB_URL = 'postgresql://dwh:DBTTEST@localhost:5432/dwh'

STATEMENTS = [
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."ROLE" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        code VARCHAR(64) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        description TEXT NULL,
        actor_scope VARCHAR(32) NOT NULL DEFAULT 'both'
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."CLUB_USER_ROLE" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        club_user BIGINT NOT NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
        club BIGINT NOT NULL REFERENCES "RACINGAPP"."CLUBCONTROL"(key),
        role BIGINT NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
        granted_by BIGINT NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
        granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE (club_user, club, role)
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."SAILOR_ROLE_GRANT" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        sailor_user BIGINT NOT NULL REFERENCES "RACINGAPP"."SAILORUSER"(key),
        sailor BIGINT NOT NULL REFERENCES "RACINGAPP"."SAILORCONTROL"(key),
        club BIGINT NULL REFERENCES "RACINGAPP"."CLUBCONTROL"(key),
        role BIGINT NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
        valid_from TIMESTAMP NULL,
        valid_to TIMESTAMP NULL,
        granted_by BIGINT NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
        grant_reason TEXT NULL,
        granted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."RACE_RESULT_REVISION" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        race_id BIGINT NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
        revision_no INT NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'draft',
        source_mode VARCHAR(32) NOT NULL DEFAULT 'live',
        reason TEXT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by_user BIGINT NULL,
        created_by_type VARCHAR(32) NULL,
        based_on_revision_id BIGINT NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key),
        snapshot_json JSONB NULL,
        UNIQUE (race_id, revision_no)
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        race_id BIGINT NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
        sailor BIGINT NOT NULL REFERENCES "RACINGAPP"."SAILORCONTROL"(key),
        sailor_user BIGINT NULL REFERENCES "RACINGAPP"."SAILORUSER"(key),
        role BIGINT NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
        duty_type VARCHAR(64) NOT NULL DEFAULT 'race_officer',
        starts_at TIMESTAMP NULL,
        ends_at TIMESTAMP NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'assigned',
        assigned_by BIGINT NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
        notes TEXT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (race_id, sailor, role)
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS "RACINGAPP"."RACE_RESULT_AUDIT" (
        key BIGINT PRIMARY KEY DEFAULT nextval('key'),
        race_id BIGINT NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
        revision_id BIGINT NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key) ON DELETE SET NULL,
        entity_type VARCHAR(64) NOT NULL,
        entity_id BIGINT NULL,
        action VARCHAR(64) NOT NULL,
        actor_type VARCHAR(32) NOT NULL,
        actor_user_id BIGINT NULL,
        actor_sailor_id BIGINT NULL,
        reason TEXT NULL,
        before_json JSONB NULL,
        after_json JSONB NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    'ALTER TABLE "RACINGAPP"."RACE" ADD COLUMN IF NOT EXISTS results_status VARCHAR(32) NOT NULL DEFAULT \'draft\'',
    'ALTER TABLE "RACINGAPP"."RACE" ADD COLUMN IF NOT EXISTS results_locked_at TIMESTAMP NULL',
    'ALTER TABLE "RACINGAPP"."RACE" ADD COLUMN IF NOT EXISTS results_locked_by BIGINT NULL',
    'ALTER TABLE "RACINGAPP"."RACE" ADD COLUMN IF NOT EXISTS source_mode VARCHAR(32) NOT NULL DEFAULT \'live\'',
    'ALTER TABLE "RACINGAPP"."RACE_ENTRY" ADD COLUMN IF NOT EXISTS created_by_user BIGINT NULL',
    'ALTER TABLE "RACINGAPP"."RACE_ENTRY" ADD COLUMN IF NOT EXISTS created_by_type VARCHAR(32) NULL',
    'ALTER TABLE "RACINGAPP"."RACE_ENTRY" ADD COLUMN IF NOT EXISTS source VARCHAR(32) NULL',
    'ALTER TABLE "RACINGAPP"."RACE_ENTRY" ADD COLUMN IF NOT EXISTS revision_id BIGINT NULL',
    'ALTER TABLE "RACINGAPP"."LAP" ADD COLUMN IF NOT EXISTS created_by_user BIGINT NULL',
    'ALTER TABLE "RACINGAPP"."LAP" ADD COLUMN IF NOT EXISTS created_by_type VARCHAR(32) NULL',
    'ALTER TABLE "RACINGAPP"."LAP" ADD COLUMN IF NOT EXISTS source VARCHAR(32) NULL',
    'ALTER TABLE "RACINGAPP"."LAP" ADD COLUMN IF NOT EXISTS revision_id BIGINT NULL',
    'CREATE INDEX IF NOT EXISTS idx_club_user_role_club ON "RACINGAPP"."CLUB_USER_ROLE" (club)',
    'CREATE INDEX IF NOT EXISTS idx_sailor_role_grant_sailor ON "RACINGAPP"."SAILOR_ROLE_GRANT" (sailor)',
    'CREATE INDEX IF NOT EXISTS idx_sailor_role_grant_role ON "RACINGAPP"."SAILOR_ROLE_GRANT" (role)',
    'CREATE INDEX IF NOT EXISTS idx_race_duty_assignment_race ON "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (race_id)',
    'CREATE INDEX IF NOT EXISTS idx_race_duty_assignment_sailor ON "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (sailor)',
    'CREATE INDEX IF NOT EXISTS idx_race_result_audit_race ON "RACINGAPP"."RACE_RESULT_AUDIT" (race_id)',
    'CREATE INDEX IF NOT EXISTS idx_race_result_revision_race ON "RACINGAPP"."RACE_RESULT_REVISION" (race_id)',
]

ROLE_SEEDS = [
    ('club_admin', 'Club Admin', 'Full club administration and result approval rights', 'club_user'),
    ('race_officer', 'Race Officer', 'Operational race control access for assigned races', 'both'),
    ('sailor', 'Sailor', 'Standard sailor application access', 'sailor_user'),
]


def main() -> int:
    conn = psycopg2.connect(DB_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                for statement in STATEMENTS:
                    cur.execute(statement)

                for code, name, description, actor_scope in ROLE_SEEDS:
                    cur.execute(
                        '''
                        INSERT INTO "RACINGAPP"."ROLE" (key, code, name, description, actor_scope)
                        VALUES (nextval('key'), %s, %s, %s, %s)
                        ON CONFLICT (code) DO UPDATE
                        SET name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            actor_scope = EXCLUDED.actor_scope
                        ''',
                        (code, name, description, actor_scope),
                    )
        print('✓ P0 operational schema migration applied')
        return 0
    except Exception as exc:
        print(f'✗ Migration failed: {exc}')
        return 1
    finally:
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
