import os
import json
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
from db import db
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

        # Read the file content as a binary object
        file_content = file.read()

        # Establish database connection
        db.connect()
        conn = db.connection

        if conn is None:
            raise ValueError("Failed to obtain a valid database connection.")

        with conn.cursor() as cursor:
            # Check if the answer already exists (fetch all matching records)
            cursor.execute(
                """
                SELECT COUNT(*) FROM osadm.INTERVIEWS_ANSWERS 
                WHERE QUESTION_ID = :question_id AND INTERVIEW_ID = :interview_id
                """,
                {"question_id": int(question_id), "interview_id": int(interview_id)}
            )
            result = cursor.fetchall()
            existing_record = result[0][0] if result else 0

            if existing_record:
                # Update existing answer
                cursor.execute(
                    """
                    UPDATE osadm.INTERVIEWS_ANSWERS
                    SET ANSWER_PATH = :ANSWER_PATH, SCORE_COLB = :score_colb
                    WHERE QUESTION_ID = :question_id AND INTERVIEW_ID = :interview_id
                    """,
                    {
                        "ANSWER_PATH": file_content,  # Store the file as BLOB
                        "score_colb": '{}',  # Reset or keep existing score
                        "question_id": int(question_id),
                        "interview_id": int(interview_id),
                    }
                )
            else:
                # Insert new answer
                cursor.execute(
                    """
                    INSERT INTO osadm.INTERVIEWS_ANSWERS (QUESTION_ID, INTERVIEW_ID, ANSWER_PATH, SCORE_COLB)
                    VALUES (:question_id, :interview_id, :ANSWER_PATH, :score_colb)
                    """,
                    {
                        "question_id": int(question_id),
                        "interview_id": int(interview_id),
                        "ANSWER_PATH": file_content,  # Store the file as BLOB
                        "score_colb": '{}',  # Empty JSON initially
                    }
                )
        conn.commit()

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
