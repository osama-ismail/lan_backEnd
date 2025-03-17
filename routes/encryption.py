import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from db import db 

# Encryption function
def encrypt_file(file_data):
    # Generate a random 256-bit key and initialization vector (IV)
    key = os.urandom(32)  # AES 256-bit key
    iv = os.urandom(16)  # AES block size (128-bit IV)

    # Initialize AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the file data to make it a multiple of block size (16 bytes)
    padder = padding.PKCS7(128).padder()  # AES block size is 128 bits (16 bytes)
    padded_data = padder.update(file_data) + padder.finalize()

    # Encrypt the padded file data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Return the encrypted data, IV, and key (base64 encoded for transmission)
    return encrypted_data, iv, key

# Decryption function
def decrypt_file(encrypted_data, iv, key):
    # Decode base64 encoded encrypted data, IV, and key
    encrypted_data = base64.b64decode(encrypted_data)
    iv = base64.b64decode(iv)
    key = base64.b64decode(key)

    # Initialize AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the data
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(128).unpadder()
    unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

    return unpadded_data

# Method to encrypt video, save encrypted data in a blob in the database
def encrypt_video_and_save_to_db(file_data, query):
    try:
        # Encrypt the video file (whether it's an image or a video)
        encrypted_data, iv, key = encrypt_file(file_data)

        # Save the encrypted video as a blob in the database
        db.execute(query, (encrypted_data, iv, key))  # Save encrypted data, IV, and key

        # Return confirmation
        return {'message': 'Video encrypted and saved to database as BLOB successfully!'}

    except Exception as e:
        return {'error': str(e)}

# Method to decrypt video from database using the encrypted blob
def decrypt_video_from_db(query, db_params):
    try:
        # Query to retrieve the encrypted video from the database
        result = db.execute(query, db_params).fetchone()
        
        if not result:
            return {'error': 'Video not found in database'}
        
        encrypted_data, iv, key = result
        
        # Decrypt the video
        decrypted_data = decrypt_file(encrypted_data, iv, key)

        # Return the decrypted video data (base64 encoded for easier transport)
        return {'decrypted_video': base64.b64encode(decrypted_data).decode('utf-8')}

    except Exception as e:
        return {'error': str(e)}

