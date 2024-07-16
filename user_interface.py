from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import uuid
import os

app = Flask(__name__, static_folder='static')

API_URL = "http://127.0.0.1:8050/ask"
FEEDBACK_URL = "http://127.0.0.1:8050/feedback"

def call_api(question, format="default", conversation_id=None):
    payload = {
        "question": question, 
        "format": format,
        "conversation_id": conversation_id
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
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
    question = data.get('question')
    format = data.get('format', 'default')
    conversation_id = data.get('conversation_id')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    response = call_api(question, format, conversation_id)
    
    if "error" in response:
        return jsonify(response), 500
    
    return jsonify({
        "answer": response.get("answer"),
        "interaction_id": response.get("interaction_id"),
        "conversation_id": response.get("conversation_id") or str(uuid.uuid4()),
        "sources": response.get("sources", [])
    })

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    interaction_id = data.get('interaction_id')
    feedback_rating = data.get('feedback')
    
    if not interaction_id or feedback_rating is None:
        return jsonify({"error": "Invalid feedback data"}), 400
    
    try:
        response = requests.post(FEEDBACK_URL, json=data, timeout=10)
        response.raise_for_status()
        return jsonify({"message": "Feedback submitted successfully"})
    except requests.RequestException as e:
        return jsonify({"error": f"Error submitting feedback: {str(e)}"}), 500

@app.route('/get_chat_messages/<conversation_id>')
def get_chat_messages(conversation_id):
    # This is a placeholder. In a real application, you would fetch the messages from your database.
    # For now, we'll return an empty list.
    return jsonify({"messages": []})

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)