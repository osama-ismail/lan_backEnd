import cv2
import face_recognition
from flask import Blueprint, request, jsonify
import numpy as np
from routes.auth_middleware import jwt_required
 
face_bp = Blueprint('face_detection', __name__)
 
@jwt_required 
@face_bp.route('face_detection', methods=['POST'])
def detect_faces():
    """
    Face Detection API - Checks if a face is present in an image and counts the number of detected faces.
    """
    try:
        # Ensure the request contains an image file
        if 'image' not in request.files:
            return jsonify({"error": "Image file is required"}), 400
 
        image_file = request.files['image']
 
        # Read the image file into a numpy array
        image_bytes = np.frombuffer(image_file.read(), np.uint8)
        # Decode the image to color format using OpenCV
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
 
        # Check if the image was loaded correctly
        if image is None:
            return jsonify({"error": "Failed to load image. The image may be corrupted or unsupported."}), 400
 
        # Convert the image to RGB (required by face_recognition)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
 
        # Detect faces in the image using face_recognition
        face_locations = face_recognition.face_locations(rgb_image)
 
        # If no faces are detected, return a message indicating so
        if len(face_locations) == 0:
            return jsonify({"message": "No faces detected"}), 200
 
        # Return the number of faces detected
        return jsonify({"status": "200", "faces_count": len(face_locations)}), 200
 
    except Exception as e:
        return jsonify({"error": f"Error in detect_faces: {str(e)}"}), 500