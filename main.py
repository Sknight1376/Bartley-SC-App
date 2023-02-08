from handicaps.parsing import import_races
from handicaps.calculations import compare_to_median

if __name__ == "__main__":

    init_import = import_races('handicaps.csv')

    corrected_times = init_import.get_corrected_times('races', ['Time'], 'Boat')


    print(corrected_times)


        

    


            
            

