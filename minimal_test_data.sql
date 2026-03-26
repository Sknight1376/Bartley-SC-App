-- Minimal Test Data for Quick Testing
-- Run this after the main init.sql to get basic test data

-- ===========================================
-- BASIC CLUB AND SERIES
-- ===========================================
INSERT INTO "RACINGAPP"."CLUBCONTROL" (name) VALUES ('Test Club');

INSERT INTO "RACINGAPP"."SERIESCONTROL" (year, name, club)
VALUES ('2024', 'Test Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Test Club'));

-- ===========================================
-- BASIC SAILORS
-- ===========================================
INSERT INTO "RACINGAPP"."SAILORCONTROL" (FullName, FirstName, LastName, club) VALUES
('Alice Test', 'Alice', 'Test', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Test Club')),
('Bob Test', 'Bob', 'Test', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Test Club')),
('Charlie Test', 'Charlie', 'Test', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Test Club'));

-- ===========================================
-- BASIC BOATS (using existing handicap data)
-- ===========================================
INSERT INTO "RACINGAPP"."BOATCONTROL" (boat, sailor, sail_number) VALUES
-- Alice's Laser
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER' LIMIT 1), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Alice Test'), '100'),
-- Bob's 420
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '420' LIMIT 1), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Bob Test'), '200'),
-- Charlie's Fireball
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL' LIMIT 1), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Charlie Test'), '300');

INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at) VALUES
((SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Test Club'),
 (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Test Series'),
 1,
 'active',
 CURRENT_TIMESTAMP);

INSERT INTO "RACINGAPP"."RACE_ENTRY" (race_id, boatkey, sailor, boat, sail_number, handicap) VALUES
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 1 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Test Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Alice Test'),
 'Alice Test', 'LASER', '100', (SELECT handicap FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER' LIMIT 1)),
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 1 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Test Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Bob Test'),
 'Bob Test', '420', '200', (SELECT handicap FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '420' LIMIT 1)),
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 1 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Test Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Charlie Test'),
 'Charlie Test', 'FIREBALL', '300', (SELECT handicap FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL' LIMIT 1));

COMMIT;

-- Quick verification
SELECT 'Test data loaded successfully!' as status;