from flask import Blueprint, request, jsonify
import json
import os
from db import db  # Assuming these are helper functions for DB queries

questions_bp = Blueprint('questions', __name__)

CACHE_FILE = "cached_users.json"

def load_cached_users():
    """Load cached users from the JSON file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            return data.get("users", [])
        return []
    except Exception as e:
        print(f"Error in load_cached_users: {e}")
        return []

@questions_bp.route('/next', methods=['POST'])
def get_next_question():
    """Fetch the first unanswered question for the given user from the database."""
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        users = load_cached_users()
        
        user = next((u for u in users if u["user_id"] == user_id), None)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Find the first unanswered question
        for question_id, status in user["questions"].items():
            if status == 0:  # Unanswered
                # Fetch full question details from the database
                query = "SELECT * FROM osadm.INTERVIEWS_QUESTIONS WHERE QUESTION_ID = :question_id"
                question_data = db.fetch_one(query, {"question_id": question_id})
                
                if question_data:
                    return jsonify({"question": question_data}), 200
                else:
                    return jsonify({"error": "Question not found in database"}), 404

        return jsonify({"message": "No unanswered questions"}), 200
    
    except Exception as e:
        print(f"Error in get_next_question: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@questions_bp.route('/count', methods=['POST'])
def get_question_count():
    """Returns the total number of questions assigned to a user."""
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        users = load_cached_users()
        
        user = next((u for u in users if u["user_id"] == user_id), None)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        question_count = len(user["questions"])
        
        return jsonify({"user_id": user_id, "total_questions": question_count}), 200
    
    except Exception as e:
        print(f"Error in get_question_count: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
