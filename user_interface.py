from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder='static')

API_URL = "http://127.0.0.1:8050"

def call_api(endpoint, method='GET', data=None):
    url = f"{API_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Error calling API: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    response = call_api('/ask', method='POST', data=data)
    return jsonify(response)

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    response = call_api('/feedback', method='POST', data=data)
    return jsonify(response)

@app.route('/chat_history')
def chat_history():
    response = call_api('/chat_history')
    return jsonify(response)

@app.route('/conversation/<conversation_id>')
def get_conversation(conversation_id):
    response = call_api(f'/conversation/{conversation_id}')
    return jsonify(response)

@app.route('/conversation/new', methods=['POST'])
def new_conversation():
    response = call_api('/conversation/new', method='POST')
    return jsonify(response)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)