import pandas as pd
from os import listdir
from os.path import isfile, join

from handicaps.calculations import handicap_calculations

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

        new_result = []

        for file in listdir(dir):

            loaded = load_files(join(dir,file))

            for row in loaded:

                print(row)

                handicap = [Class['Number'] for Class in handicaps if Class['Class Name'].upper() == row[boat].upper()][0]

                corrected_time = handicap_calculations.corrected_time(*[row[name] for name in dict_names], int(handicap))

                row['corrected_time'] = corrected_time

                row['handicap'] = handicap

                new_result.append(row)

        return new_result





class formatting:

    def format_results(result_dict):
        
        ## parse to pandas dataframe
        result_frame = pd.DataFrame(result_dict)

        ## Sort results by corrected time
        sorted_results = result_frame.sort_values('corrected_time', ignore_index=True)

        ## Amend index, starts at 1 rather than 0
        sorted_results.index+=1

        return sorted_results
            