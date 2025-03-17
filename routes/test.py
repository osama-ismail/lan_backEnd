from flask import Blueprint, jsonify
from db import db
from .auth_middleware import check_api_key, jwt_required  # Ensure this matches your JWT file name


test_bp = Blueprint('test', __name__)

@test_bp.route('/test-db', methods=['GET'])
@jwt_required 
def test_db():
    try:
        api_check = check_api_key()
        if api_check:  # If invalid, return error response
            return api_check
        query = "SELECT * FROM dual"
        result = db.fetch_all(query)
        return jsonify({"message": "Database connection successful", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

