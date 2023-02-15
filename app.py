
from flask import Flask, render_template
import json
import pandas as pd

def get_boats():
    handicaps = pd.read_csv('handicaps.csv')

    boats = handicaps['Class Name'].sort_values()
    c = 1
    boatsarray = {}
    for i in boats:
        boatsarray[c] = i
        c+=1

    return boatsarray


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






if __name__ == "__main__":
    app.run(debug=True)