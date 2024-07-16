from flask import Flask, render_template, request, jsonify
import requests
import uuid

app = Flask(__name__, static_folder='static')

API_URL = "https://9dcf-105-27-226-165.ngrok-free.app/ask"
FEEDBACK_URL = "https://9dcf-105-27-226-165.ngrok-free.app/feedback" 

def call_api(question, format="default", conversation_id=None):
    payload = {
        "question": question, 
        "format": format,
        "conversation_id": conversation_id
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
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
        "conversation_id": response.get("conversation_id") or str(uuid.uuid4())
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

if __name__ == '__main__':
    app.run(debug=False)  # Set to False for production