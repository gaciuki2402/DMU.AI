from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import os
import logging
import subprocess
import signal
import atexit

app = Flask(__name__, static_folder="static")
application = app

API_URL = "http://127.0.0.1:8050"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to call API
def call_api(endpoint, method="GET", data=None):
    url = f"{API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=30)
        else:
            return {"error": "Unsupported HTTP method"}

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API call error: {str(e)}")
        return {"error": f"Error calling API: {str(e)}"}


# Flask routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    response = call_api("/ask", method="POST", data=data)
    return jsonify(response)


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    response = call_api(
        "/feedback",
        method="POST",
        data={
            "interaction_id": data["interaction_id"],
            "is_helpful": data["is_helpful"],
        },
    )
    return jsonify(response)


@app.route("/chat_history")
def chat_history():
    response = call_api("/chat_history")
    return jsonify(response)


@app.route("/conversation/<conversation_id>")
def get_conversation(conversation_id):
    response = call_api(f"/conversation/{conversation_id}")
    return jsonify(response)


@app.route("/conversation/new", methods=["POST"])
def new_conversation():
    response = call_api("/conversation/new", method="POST")
    return jsonify(response)


@app.route("/conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    response = call_api(f"/conversation/{conversation_id}", method="DELETE")
    if "error" in response:
        logger.error(f"Error deleting conversation: {response['error']}")
        return jsonify({"error": response["error"]}), 400
    return jsonify({"message": "Conversation deleted successfully"}), 200


@app.route("/api_status")
def api_status():
    response = call_api("/")
    return jsonify(response)


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


fastapi_process = subprocess.Popen(
    ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8050"]
)


def cleanup():
    fastapi_process.send_signal(signal.SIGINT)
    fastapi_process.wait()


atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


# from flask import Flask, render_template, request, jsonify, send_from_directory
# import requests
# import os
# import logging

# app = Flask(__name__, static_folder='static')

# API_URL = "http://127.0.0.1:8050"

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def call_api(endpoint, method='GET', data=None):
#     url = f"{API_URL}{endpoint}"
#     try:
#         if method == 'GET':
#             response = requests.get(url, timeout=30)
#         elif method == 'POST':
#             response = requests.post(url, json=data, timeout=30)
#         elif method == 'DELETE':
#             response = requests.delete(url, timeout=30)
#         elif method == 'PUT':
#             response = requests.put(url, json=data, timeout=30)
#         else:
#             return {"error": "Unsupported HTTP method"}
        
#         response.raise_for_status()
#         return response.json()
#     except requests.RequestException as e:
#         logger.error(f"API call error: {str(e)}")
#         return {"error": f"Error calling API: {str(e)}"}

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/ask', methods=['POST'])
# def ask():
#     data = request.json
#     response = call_api('/ask', method='POST', data=data)
#     return jsonify(response)

# @app.route('/feedback', methods=['POST'])
# def feedback():
#     data = request.json
#     response = call_api('/feedback', method='POST', data={
#         'interaction_id': data['interaction_id'],
#         'is_helpful': data['is_helpful']
#     })
#     return jsonify(response)

# @app.route('/chat_history')
# def chat_history():
#     response = call_api('/chat_history')
#     return jsonify(response)

# @app.route('/conversation/<conversation_id>')
# def get_conversation(conversation_id):
#     response = call_api(f'/conversation/{conversation_id}')
#     return jsonify(response)

# @app.route('/conversation/new', methods=['POST'])
# def new_conversation():
#     response = call_api('/conversation/new', method='POST')
#     return jsonify(response)

# @app.route('/conversation/<conversation_id>', methods=['DELETE'])
# def delete_conversation(conversation_id):
#     response = call_api(f'/conversation/{conversation_id}', method='DELETE')
#     if 'error' in response:
#         logger.error(f"Error deleting conversation: {response['error']}")
#         return jsonify({'error': response['error']}), 400
#     return jsonify({'message': 'Conversation deleted successfully'}), 200

# @app.route('/api_status')
# def api_status():
#     response = call_api('/')
#     return jsonify(response)

# @app.route('/static/<path:path>')
# def send_static(path):
#     return send_from_directory('static', path)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)