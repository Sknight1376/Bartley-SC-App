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


    def get_corrected_times(self, dir, dict_names, boat):

        handicaps = self.handicaps

        new_result = []

        for file in listdir(dir):

            loaded = load_files(join(dir,file))

            for row in loaded:

                handicap = [Class['Number'] for Class in handicaps if Class['Class Name'].upper() == row[boat].upper()][0]

                corrected_time = handicap_calculations.corrected_time(*[row[name] for name in dict_names], int(handicap))

                row['corrected_time'] = corrected_time

                new_result.append(row)

        return new_result

            



    

    

    # c=0
    # for k, v in loaded_race.items():
    #     loop = len(v)

    # while c < loop:
    #     corrected = handicap_calculations.corrected_time(loaded_race['Boat'][c],loaded_race['Time'][c],1000)
    #     print(loaded_race['Boat'][c], corrected)
    #     c+=1