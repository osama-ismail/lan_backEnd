from flask import Blueprint, request, jsonify
from db import db
import json

from routes.auth_middleware import check_api_key, jwt_required

users_bp = Blueprint('users', __name__)
@jwt_required 
@users_bp.route('/save-feedback', methods=['POST'])
def save_feedback():
    """
    Save Feedback API - Stores user feedback as JSON and updates interview status to 4.
    """
    try:
        api_check = check_api_key()
        if api_check:  # If invalid, return error response
            return api_check
        data = request.json
        user_id = data.get("user_id")
        rating = data.get("rating")
        notes = data.get("notes", "")

        if not user_id or rating is None:
            return jsonify({"error": "User ID and rating are required"}), 400

        # Prepare feedback data as JSON
        feedback = json.dumps({
            "rating": rating,
            "notes": notes
        })

        query = """
            UPDATE osadm.INTERVIEWS_INTERVIEWS 
            SET INTERVIEW_STATUS = '4', USER_FEEDBACK = :feedback 
            WHERE USER_ID = :user_id
        """
        
        db.execute(query, {"feedback": feedback, "user_id": user_id})

        return jsonify({
            "status": "200",
            "message": "Feedback saved successfully",
            "feedback": json.loads(feedback),
            "interview_status": 4
        }), 200
    
    except Exception as e:
        return jsonify({"error in feedback": str(e)}), 500
