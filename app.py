from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from routes.test import test_bp
from routes.user import users_bp
from routes.answers import answers_bp
from routes.auth import auth_bp
from routes.chatbot import chatbot_pb
from routes.face_detection import face_bp
from routes.ID_detection import id_bp
from routes.questions import questions_bp
# from cache import update_cache, CACHE_FILE 

import os

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://10.64.5.117:3000"}}, supports_credentials=True)

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.secret_key = os.getenv("SECRET_KEY")

# Initialize Flask-Session
Session(app)

# Initialize Flask-Limiter (Rate Limiting)
limiter = Limiter(
    get_remote_address,  # Identify users by their IP address
    app=app,
    default_limits=["2000 per day", "200 per hour"]  # Default limit for all routes
)

# Register blueprints with rate limits
app.register_blueprint(test_bp, url_prefix='/test')
app.register_blueprint(questions_bp, url_prefix='/questions')
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(answers_bp, url_prefix='/answers')
app.register_blueprint(chatbot_pb, url_prefix='/chatbot')
app.register_blueprint(auth_bp, url_prefix='/auth')



# Run cache update once at startup
# update_cache()



# @app('/test1233', methods=['GET'])
# def upload_video():
#     return 'hi'


if __name__ == "__main__":
    app.run(host="172.19.8.57", port=5011, debug= False )  
