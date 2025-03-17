import json
import os
import jwt  # Import PyJWT
from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta

from routes.auth_middleware import check_api_key

app = Flask(__name__)
auth_bp = Blueprint('auth', __name__)

# Path to the JSON file (Ensure it's correct!)
JSON_FILE_PATH = "cached_users.json"

# Secret key for JWT (Store securely in an env variable)
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key")  # Change this in production

def generate_jwt(email):
    """Generate a JWT token with expiration time."""
    expiration = datetime.utcnow() + timedelta(hours=1)  # Token expires in 2 hours
    payload = {
        "email": email,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token

@auth_bp.route('/auth', methods=['POST'])
def login():
    """
    Login API - Verifies user credentials, generates JWT if successful.
    """
    try:
        api_check = check_api_key()
        if api_check:  # If invalid, return error response
            return api_check
        # Get request data
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"statusCode": "0", "message": "Both email and password are required"}), 400

        # Check if JSON file exists
        if not os.path.exists(JSON_FILE_PATH):
            return jsonify({"statusCode": "0", "message": "Cached user file not found"}), 500

        # Load users from JSON file
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
            users_data = json.load(file)

        print(f"Users Data: {users_data}")  # Debugging
        print(f"Looking for: {email}")  # Debugging

        # Find user by email (Case insensitive)
        user = next((user for user in users_data.get("users", []) if user.get("email", "").strip().lower() == email), None)

        print(f"Found user: {user}")  # Debugging

        if not user:
            return jsonify({"statusCode": "0", "message": "Failed - User not found"}), 404

        # Check slot date
        slot_date_str = user.get("slot_date", "")
        if not slot_date_str:
            return jsonify({"statusCode": "0", "message": "Invalid slot time"}), 400

        try:
            slot_time = datetime.strptime(slot_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"statusCode": "0", "message": "Invalid slot time format"}), 400

        now = datetime.utcnow()
        
        # Check if login is on the correct date
        if slot_time.date() != now.date():
            return jsonify({
                "statusCode": "0",
                "message": "Login is only allowed on your slot date"
            }), 403

        # Validate password
        print(f"Stored Password: {user.get('password')} | Entered Password: {password}")  # Debugging
        if user.get("password") != password:
            return jsonify({"statusCode": "0", "message": "Invalid password"}), 401

        # Generate JWT token
        token = generate_jwt(email)

        return jsonify({
            "statusCode": "1",
            "message": "pin code sent successfully",
            "token": token
        }), 200

    except Exception as e:
        return jsonify({
            "statusCode": "0",
            "message": f"Error: {str(e)}"
        }), 500

# Register the blueprint
app.register_blueprint(auth_bp)


@auth_bp.route('/validatePinCode', methods=['POST'])
def login():
    """
    Login API - Verifies user credentials, generates JWT if successful.
    """
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        pinCode = data.get("pinCode", "").strip()
        return jsonify({
            "statusCode": "1",
            "message": "Login successful"
        }), 200

    except Exception as e:
        return jsonify({
            "statusCode": "0",
            "message": f"Error: {str(e)}"
        }), 500



if __name__ == '__main__':
    app.run(debug=True, port=5001)
