import pandas as pd
from os import listdir
from os.path import isfile, join

from handicaps.calculations import handicap_calculations, compare_to_median

def load_files(file):

    File = pd.read_csv(file)

    loaded_data = pd.DataFrame.to_dict(File, orient='records')

    return loaded_data




class import_races:

    def __init__(self, handicaps):

        self.handicaps = load_files(handicaps)

    ## Return corrected time in dict format
    def get_corrected_times(self, dir, dict_names, boat):

        handicaps = self.handicaps

        all_results = []

        for file in listdir(dir):

            loaded = load_files(join(dir,file))

            new_result = []

            for row in loaded:

                handicap = [Class['Number'] for Class in handicaps if Class['Class Name'].upper() == row[boat].upper()][0]

                corrected_time = handicap_calculations.corrected_time(*[row[name] for name in dict_names], int(handicap))

                row['corrected_time'] = corrected_time

                row['handicap'] = handicap

                row['race'] = file

                new_result.append(row)

            init_adjusted = compare_to_median(new_result)

            adjusted = init_adjusted.comparison(new_result)

            all_results.append(formatting.format_results(adjusted))


        return all_results





class formatting:

    def format_results(result_dict):
        
        ## parse to pandas dataframe
        result_frame = pd.DataFrame(result_dict)

        ## Sort results by corrected time
        result_frame['rank'] = result_frame['corrected_time'].rank(method='first')

        return result_frame
            