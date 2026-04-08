CREATE SCHEMA "RACINGAPP";
CREATE SEQUENCE key START 1;
CREATE EXTENSION IF NOT EXISTS pgcrypto;


CREATE TABLE "RACINGAPP"."SERIESCONTROL"
(
	key				bigint NOT NULL PRIMARY KEY,
	year			varchar(255) NULL,
	name			varchar(255) NOT NULL,
	club			varchar(255) NULL
);

CREATE TABLE "RACINGAPP"."CLUBCONTROL"
(
	key				bigint NOT NULL PRIMARY KEY,
	name			varchar(255) NOT NULL
);

CREATE TABLE "RACINGAPP"."CLUBUSER"
(
	key				bigint NOT NULL PRIMARY KEY,
	club			bigint NOT NULL REFERENCES "RACINGAPP"."CLUBCONTROL"(key),
	username		varchar(100) NOT NULL UNIQUE,
	password_hash		varchar(255) NOT NULL,
	is_active		boolean NOT NULL DEFAULT TRUE,
	created_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_login		timestamp NULL
);

CREATE TABLE "RACINGAPP"."SAILORUSER"
(
	key				bigint NOT NULL PRIMARY KEY,
	sailor			bigint NOT NULL,
	username		varchar(100) NOT NULL UNIQUE,
	password_hash		varchar(255) NOT NULL,
	is_active		boolean NOT NULL DEFAULT TRUE,
	created_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_login		timestamp NULL
);

CREATE TABLE "RACINGAPP"."SAILORCONTROL"
(
	key				bigint NOT NULL PRIMARY KEY,
	FullName		varchar(255) NOT NULL,
	FirstName 		varchar(255) NOT NULL,
	LastName		varchar(255) NULL,
	club			bigint
);

CREATE TABLE "RACINGAPP"."HANDICAPCONTROL"
(
	key				bigint NOT NULL PRIMARY KEY,
	date			DATE NOT NULL,
	boat			varchar(255) NOT NULL,
	handicap		int NOT NULL
);

CREATE TABLE "RACINGAPP"."BOATCONTROL"
(
	key				bigint NOT NULL PRIMARY KEY,
	boat			bigint NOT NULL,
	sailor			bigint NOT NULL,
	sail_number		varchar(255) NOT NULL
);

CREATE TABLE "RACINGAPP"."RACE"
(
	key				bigint NOT NULL PRIMARY KEY,
	club			bigint NOT NULL,
	series			bigint NOT NULL,
	race_no			int NOT NULL,
	status			varchar(50) NOT NULL DEFAULT 'not_started',
	started_at		timestamp NULL,
	ended_at		timestamp NULL
);

CREATE TABLE "RACINGAPP"."RACE_ENTRY"
(
	key				bigint NOT NULL PRIMARY KEY,
	race_id			bigint NOT NULL REFERENCES "RACINGAPP"."RACE"(key),
	boatkey			bigint NOT NULL,
	sailor			varchar(255) NOT NULL,
	boat			varchar(255) NOT NULL,
	sail_number		varchar(255) NOT NULL,
	handicap		int NULL
);

CREATE TABLE "RACINGAPP"."LAP"
(
	key				bigint NOT NULL PRIMARY KEY,
	race_entry_id		bigint NOT NULL REFERENCES "RACINGAPP"."RACE_ENTRY"(key),
	lap_number		int NOT NULL,
	is_finish		boolean NOT NULL DEFAULT FALSE,
	elapsed_sec		int NOT NULL,
	corrected_sec		int NULL,
	position		int NULL,
	recorded_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT lap_unique_entry_number_finish UNIQUE (race_entry_id, lap_number, is_finish)
);

CREATE TEMPORARY TABLE temp_dest (boat varchar(255), handicap int);

COPY temp_dest(boat, handicap) FROM '/var/handicaps.csv' DELIMITER ',' csv header;

INSERT INTO "RACINGAPP"."HANDICAPCONTROL"
SELECT nextval('key'), current_timestamp, boat, handicap
FROM temp_dest;

ALTER TABLE "RACINGAPP"."SAILORUSER"
	ADD CONSTRAINT sailoruser_sailor_fk
	FOREIGN KEY (sailor)
	REFERENCES "RACINGAPP"."SAILORCONTROL"(key);

ALTER TABLE "RACINGAPP"."RACE"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."CLUBUSER"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."SAILORUSER"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."RACE_ENTRY"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."LAP"
	ALTER COLUMN key SET DEFAULT nextval('key');

CREATE TABLE "RACINGAPP"."ROLE"
(
	key				bigint NOT NULL PRIMARY KEY,
	code			varchar(64) NOT NULL UNIQUE,
	name			varchar(255) NOT NULL,
	description		text NULL,
	actor_scope		varchar(32) NOT NULL DEFAULT 'both'
);

CREATE TABLE "RACINGAPP"."CLUB_USER_ROLE"
(
	key				bigint NOT NULL PRIMARY KEY,
	club_user		bigint NOT NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
	club			bigint NOT NULL REFERENCES "RACINGAPP"."CLUBCONTROL"(key),
	role			bigint NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
	granted_by		bigint NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
	granted_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	is_active		boolean NOT NULL DEFAULT TRUE,
	UNIQUE (club_user, club, role)
);

CREATE TABLE "RACINGAPP"."SAILOR_ROLE_GRANT"
(
	key				bigint NOT NULL PRIMARY KEY,
	sailor_user		bigint NOT NULL REFERENCES "RACINGAPP"."SAILORUSER"(key),
	sailor			bigint NOT NULL REFERENCES "RACINGAPP"."SAILORCONTROL"(key),
	club			bigint NULL REFERENCES "RACINGAPP"."CLUBCONTROL"(key),
	role			bigint NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
	valid_from		timestamp NULL,
	valid_to		timestamp NULL,
	granted_by		bigint NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
	grant_reason		text NULL,
	is_active		boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE "RACINGAPP"."RACE_RESULT_REVISION"
(
	key				bigint NOT NULL PRIMARY KEY,
	race_id			bigint NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
	revision_no		int NOT NULL,
	status			varchar(32) NOT NULL DEFAULT 'draft',
	source_mode		varchar(32) NOT NULL DEFAULT 'live',
	reason			text NULL,
	created_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	created_by_user		bigint NULL,
	created_by_type		varchar(32) NULL,
	based_on_revision_id	bigint NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key),
	snapshot_json		jsonb NULL,
	UNIQUE (race_id, revision_no)
);

CREATE TABLE "RACINGAPP"."RACE_DUTY_ASSIGNMENT"
(
	key				bigint NOT NULL PRIMARY KEY,
	race_id			bigint NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
	sailor			bigint NOT NULL REFERENCES "RACINGAPP"."SAILORCONTROL"(key),
	sailor_user		bigint NULL REFERENCES "RACINGAPP"."SAILORUSER"(key),
	role			bigint NOT NULL REFERENCES "RACINGAPP"."ROLE"(key),
	duty_type		varchar(64) NOT NULL DEFAULT 'race_officer',
	starts_at		timestamp NULL,
	ends_at			timestamp NULL,
	status			varchar(32) NOT NULL DEFAULT 'assigned',
	assigned_by		bigint NULL REFERENCES "RACINGAPP"."CLUBUSER"(key),
	notes			text NULL,
	created_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (race_id, sailor, role)
);

CREATE TABLE "RACINGAPP"."RACE_RESULT_AUDIT"
(
	key				bigint NOT NULL PRIMARY KEY,
	race_id			bigint NOT NULL REFERENCES "RACINGAPP"."RACE"(key) ON DELETE CASCADE,
	revision_id		bigint NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key) ON DELETE SET NULL,
	entity_type		varchar(64) NOT NULL,
	entity_id		bigint NULL,
	action			varchar(64) NOT NULL,
	actor_type		varchar(32) NOT NULL,
	actor_user_id		bigint NULL,
	actor_sailor_id		bigint NULL,
	reason			text NULL,
	before_json		jsonb NULL,
	after_json		jsonb NULL,
	created_at		timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE "RACINGAPP"."RACE"
	ADD COLUMN results_status varchar(32) NOT NULL DEFAULT 'draft';

ALTER TABLE "RACINGAPP"."RACE"
	ADD COLUMN results_locked_at timestamp NULL;

ALTER TABLE "RACINGAPP"."RACE"
	ADD COLUMN results_locked_by bigint NULL REFERENCES "RACINGAPP"."CLUBUSER"(key);

ALTER TABLE "RACINGAPP"."RACE"
	ADD COLUMN source_mode varchar(32) NOT NULL DEFAULT 'live';

ALTER TABLE "RACINGAPP"."RACE_ENTRY"
	ADD COLUMN created_by_user bigint NULL;

ALTER TABLE "RACINGAPP"."RACE_ENTRY"
	ADD COLUMN created_by_type varchar(32) NULL;

ALTER TABLE "RACINGAPP"."RACE_ENTRY"
	ADD COLUMN source varchar(32) NULL;

ALTER TABLE "RACINGAPP"."RACE_ENTRY"
	ADD COLUMN revision_id bigint NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key);

ALTER TABLE "RACINGAPP"."LAP"
	ADD COLUMN created_by_user bigint NULL;

ALTER TABLE "RACINGAPP"."LAP"
	ADD COLUMN created_by_type varchar(32) NULL;

ALTER TABLE "RACINGAPP"."LAP"
	ADD COLUMN source varchar(32) NULL;

ALTER TABLE "RACINGAPP"."LAP"
	ADD COLUMN revision_id bigint NULL REFERENCES "RACINGAPP"."RACE_RESULT_REVISION"(key);

ALTER TABLE "RACINGAPP"."ROLE"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."CLUB_USER_ROLE"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."SAILOR_ROLE_GRANT"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."RACE_RESULT_REVISION"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."RACE_DUTY_ASSIGNMENT"
	ALTER COLUMN key SET DEFAULT nextval('key');

ALTER TABLE "RACINGAPP"."RACE_RESULT_AUDIT"
	ALTER COLUMN key SET DEFAULT nextval('key');

INSERT INTO "RACINGAPP"."ROLE" (key, code, name, description, actor_scope)
VALUES
	(nextval('key'), 'club_admin', 'Club Admin', 'Full club administration and result approval rights', 'club_user'),
	(nextval('key'), 'race_officer', 'Race Officer', 'Operational race control access for assigned races', 'both'),
	(nextval('key'), 'sailor', 'Sailor', 'Standard sailor application access', 'sailor_user');

CREATE INDEX idx_club_user_role_club ON "RACINGAPP"."CLUB_USER_ROLE" (club);
CREATE INDEX idx_sailor_role_grant_sailor ON "RACINGAPP"."SAILOR_ROLE_GRANT" (sailor);
CREATE INDEX idx_sailor_role_grant_role ON "RACINGAPP"."SAILOR_ROLE_GRANT" (role);
CREATE INDEX idx_race_duty_assignment_race ON "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (race_id);
CREATE INDEX idx_race_duty_assignment_sailor ON "RACINGAPP"."RACE_DUTY_ASSIGNMENT" (sailor);
CREATE INDEX idx_race_result_audit_race ON "RACINGAPP"."RACE_RESULT_AUDIT" (race_id);
CREATE INDEX idx_race_result_revision_race ON "RACINGAPP"."RACE_RESULT_REVISION" (race_id);


ALTER TABLE "RACINGAPP"."CLUBCONTROL"
  ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;

ALTER TABLE "RACINGAPP"."CLUBUSER"
	ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;

ALTER TABLE "RACINGAPP"."SAILORUSER"
	ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;

-- Series Control

-- ALTER TABLE "RACINGAPP"."SERIESCONTROL"
-- 	ALTER COLUMN year SET DEFAULT EXTRACT(YEAR FROM CURRENT_DATE);

	
ALTER TABLE "RACINGAPP"."SERIESCONTROL"
  ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;

ALTER TABLE "RACINGAPP"."SAILORCONTROL"
  ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;

ALTER TABLE "RACINGAPP"."BOATCONTROL"
  ALTER COLUMN "key" ADD GENERATED BY DEFAULT AS IDENTITY;




-- ALTER TABLE "RACINGAPP"."SERIESCONTROL"
--   ADD CONSTRAINT seriescontrol_year_name_uq UNIQUE (y



