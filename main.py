from handicaps.parsing import import_races
import pandas as pd


if __name__ == "__main__":

    init_import = import_races('handicaps.csv')

    result = init_import.get_corrected_times('races', ['Boat', 'Time'], 'Boat')

    result_frame = pd.DataFrame(result)

    sorted_results = result_frame.sort_values('corrected_time', ignore_index=True)

    sorted_results.index+=1

    print(sorted_results)
            
            

