import sys
import json
from generate import *
from algorithms import *

from flask import Flask, request
app = Flask(__name__, static_url_path='/static')

@app.route("/solve", methods=['POST'])
def solve():
	data = 'ERROR'
	if (request.json == 'single'):
		data = optimal_solution()
	elif (request.json == 'double'):
		data = alt_multi()

	for m_data in data['matches']:
		if m_data is None: continue
		order = []
		for dest in m_data[2]['order']:
			order.append({
				"pos" : {
					"lat": dest.location[0],
					"lng": dest.location[1]
				},
				"type": 'Company' if type(dest) is Company else 'Restaurant'
			})
		m_data[2]['order'] = order

	return json.dumps(data)

@app.route("/generate", methods=['POST'])
def generate():
	o_num = request.json['orders']
	d_num = request.json['drivers']
	generate_new_test_data(int(o_num), int(d_num), int(o_num))
	return json.dumps(generate_all(), default=lambda o: o.__dict__)

@app.route("/load", methods=['POST'])
def load():
	return json.dumps(generate_all(), default=lambda o: o.__dict__)

@app.route("/get_data", methods=['GET'])
def get_data():
	return json.dumps(generate_all(), default=lambda o: o.__dict__)

@app.route('/')
def root():
    return app.send_static_file('index.html')

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)
