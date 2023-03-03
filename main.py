from handicaps.parsing import import_races
from connections.connection import connect


if __name__ == "__main__":

    init_import = import_races('handicaps.csv')

    corrected_times = init_import.get_corrected_times('races', ['Time'], 'Boat')

    conn = connect('database.db')

    for frame in corrected_times:


        conn.insert_values(frame)

        

    
    conn.close_connection()




        

    


            
            

