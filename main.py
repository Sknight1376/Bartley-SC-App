from handicaps.parsing import import_races, formatting
import pandas as pd
from handicaps.calculations import compare_to_median

if __name__ == "__main__":

    init_import = import_races('handicaps.csv')

    corrected_times = init_import.get_corrected_times('races', ['Time'], 'Boat')

    find_median = compare_to_median(corrected_times)

    with_adjusted = find_median.comparison(corrected_times)

    final = formatting.format_results(with_adjusted)

    print(final)

    


            
            

