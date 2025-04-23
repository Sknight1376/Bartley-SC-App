import psycopg2
import pandas as pd





class connect:

    def __init__(self):

        self.conn = psycopg2.connect(database="dwh",
                        host="localhost",
                        user="dwh",
                        password="DBTTEST",
                        port="5432")

        self.cursor = self.conn.cursor()
        

    def handicapcontrol(self):

        cursor = self.cursor 

        cursor.execute('SELECT * FROM "RACINGAPP"."HANDICAPCONTROL"')

        handicaps = pd.DataFrame(cursor.fetchall(), columns=['Date','Class_Name', 'Handicap'])
        self.conn.commit()

        self.conn.close()
        self.cursor.close()

        return handicaps
        
    def inserttime(self, timedict):


        boat            =   timedict['Boat']
        sail_number     =   "test"
        handicap        =   100
        club            =   "test"
        series          =   "test"
        race            =   1
        recorded_time   =   timedict['elapsed_time']
        corrected_time  =   timedict['corrected_time']
        position 	    =   1
        time            =   timedict['time']

        cursor = self.cursor 

        cursor.execute(f'''INSERT INTO "RACINGAPP"."RACEMASTER" (Boat,
            Sail_number, 
            handicap,
            club,
            series,
            race,
            recorded_time,
            corrected_time,
            position,
            time)
            values('{boat}',
                '{sail_number}',
                {handicap},
                '{club}',
                '{series}',
                {race},
                '{recorded_time}',
                '{corrected_time}',
                {position},
                '{time}' )''')
        
        self.conn.commit()

        self.conn.close()
        self.cursor.close()



