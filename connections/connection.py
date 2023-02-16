import sqlite3
import os
import pandas as pd

class connect:

    def __init__(self, conn):

        self.conn = sqlite3.connect(conn)

        self.c = self.conn.cursor()
        
        if os.path.exists(conn)==False:

            with open('connections/schema.sql', 'r') as script:

                schema = script.read()

            self.c.executescript(schema)    


    def insert_values(self, frame):

        frame.to_sql('race_data', self.conn, if_exists="append")

    
