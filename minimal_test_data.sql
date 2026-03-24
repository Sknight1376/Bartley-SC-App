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

COMMIT;

-- Quick verification
SELECT 'Test data loaded successfully!' as status;