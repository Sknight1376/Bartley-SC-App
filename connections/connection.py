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
        

    def get_boats(self):

        cursor = self.cursor 

        cursor.execute('SELECT * FROM "RACINGAPP"."HANDICAPCONTROL"')

        handicaps = pd.DataFrame(cursor.fetchall(), columns=['Date','Class_Name', 'Handicap'])
        self.conn.commit()


        boats = handicaps['Class_Name'].sort_values()
        c = 1
        boatsarray = {}
        for i in boats:
            boatsarray[c] = i
            c+=1

        return boatsarray
    
    def close_connection(self):
        
        self.conn.close()
        self.cursor.close()



