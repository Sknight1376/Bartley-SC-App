from handicaps.calculations import handicap_calculations


import pandas as pd


if __name__ == "__main__":

    Races = pd.read_csv('Races.csv')

    loaded_race = pd.DataFrame.to_dict(Races)
