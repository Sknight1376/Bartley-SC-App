-- Test Data Generation Script for Racing Application
-- This script creates comprehensive test data for development and testing

-- ===========================================
-- 1. CLUB DATA
-- ===========================================
INSERT INTO "RACINGAPP"."CLUBCONTROL" (key, name) VALUES
(nextval('key'), 'Bartley Sailing Club'),
(nextval('key'), 'Royal Southampton Yacht Club'),
(nextval('key'), 'Hamble River Sailing Club'),
(nextval('key'), 'Warsash Sailing Club'),
(nextval('key'), 'Hill Head Sailing Club');

-- ===========================================
-- 1b. CLUB USERS (default password: ChangeMe123!)
-- ===========================================
INSERT INTO "RACINGAPP"."CLUBUSER" (key, club, username, password_hash) VALUES
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), 'bartley_admin', crypt('ChangeMe123!', gen_salt('bf'))),
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club'), 'rsyc_admin', crypt('ChangeMe123!', gen_salt('bf'))),
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club'), 'hamble_admin', crypt('ChangeMe123!', gen_salt('bf'))),
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club'), 'warsash_admin', crypt('ChangeMe123!', gen_salt('bf'))),
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hill Head Sailing Club'), 'hillhead_admin', crypt('ChangeMe123!', gen_salt('bf')));

-- ===========================================
-- 2. SERIES DATA
-- ===========================================
INSERT INTO "RACINGAPP"."SERIESCONTROL" (key, year, name, club) VALUES
(nextval('key'), '2024', 'Summer Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), '2024', 'Winter Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), '2024', 'Championship Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
(nextval('key'), '2024', 'Training Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
(nextval('key'), '2024', 'Club Championship', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club'));

-- ===========================================
-- 3. SAILOR DATA
-- ===========================================
INSERT INTO "RACINGAPP"."SAILORCONTROL" (key, FullName, FirstName, LastName, club) VALUES
-- Bartley Sailing Club sailors
(nextval('key'), 'John Smith', 'John', 'Smith', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), 'Sarah Johnson', 'Sarah', 'Johnson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), 'Mike Wilson', 'Mike', 'Wilson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), 'Emma Davis', 'Emma', 'Davis', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), 'David Brown', 'David', 'Brown', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
(nextval('key'), 'Lisa Taylor', 'Lisa', 'Taylor', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),

-- Royal Southampton Yacht Club sailors
(nextval('key'), 'James Anderson', 'James', 'Anderson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
(nextval('key'), 'Rachel White', 'Rachel', 'White', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
(nextval('key'), 'Tom Harris', 'Tom', 'Harris', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
(nextval('key'), 'Sophie Martin', 'Sophie', 'Martin', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),

-- Hamble River Sailing Club sailors
(nextval('key'), 'Chris Evans', 'Chris', 'Evans', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
(nextval('key'), 'Anna Thompson', 'Anna', 'Thompson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
(nextval('key'), 'Paul Roberts', 'Paul', 'Roberts', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),

-- Warsash Sailing Club sailors
(nextval('key'), 'Mark Lewis', 'Mark', 'Lewis', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club')),
(nextval('key'), 'Helen Walker', 'Helen', 'Walker', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club')),
(nextval('key'), 'Steve Hall', 'Steve', 'Hall', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club'));

-- ===========================================
-- 4. BOAT DATA (linking sailors to boat classes)
-- ===========================================
-- Get some handicap keys for popular boat classes
INSERT INTO "RACINGAPP"."BOATCONTROL" (key, boat, sailor, sail_number) VALUES
-- Bartley Sailing Club boats
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'John Smith'), '1234'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '420'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Sarah Johnson'), '5678'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Mike Wilson'), '9012'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'ENTERPRISE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Emma Davis'), '3456'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FINN'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'David Brown'), '7890'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Lisa Taylor'), '1111'),

-- Royal Southampton Yacht Club boats
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'CONTENDER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'James Anderson'), '2222'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '29ER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Rachel White'), '3333'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '505'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Tom Harris'), '4444'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Sophie Martin'), '5555'),

-- Hamble River Sailing Club boats
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'ALBACORE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Chris Evans'), '6666'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'BLAZE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Anna Thompson'), '7777'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'EUROPE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Paul Roberts'), '8888'),

-- Warsash Sailing Club boats
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'DEVOTI_D-ONE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Mark Lewis'), '9999'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'COMET'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Helen Walker'), '1010'),
(nextval('key'), (SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'BRITISH_MOTH'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Steve Hall'), '1112');

-- ===========================================
-- 5. PERSISTED RACE / ENTRY / LAP TEST DATA
-- ===========================================
INSERT INTO "RACINGAPP"."RACE" (key, club, series, race_no, status, started_at, ended_at) VALUES
(nextval('key'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 3, 'finished', CURRENT_TIMESTAMP - INTERVAL '2 hour', CURRENT_TIMESTAMP - INTERVAL '75 minute');

INSERT INTO "RACINGAPP"."RACE_ENTRY" (key, race_id, boatkey, sailor, boat, sail_number, handicap) VALUES
(
 nextval('key'),
 (SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'John Smith'),
 'John Smith', 'LASER', '1234', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = 'LASER' LIMIT 1)),
(
 nextval('key'),
 (SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Sarah Johnson'),
 'Sarah Johnson', '420', '5678', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = '420' LIMIT 1)),
(
 nextval('key'),
 (SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Mike Wilson'),
 'Mike Wilson', 'FIREBALL', '9012', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = 'FIREBALL' LIMIT 1));

INSERT INTO "RACINGAPP"."LAP" (key, race_entry_id, lap_number, is_finish, elapsed_sec, corrected_sec, position) VALUES
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'John Smith' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 900, 818, 1),
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Sarah Johnson' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 945, 844, 2),
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Mike Wilson' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 960, 853, 3),
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'John Smith' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1830, 1691, 1),
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Sarah Johnson' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1895, 1692, 2),
(nextval('key'), (SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Mike Wilson' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1920, 1707, 3);

-- ===========================================
-- VERIFICATION QUERIES
-- ===========================================

-- Check club data
SELECT 'Clubs:' as info, COUNT(*) as count FROM "RACINGAPP"."CLUBCONTROL"
UNION ALL
-- Check series data
SELECT 'Series:', COUNT(*) FROM "RACINGAPP"."SERIESCONTROL"
UNION ALL
-- Check sailor data
SELECT 'Sailors:', COUNT(*) FROM "RACINGAPP"."SAILORCONTROL"
UNION ALL
-- Check boat data
SELECT 'Boats:', COUNT(*) FROM "RACINGAPP"."BOATCONTROL"
UNION ALL
-- Check handicap data
SELECT 'Handicaps:', COUNT(*) FROM "RACINGAPP"."HANDICAPCONTROL"
UNION ALL
SELECT 'Club Users:', COUNT(*) FROM "RACINGAPP"."CLUBUSER"
UNION ALL
SELECT 'Persisted Races:', COUNT(*) FROM "RACINGAPP"."RACE"
UNION ALL
SELECT 'Persisted Entries:', COUNT(*) FROM "RACINGAPP"."RACE_ENTRY"
UNION ALL
SELECT 'Persisted Laps:', COUNT(*) FROM "RACINGAPP"."LAP";

-- Sample query to see boat details with handicaps
SELECT
    sc.FullName as Sailor,
    hc.boat as Boat_Class,
    hc.handicap as Handicap,
    bc.sail_number as Sail_Number,
    cc.name as Club
FROM "RACINGAPP"."BOATCONTROL" bc
JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key
JOIN "RACINGAPP"."HANDICAPCONTROL" hc ON bc.boat = hc.key
JOIN "RACINGAPP"."CLUBCONTROL" cc ON sc.club = cc.key
ORDER BY cc.name, sc.FullName;

COMMIT;