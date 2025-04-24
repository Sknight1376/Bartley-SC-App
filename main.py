from handicaps.parsing import import_races
from connections.connection import connect
import psycopg2
import pandas as pd


boat = 'RS400'


if __name__ == "__main__":

    
    def load_handicaps():

        cursor = connect()

        handicaps = cursor.handicapcontrol()

        return handicaps

    handicaps = pd.DataFrame.to_dict(load_handicaps(), orient='records')
        
    print(handicaps)

    handicap = [Class['Handicap'] for Class in handicaps if Class['Class_Name'].upper() == boat][0]
        
    print(handicap)

    


            
            

