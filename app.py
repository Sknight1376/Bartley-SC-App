
from flask import Flask, render_template, jsonify, request
import json
import pandas as pd

from handicaps.calculations import handicap_calculations
from handicaps.conversions import time_conversions
from connections.connection import connect


def get_boats():

    cursor = connect()

    handicaps = cursor.handicapcontrol()

    boats = handicaps['Class_Name'].sort_values()
    c = 1
    boatsarray = {}
    for i in boats:
        boatsarray[c] = i
        c+=1

    return boatsarray

def load_handicaps():

    cursor = connect()

    handicaps = cursor.handicapcontrol()

    return handicaps

handicaps = pd.DataFrame.to_dict(load_handicaps(), orient='records')


app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html', boatarray = get_boats())

# @app.route('/process_times/<string:time>', methods=['POST'])
# def processtimes(time):
#     times = json.loads(time)
#     for entry in times:
#         print(entry['Boat'])
#     return "Done"

@app.route('/times', methods=['POST'])
def times():
    boat = request.form.get('boat')
    elapsed_time = request.form.get('elapsed')
    split = request.form.get('split')
    handicap = [Class['Handicap'] for Class in handicaps if Class['Class_Name'].upper() == boat][0]
    
    print(split, boat, handicap_calculations.corrected_time(elapsed_time, handicap))
    new_time = handicap_calculations.corrected_time(elapsed_time, handicap)
    corrected_time= {'corrected_time' : new_time, "seconds": time_conversions.tosecs(new_time)}

    cursor = connect()
    cursor.inserttime({
        "Boat"            :   boat,
        "sail_number"     :   "test",
        "handicap"        :   100,
        "club"            :   "test",
        "series"          :   "test",
        "race"            :   1,
        "elapsed_time"    :   elapsed_time,
        "corrected_time"  :   new_time,
        "position" 	      :   1,
        "time"            :   split
    })
    

    return jsonify(corrected_time)
 






if __name__ == "__main__":
    app.run(debug=True)