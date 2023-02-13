
from flask import Flask, render_template, request, session, Response
import json


app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')

@app.route('/process_times/<string:time>', methods=['POST'])
def processtimes(time):
    times = json.loads(time)
    print()
    print(time)
    return('/')







if __name__ == "__main__":
    app.run(debug=True)