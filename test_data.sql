-- Test Data Generation Script for Racing Application
-- This script creates comprehensive test data for development and testing

-- ===========================================
-- 1. CLUB DATA
-- ===========================================
INSERT INTO "RACINGAPP"."CLUBCONTROL" (name) VALUES
('Bartley Sailing Club'),
('Royal Southampton Yacht Club'),
('Hamble River Sailing Club'),
('Warsash Sailing Club'),
('Hill Head Sailing Club');

-- ===========================================
-- 2. SERIES DATA
-- ===========================================
INSERT INTO "RACINGAPP"."SERIESCONTROL" (year, name, club) VALUES
('2024', 'Summer Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('2024', 'Winter Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('2024', 'Championship Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
('2024', 'Training Series', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
('2024', 'Club Championship', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club'));

-- ===========================================
-- 3. SAILOR DATA
-- ===========================================
INSERT INTO "RACINGAPP"."SAILORCONTROL" (FullName, FirstName, LastName, club) VALUES
-- Bartley Sailing Club sailors
('John Smith', 'John', 'Smith', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('Sarah Johnson', 'Sarah', 'Johnson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('Mike Wilson', 'Mike', 'Wilson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('Emma Davis', 'Emma', 'Davis', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('David Brown', 'David', 'Brown', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),
('Lisa Taylor', 'Lisa', 'Taylor', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club')),

-- Royal Southampton Yacht Club sailors
('James Anderson', 'James', 'Anderson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
('Rachel White', 'Rachel', 'White', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
('Tom Harris', 'Tom', 'Harris', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),
('Sophie Martin', 'Sophie', 'Martin', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Royal Southampton Yacht Club')),

-- Hamble River Sailing Club sailors
('Chris Evans', 'Chris', 'Evans', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
('Anna Thompson', 'Anna', 'Thompson', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),
('Paul Roberts', 'Paul', 'Roberts', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Hamble River Sailing Club')),

-- Warsash Sailing Club sailors
('Mark Lewis', 'Mark', 'Lewis', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club')),
('Helen Walker', 'Helen', 'Walker', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club')),
('Steve Hall', 'Steve', 'Hall', (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Warsash Sailing Club'));

-- ===========================================
-- 4. BOAT DATA (linking sailors to boat classes)
-- ===========================================
-- Get some handicap keys for popular boat classes
INSERT INTO "RACINGAPP"."BOATCONTROL" (boat, sailor, sail_number) VALUES
-- Bartley Sailing Club boats
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'John Smith'), '1234'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '420'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Sarah Johnson'), '5678'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Mike Wilson'), '9012'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'ENTERPRISE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Emma Davis'), '3456'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FINN'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'David Brown'), '7890'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'LASER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Lisa Taylor'), '1111'),

-- Royal Southampton Yacht Club boats
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'CONTENDER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'James Anderson'), '2222'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '29ER'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Rachel White'), '3333'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = '505'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Tom Harris'), '4444'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'FIREBALL'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Sophie Martin'), '5555'),

-- Hamble River Sailing Club boats
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'ALBACORE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Chris Evans'), '6666'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'BLAZE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Anna Thompson'), '7777'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'EUROPE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Paul Roberts'), '8888'),

-- Warsash Sailing Club boats
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'DEVOTI_D-ONE'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Mark Lewis'), '9999'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'COMET'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Helen Walker'), '1010'),
((SELECT key FROM "RACINGAPP"."HANDICAPCONTROL" WHERE boat = 'BRITISH_MOTH'), (SELECT key FROM "RACINGAPP"."SAILORCONTROL" WHERE FullName = 'Steve Hall'), '1112');

-- ===========================================
-- 5. PERSISTED RACE / ENTRY / LAP TEST DATA
-- ===========================================
INSERT INTO "RACINGAPP"."RACE" (club, series, race_no, status, started_at, ended_at) VALUES
((SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 3, 'finished', CURRENT_TIMESTAMP - INTERVAL '2 hour', CURRENT_TIMESTAMP - INTERVAL '75 minute');

INSERT INTO "RACINGAPP"."RACE_ENTRY" (race_id, boatkey, sailor, boat, sail_number, handicap) VALUES
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'John Smith'),
 'John Smith', 'LASER', '1234', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = 'LASER' LIMIT 1)),
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Sarah Johnson'),
 'Sarah Johnson', '420', '5678', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = '420' LIMIT 1)),
((SELECT key FROM "RACINGAPP"."RACE" WHERE race_no = 3 AND series = (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series') ORDER BY key DESC LIMIT 1),
 (SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Mike Wilson'),
 'Mike Wilson', 'FIREBALL', '9012', (SELECT hc.handicap FROM "RACINGAPP"."HANDICAPCONTROL" hc WHERE hc.boat = 'FIREBALL' LIMIT 1));

INSERT INTO "RACINGAPP"."LAP" (race_entry_id, lap_number, is_finish, elapsed_sec, corrected_sec, position) VALUES
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'John Smith' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 900, 818, 1),
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Sarah Johnson' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 945, 844, 2),
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Mike Wilson' ORDER BY re.key DESC LIMIT 1), 1, FALSE, 960, 853, 3),
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'John Smith' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1830, 1691, 1),
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Sarah Johnson' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1895, 1692, 2),
((SELECT re.key FROM "RACINGAPP"."RACE_ENTRY" re WHERE re.sailor = 'Mike Wilson' ORDER BY re.key DESC LIMIT 1), 2, TRUE, 1920, 1707, 3);

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