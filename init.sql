CREATE SCHEMA "RACINGAPP";
CREATE SCHEMA "AUDIT";


CREATE TABLE "RACINGAPP"."RACES"
(
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
	year			varchar(255) NOT NULL,
	seriesname		varchar(255) NOT NULL,
	club			varchar(255) NULL
);


CREATE TABLE "RACINGAPP"."SAILORCONTROL"
(
	boat			varchar(255) NOT NULL,
	sail_number		varchar(255) NOT NULL,
	FirstName 		varchar(255) NOT NULL,
	LastName		varchar(255) NULL,
	club			varchar(255) NULL
);

CREATE TABLE "RACINGAPP"."HANDICAPCONTROL"
(
	date			DATE NOT NULL,
	boat			varchar(255) NOT NULL,
	handicap		int NOT NULL
);


CREATE TABLE "RACINGAPP"."RACEMASTER"
(
	boat			varchar(255) NOT NULL,
	sail_number		varchar(255) NOT NULL,
	handicap 		int NULL,
	club			varchar(255) NULL,
	series			varchar(255) NULL,
	race 			int NULL,
	recorded_time 	time NULL,
	corrected_time 	time NULL,
	position 		int NULL,
	time			time
);




CREATE TABLE "AUDIT".cdc
(
	TableName varchar(255) NULL,
	DateColumn varchar(255) NULL,
	LastLoadTimestamp date NULL
)