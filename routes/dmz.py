from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS


load_dotenv(dotenv_path='/home/asem/projects/hr-interview-analyzer-main/backend/.env')

API_SERVER_URL = os.getenv("MIDDLEWARE_SERVER_URL")
API_KEY = os.getenv("MIDDLEWARE_API_KEY")



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://10.64.5.117", "http://10.64.6.117"]}}, supports_credentials=True)



@app.route('/auth/auth', methods=['POST'])
def auth():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/auth/auth"
    response = requests.post(url, json={"email": email, "password": password},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500

@app.route('/auth/validatePinCode', methods=['POST'])
def validatePinCode():
    data = request.json
    email = data.get("email")
    pinCode = data.get("pinCode")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/auth/validatePinCode"
    response = requests.post(url, json={"email": email, "pinCode": pinCode},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500





# API to save feedback
@app.route('/save-feedback', methods=['POST'])
def save_feedback():
    data = request.json
    user_id = data.get("user_id")
    rating = data.get("rating")
    notes = data.get("notes")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/users/save-feedback"
    response = requests.post(url, json={"user_id": user_id, "rating": rating, "notes": notes},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500
@app.route('/face_detection', methods=['POST'])
def face_detection():
    image_file = request.files['image']

    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/face/face_detection"
    response = requests.post(url, json={"image_file": image_file},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500

# API to start a chatbot session
@app.route('/start-session', methods=['GET'])
def start_session():
    url = f"{API_SERVER_URL}/chatbot/start-session"
    try:
        auth_token = request.headers.get("Authorization")
    
        headers = {
            "API-KEY": API_KEY,
            "Content-Type": "application/json",
            "Authorization":auth_token
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json()}), 500
    except Exception as e:
        return jsonify({"error": f"Error in start_session: {e}"}), 500

# API to send a chat message
@app.route('/send-chat-message', methods=['POST'])
def send_chat_message():
    data = request.json
    session_id = data.get("session_id")
    user_input = data.get("user_input")
    user_id = data.get("user_id")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/chatbot/chat"
    response = requests.post(url, json={"session_id": session_id, "user_input": user_input, "user_id": user_id},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500

# API to end a chatbot session
@app.route('/end-session', methods=['POST'])
def end_session():
    data = request.json
    session_id = data.get("session_id")
    user_id = data.get("user_id")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/chatbot/end-session"
    response = requests.post(url, json={"session_id": session_id, "user_id": user_id},headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": response.json()}), 500

# API to compare faces
@app.route('/compare-faces', methods=['POST'])
def compare_faces():
    id_image = request.files.get("id_image")
    selfie_image = request.files.get("selfie_image")
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    url = f"{API_SERVER_URL}/id/compare_faces"
    files = {
        "id_image": id_image,
        "selfie_image": selfie_image
    }

    try:
        response = requests.post(url, files=files,headers=headers)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json()}), 500
    except Exception as e:
        return jsonify({"error": f"Error in compare_faces: {e}"}), 500

# API to upload video
@app.route('/upload-video', methods=['POST'])
def upload_video():
    user_id = request.form.get("user_id")
    question_id = request.form.get("question_id")
    interview_id = request.form.get("interview_id")
    video_file = request.files.get("file")

    url = f"{API_SERVER_URL}/answers/upload-video"
    files = {
        "file": video_file
    }
    data = {
        "user_id": user_id,
        "question_id": question_id,
        "interview_id": interview_id
    }
    auth_token = request.headers.get("Authorization")
    
    headers = {
        "API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Authorization":auth_token
    }
    try:
        response = requests.post(url, files=files, data=data,headers=headers)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json()}), 500
    except Exception as e:
        return jsonify({"error": f"Error in upload_video: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=False, host="10.64.5.117", port=5002) #dmz host and port
