
from flask import Flask, render_template, jsonify, request
import json
import pandas as pd
from handicaps.calculations import handicap_calculations
from handicaps.conversions import time_conversions

def get_boats():
    handicaps = pd.read_csv('handicaps.csv')

    boats = handicaps['Class_Name'].sort_values()
    c = 1
    boatsarray = {}
    for i in boats:
        boatsarray[c] = i
        c+=1

    return boatsarray

def load_files(file):

    File = pd.read_csv(file)

    loaded_data = pd.DataFrame.to_dict(File, orient='records')

    return loaded_data

handicaps = load_files('handicaps.csv')


app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html', boatarray = get_boats())

@app.route('/process_times/<string:time>', methods=['POST'])
def processtimes(time):
    times = json.loads(time)
    print()
    print(times)
    return('/')

@app.route('/times', methods=['POST'])
def times():
    boat = request.form.get('boat')
    time = request.form.get('Elapsed')
    handicap = [Class['Number'] for Class in handicaps if Class['Class_Name'].upper() == boat][0]
    print(time)
    print(boat, handicap_calculations.corrected_time(time, handicap))
    new_time = handicap_calculations.corrected_time(time, handicap)
    corrected_time= {'corrected_time' : new_time, "seconds": time_conversions.tosecs(new_time)}
    return jsonify(corrected_time)
 






if __name__ == "__main__":
    app.run(debug=True)