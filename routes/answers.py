import os
import json
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
from db import db  # Make sure db is correctly imported from your db.py file
from routes.auth_middleware import check_api_key, jwt_required
 
UPLOAD_FOLDER = 'uploads'
CACHE_FILE = "cached_users.json"
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm'}
 
answers_bp = Blueprint('answers', __name__)
 
limiter = Limiter(get_remote_address)
 
# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
 
def allowed_file(filename):
    try:
        if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            return True
        return False
    except Exception as e:
        print(f"Error in allowed_file: {e}")
        return False
 
def load_cached_users():
    """Load cached users from the JSON file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f).get("users", [])
        return []
    except Exception as e:
        print(f"Error in load_cached_users: {e}")
        return []
 
def save_cached_users(users):
    """Save updated user data back to the JSON file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"users": users}, f, indent=4)
    except Exception as e:
        print(f"Error in save_cached_users: {e}")
 
@answers_bp.route('/upload-video', methods=['POST'])
@limiter.limit("5 per minute")
@jwt_required
def upload_video():
    try:
        api_check = check_api_key()
        if api_check:  # If invalid, return error response
            return api_check
        # Get file and form data
        file = request.files.get('file')
        user_id = request.form.get('user_id')
        question_id = request.form.get('question_id')
        interview_id = request.form.get('interview_id')
 
        if not file or not user_id or not question_id:
            return jsonify({"error": "File, user_id, and question_id are required"}), 400
 
        if not user_id.isdigit() or not question_id.isdigit():
            return jsonify({"error": "user_id and question_id must be numeric"}), 400
 
        # Create a folder for the user if it doesn't exist
        user_folder = os.path.join(UPLOAD_FOLDER, f"user_{user_id}_{datetime.now().strftime('%Y-%m-%d')}")
        os.makedirs(user_folder, exist_ok=True)
 
        # Generate a filename for the video
        filename = f"user_{user_id}_question_{question_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.webm"
        file_path = os.path.join(user_folder, filename)
 
        # Save the file locally
        file.save(file_path)
 
        # Read the file content as a binary object
        file_content = file.read()
 
        # Now save the video as BLOB in the database, along with the filename
        query = """
            INSERT INTO osadm.INTERVIEWS_ANSWERS (QUESTION_ID, INTERVIEW_ID, VIDEO_NAME, VIDEO_DATA)
            VALUES (:question_id, :interview_id, :video_name, :video_data)
        """
        db.execute(query, {
            'question_id': int(question_id),
            'interview_id': int(interview_id),
            'video_name': filename,  # Store the video name
            'video_data': file_content  # Store the file as BLOB
        })
 
        # Update cache file (set question status to 1)
        users = load_cached_users()
        for user in users:
            if user["user_id"] == int(user_id):
                if str(question_id) in user["questions"]:
                    user["questions"][str(question_id)] = 1  # Mark as answered
                break
        save_cached_users(users)
 
        return jsonify({"message": "Video uploaded successfully"}), 200
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500