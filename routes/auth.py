import json
import os
import random
import jwt  # Import PyJWT
from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta
from db import db 

from routes.auth_middleware import check_api_key

app = Flask(__name__)
auth_bp = Blueprint('auth', __name__)

JWT_SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key")

def generate_jwt(email):
    """Generate a JWT token with expiration time."""
    expiration = datetime.utcnow() + timedelta(hours=1)  
    payload = {
        "email": email,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token

@auth_bp.route('/auth', methods=['POST'])
def login():
    """
    Login API - Verifies user credentials, checks login attempts, and generates PIN.
    """
    try:
        api_check = check_api_key()
        if api_check:
            return api_check

        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"statusCode": "0", "message": "Both email and password are required"}), 400

        query = """
            SELECT PASSWORD, LOGIN_ATTEMPTS, IS_LOGGEDIN 
            FROM AI_USERS WHERE LOWER(EMAIL) = :email
        """
        user = db.execute(query, {"email": email}).fetchone()

        if not user:
            return jsonify({"statusCode": "0", "message": "Failed - User not found"}), 404

        db_password, login_attempts, is_loggedin = user

        if login_attempts >= 4:
            return jsonify({"statusCode": "0", "message": "Too many failed login attempts. Try again later."}), 403
        
        if is_loggedin:
            return jsonify({"statusCode": "0", "message": "User is already logged in"}), 403

        if db_password != password:
            return jsonify({"statusCode": "0", "message": "Invalid password"}), 401

        new_pincode = str(random.randint(100000, 999999))
        update_query = """
            UPDATE AI_USERS 
            SET PINCODE = :pincode, LOGIN_ATTEMPTS = LOGIN_ATTEMPTS + 1 
            WHERE LOWER(EMAIL) = :email
        """
        db.execute(update_query, {"pincode": new_pincode, "email": email})


        return jsonify({
            "statusCode": "1",
            "message": "Pin code sent successfully",
        }), 200

    except Exception as e:
        return jsonify({"statusCode": "0", "message": f"Error: {str(e)}"}), 500

@auth_bp.route('/validatePinCode', methods=['POST'])
def validate_pin_code():
    """
    Validate Pin Code API - Verifies the PIN for authentication.
    """
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        pinCode = data.get("pinCode", "").strip()

        if not email or not pinCode:
            return jsonify({"statusCode": "0", "message": "Email and PIN code are required"}), 400

        query = "SELECT PINCODE FROM AI_USERS WHERE LOWER(EMAIL) = :email"
        user = db.execute(query, {"email": email}).fetchone()

        if not user:
            return jsonify({"statusCode": "0", "message": "User not found"}), 404

        stored_pincode = user[0]

        if stored_pincode != pinCode:
            return jsonify({"statusCode": "0", "message": "Invalid PIN code"}), 401
        token = generate_jwt(email)

        return jsonify({
            "statusCode": "1",
            "message": "Login successful",
            "token":token
        }), 200

    except Exception as e:
        return jsonify({"statusCode": "0", "message": f"Error: {str(e)}"}), 500
