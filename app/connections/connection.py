import os
import psycopg2
import pandas as pd


class connect:

    def __init__(self):
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            self.conn = psycopg2.connect(db_url)
        else:
            self.conn = psycopg2.connect(
                database=os.environ.get('POSTGRES_DB', 'dwh'),
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                user=os.environ.get('POSTGRES_USER', 'dwh'),
                password=os.environ.get('POSTGRES_PASSWORD', 'DBTTEST'),
                port=os.environ.get('POSTGRES_PORT', '5432'),
            )

        self.cursor = self.conn.cursor()

    def inserttime(self, timedict):
        boat           = timedict['Boat']
        sail_number    = "test"
        handicap       = 100
        club           = "test"
        series         = "test"
        race           = 1
        recorded_time  = timedict['elapsed_time']
        corrected_time = timedict['corrected_time']
        position       = 1
        timestamp      = timedict['time']

        cursor = self.cursor

        # Parameterised query — never interpolate user data directly into SQL.
        cursor.execute(
            '''
            INSERT INTO "RACINGAPP"."RACEMASTER" (
                Key, Boatkey, Sail_number, handicap, club, series, race,
                recorded_time, corrected_time, position, time
            ) VALUES (
                nextval('key'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ''',
            (boat, sail_number, handicap, club, series, race,
             recorded_time, corrected_time, position, timestamp),
        )

        self.conn.commit()
        self.conn.close()
        self.cursor.close()



