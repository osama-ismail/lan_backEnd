# from flask import Blueprint, request, jsonify
# import face_recognition
# import cv2
# from db import db
# import numpy

# from routes.auth_middleware import check_api_key, jwt_required

# # Create a Blueprint for ID-related operations
# id_bp = Blueprint('id', __name__)

# def enc_id(file_id):
#     try:
#         image_id = cv2.cvtColor(file_id, cv2.COLOR_BGR2RGB)
#         for i in range(4):
#             encodings_id = face_recognition.face_encodings(image_id)
#             if len(encodings_id) == 1:
#                 return encodings_id
#             image_id = cv2.rotate(image_id, cv2.ROTATE_90_CLOCKWISE)
#         return 'صورة الوجه غير واضحة او يوجد عدة وجوه بالصورة'
#     except Exception as e:
#         print(f"Error in enc_id: {e}")
#         return 'Error in encoding ID image'

# def enc_selfi(selfi_img):
#     try:
#         image_selfi = cv2.cvtColor(selfi_img, cv2.COLOR_BGR2RGB)
#         encodings_image_selfi = face_recognition.face_encodings(image_selfi)
#         if len(encodings_image_selfi) != 1:
#             return 'صورة الوجه غير واضحة او يوجد عدة وجوه بالصورة'
#         return encodings_image_selfi
#     except Exception as e:
#         print(f"Error in enc_selfi: {e}")
#         return 'Error in encoding selfie image'

# def compare(file_id, selfi_img):
#     try:
#         matches = face_recognition.compare_faces(enc_selfi(selfi_img), enc_id(file_id)[0], .6)[0]
#         if matches:
#             face_distances = face_recognition.face_distance(enc_id(file_id)[0], enc_selfi(selfi_img))
#             similarity_percentage = (1 - face_distances[0]) * 100
#             print(f"Similarity: {similarity_percentage:.2f}%")
#             return similarity_percentage
#         return 'نسبة التطابق قليلة'
#     except Exception as e:
#         print(f"Error in compare: {e}")
#         return 'Error in comparing faces'

# # Endpoint to compare faces and update interview status
# @jwt_required 
# @id_bp.route('/compare_faces', methods=['POST'])
# def compare_faces():
#     try:
#         api_check = check_api_key()
#         if api_check:  # If invalid, return error response
#             return api_check
#         # Get the uploaded images from the request
#         file_id = request.files['id_image'].read()
#         selfie_img = request.files['selfie_image'].read()

#         # Convert images to numpy arrays
#         nparr_id = numpy.frombuffer(file_id, numpy.uint8)
#         file_id_image = cv2.imdecode(nparr_id, cv2.IMREAD_COLOR)

#         nparr_selfie = numpy.frombuffer(selfie_img, numpy.uint8)
#         selfie_image = cv2.imdecode(nparr_selfie, cv2.IMREAD_COLOR)

#         # Compare the faces
#         similarity = compare(file_id_image, selfie_image)

#         # If similarity is above a certain threshold, update the interview status
#         if isinstance(similarity, float) and similarity > 80:  # Assuming 80% as the threshold
#             user_id = request.form.get('user_id')
#             query = "UPDATE osadm.INTERVIEWS_INTERVIEWS SET interview_status = '2' WHERE USER_ID = ?"
#             db.execute(query, (user_id,))
#             return jsonify({"message": "Interview status updated", "similarity": similarity}), 200
        
#         return jsonify({"message": "Low similarity, status not updated", "similarity": similarity}), 200
    
#     except Exception as e:
#         print(f"Error in compare_faces: {e}")
#         return jsonify({"error": str(e)}), 400
