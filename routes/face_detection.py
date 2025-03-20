# import cv2
# import face_recognition
# from flask import Blueprint, request, jsonify
# import numpy as np

# from routes.auth_middleware import jwt_required 

# face_bp = Blueprint('face_detection', __name__)
# @jwt_required 
# @face_bp.route('', methods=['POST'])
# def detect_faces():
#     """
#     Face Detection API - Checks if a face is present in an image and counts the number of detected faces.
#     """
#     try:
#         api_check = check_api_key()
#         if api_check:  # If invalid, return error response
#             return api_check
#         if 'image' not in request.files:
#             return jsonify({"error": "Image file is required"}), 400

#         image_file = request.files['image']
        
#         # Convert the image file to a numpy array
#         image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)

#         # Check if the image was loaded correctly
#         if image is None:
#             return jsonify({"error": "Failed to load image"}), 400

#         # Detect faces using face_recognition
#         face_locations = face_recognition.face_locations(image)

#         if len(face_locations) == 0:
#             return jsonify({"error": "No face detected"}), 400

#         return jsonify({"status": "200", "faces_count": len(face_locations)}), 200
    
#     except Exception as e:
#         return jsonify({"error in detect faces": str(e)}), 500
