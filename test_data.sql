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
-- 5. SAMPLE RACE RESULTS (Optional - for testing race control)
-- ===========================================
-- Insert some sample race results for the Bartley Summer Series
INSERT INTO "RACINGAPP"."RACEMASTER" (boatkey, club, series, race, recorded_time, corrected_time, time) VALUES
-- Race 1 results
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'John Smith'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 1, '00:45:30', '00:42:15', '00:45:30'),
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Sarah Johnson'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 1, '00:47:15', '00:43:45', '00:47:15'),
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Mike Wilson'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 1, '00:44:20', '00:41:30', '00:44:20'),

-- Race 2 results
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'John Smith'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 2, '00:46:45', '00:43:25', '00:46:45'),
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'Emma Davis'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 2, '00:49:10', '00:45:30', '00:49:10'),
((SELECT bc.key FROM "RACINGAPP"."BOATCONTROL" bc JOIN "RACINGAPP"."SAILORCONTROL" sc ON bc.sailor = sc.key WHERE sc.FullName = 'David Brown'), (SELECT key FROM "RACINGAPP"."CLUBCONTROL" WHERE name = 'Bartley Sailing Club'), (SELECT key FROM "RACINGAPP"."SERIESCONTROL" WHERE name = 'Summer Series'), 2, '00:48:05', '00:44:40', '00:48:05');

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
-- Check race results
SELECT 'Race Results:', COUNT(*) FROM "RACINGAPP"."RACEMASTER";

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