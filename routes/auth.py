import json
import os
import random
import jwt  # Import PyJWT
from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta
from db import db 

from routes.auth_middleware import check_api_key
from datetime import datetime, timedelta, date
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
        email = data.get("email", "")
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"statusCode": "0", "message": "Both email and password are required"}), 400

        db.connect()
        conn = db.connection

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT a.PASSWORD, a.LOGIN_ATTEMPTS, a.IS_LOGGEDIN, 
                       c.slot_time, c.slot_duration
                FROM osadm.interviews_users a
                JOIN osadm.interviews_interviews b ON a.user_id = b.user_id
                JOIN osadm.interviews_schedule c ON b.schedule_id = c.schedule_id
                WHERE a.EMAIL = :email AND a.PASSWORD = :password
                """,
                {"email": email, "password": password}
            )
            user = cursor.fetchone()

        conn.commit()
        print("user:", user)

        if not user:
            return jsonify({"statusCode": "0", "message": "Failed - User not found"}), 404

        db_password, login_attempts, is_loggedin, slot_time, slot_duration = user

        # Ensure login_attempts is not None
        if login_attempts is None:
            login_attempts = 0

        if login_attempts >= 4:
            return jsonify({"statusCode": "0", "message": "Too many failed login attempts. Try again later."}), 403

        if is_loggedin:
            return jsonify({"statusCode": "0", "message": "User is already logged in"}), 403

        if db_password != password:
            return jsonify({"statusCode": "0", "message": "Invalid password"}), 401

        if isinstance(slot_time, str):
          slot_time = datetime.strptime(slot_time, "%Y-%m-%d %H:%M:%S")

        if date.today() == slot_duration:
            now = datetime.now()
            time_diff = now - slot_time

            if now == slot_time or (slot_time <= now <= slot_time + timedelta(minutes=15)):
                new_pincode = str(random.randint(100000, 999999))
                update_query = """
                    UPDATE osadm.interviews_users 
                    SET PINCODE = :pincode, LOGIN_ATTEMPTS = LOGIN_ATTEMPTS + 1 
                    WHERE EMAIL = :email
                """
                db.execute(update_query, {"pincode": new_pincode, "email": email})

                return jsonify({
                    "statusCode": "1",
                    "message": "Pin code sent successfully",
                }), 200
            else:
                return jsonify({"statusCode": "0", "message": "Invalid time slot"}), 403
        else:
            return jsonify({"statusCode": "0", "message": "Invalid date"}), 403

    except Exception as e:
        print(e)
        return jsonify({"statusCode": "0", "message": "Internal server error"}), 500
@auth_bp.route('/validatePinCode', methods=['POST'])
def validate_pin_code():
    """
    Validate Pin Code API - Verifies the PIN for authentication.
    """
    try:
        data = request.json
        email = data.get("email", "")
        pinCode = data.get("pinCode", "")
        db.connect()
        conn = db.connection
        if not email or not pinCode:
            return jsonify({"statusCode": "0", "message": "Email and PIN code are required"}), 400
        with conn.cursor() as cursor:
            # Check if the answer already exists (fetch all matching records)
            cursor.execute(
                """
               SELECT PINCODE FROM osadm.interviews_users WHERE EMAIL = :email
                """,
                {"email": email}
            )
            user = cursor.fetchone()
        conn.commit()
        if not user:
            return jsonify({"statusCode": "0", "message": "User not found"}), 404

        stored_pincode = user[0]
        if stored_pincode is None:
            return jsonify({"statusCode": "0", "message": "Invalid PIN code"}), 401
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
