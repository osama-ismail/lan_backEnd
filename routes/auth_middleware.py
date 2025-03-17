import os
import jwt
from flask import request, jsonify
from functools import wraps

# Secret key (must be same as the one used to generate JWT)
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key")

API_KEY = "YOUR_SECRET_API_KEY"  # Replace with an environment variable in production

def check_api_key():
    """Middleware function to check API Key in request headers"""
    api_key = request.headers.get('API-KEY')
    if api_key != API_KEY:
        return jsonify({"message": "Forbidden: Invalid API Key"}), 403  # Return 403 Forbidden
def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return jsonify({"message": "Missing Authorization header"}), 401

            # Ensure header has 'Bearer <token>' format
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != "Bearer":
                return jsonify({"message": "Invalid token format"}), 401

            token = parts[1]  # Extract JWT token

            # Decode JWT token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

            # Attach user email to request for use in views
            request.user_email = payload.get("email")

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"message": f"Token error: {str(e)}"}), 500

    return decorated_function
