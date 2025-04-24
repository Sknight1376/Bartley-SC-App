CREATE SCHEMA "RACINGAPP";
CREATE SCHEMA "AUDIT";
CREATE SEQUENCE key START 1;


CREATE TABLE "RACINGAPP"."RACES"
(
	key				bigint NOT NULL,
	boat			varchar(255) NOT NULL,
	sail_number		varchar(255) NOT NULL,
	handicap 		int NULL,
	club			varchar(255) NULL,
	series			varchar(255) NULL,
	race 			int NULL,
	recorded_time 	timestamp NULL,
	corrected_time 	timestamp NULL,
	final_position 	int NULL
);

CREATE TABLE "RACINGAPP"."SERIESCONTROL"
(
	key				bigint NOT NULL,
	year			varchar(255) NOT NULL,
	seriesname		varchar(255) NOT NULL,
	club			varchar(255) NULL
);

CREATE TABLE "RACINGAPP"."CLUBCONTROL"
(
	key				bigint NOT NULL,
	club_name		varchar(255) NOT NULL
);

CREATE TABLE "RACINGAPP"."SAILORCONTROL"
(
	key				bigint NOT NULL,
	boat			varchar(255) NOT NULL,
	sail_number		varchar(255) NOT NULL,
	FirstName 		varchar(255) NOT NULL,
	LastName		varchar(255) NULL,
);

CREATE TABLE "RACINGAPP"."HANDICAPCONTROL"
(
	key				bigint NOT NULL,
	date			DATE NOT NULL,
	boat			varchar(255) NOT NULL,
	handicap		int NOT NULL
);


CREATE TABLE "RACINGAPP"."RACEMASTER"
(
	key				bigint NOT NULL,
	boatkey			bigint,
	club			bigint
	series			bigint,
	race 			int NULL,
	recorded_time 	time NULL,
	corrected_time 	time NULL,
	time			time
);

CREATE TABLE "AUDIT".cdc
(
	TableName varchar(255) NULL,
	DateColumn varchar(255) NULL,
	LastLoadTimestamp date NULL
)