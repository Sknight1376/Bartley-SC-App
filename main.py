from handicaps.parsing import import_races
from connections.connection import connect
import psycopg2
import pandas as pd





if __name__ == "__main__":

    
    def get_boats():

        cursor = connect()

        boatsarray= cursor.get_boats()

        print(boatsarray)
    
    


        

    


            
            

