from flask import Flask, request, jsonify, Blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import uuid
import os
import time
import re
import json
from db import db
from pydantic import BaseModel, Field

chatbot_pb = Blueprint('chatbot', __name__)
load_dotenv(dotenv_path='/home/Asem.Aydi/projects/APIs/interviews_APIs/.env')


# Initialize Flask App
app = Flask(__name__)
limiter = Limiter(app)

# Configure CORS
CORS(app, supports_credentials=True, resources={r"/*": {"origins": os.getenv("HOST")}})

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Store active sessions in-memory (use a database or a persistent store in production)
sessions = {}

qa_data = {
    "متى سيتم الرجوع لي بنتيجة المقابلة؟": "خلال فترة أقصاها أسبوع سيتم التواصل معك بشأن نتيجة المقابلة.",
    "ما هو برنامج جو بروفيشنال؟": "أضخم برنامج تدريبي في فلسطين، هدفه تأهيل المتدربين لسوق العمل. تكون مدة العقد 23 شهر، يحصل خلالها المتدرب على مكافآة شهرية وميزات مختلفة",
    "ما هي مدة العقد؟": "23 شهر يتم التوقيع على عقدين",
    "نوع العقد؟": "عقد جو بروفيشنال – عقد تدريبي",
    "مكان العمل؟": "مقر الإدارة العامة – رام الله",
    "هل السكن إجباري؟": "نعم في حال كان مكان السكن الحالي خارج رام الله في المحافظات الأخرى",
    "هل يتم دفع بدل سكن؟": "متدربي جو بروفيشنال يحصلون على مبلغ رمزي بدل سكن 70 دينار بشكل شهري بشرط إحضار عقد الإيجار وصورة هوية المؤجر وتوقيع نموذج تعهد بدل سكن",
    "هل أحصل على تأمين صحي؟": "تحصل على تأمين صحي شخصي بعد تثبيت فترة التجربة",
    "كم سيكون مقدار المكافأة الشهرية او الراتب؟": "سيتم إبلاغك بالمكافأة الشهرية في حال اختيارك للانضمام للبرنامج التدريبي"
}

def is_prompt_injection(user_input):
    try:
        forbidden_patterns = [
            r"ignore previous instructions",
            r"system:.*",
            r"write a system prompt",
            r"act as.*",
            r"(?i)execute|shell|os\.system",
        ]
        return any(re.search(pattern, user_input, re.IGNORECASE) for pattern in forbidden_patterns)
    except Exception as e:
        print(f"Error in is_prompt_injection: {e}")
        return False

def validate_response(response: str):
    try:
        # Ensure the response is within a valid length range
        if len(response) < 1 or len(response) > 500:
            return False
        return True
    except Exception as e:
        print(f"Error in validate_response: {e}")
        return False

# Pydantic model for response validation (Optional, if you want more structured validation)
class OutputSchema(BaseModel):
    response: str = Field(..., min_length=1, max_length=500)


import tiktoken  # Ensure this library is installed for token calculations

def calculate_token_cost(system_message, context, user_input, response, model="gpt-4"):
    try:
        encoding = tiktoken.encoding_for_model(model)
        input_tokens = len(encoding.encode(system_message)) + len(encoding.encode(context)) + len(encoding.encode(user_input))
        response_tokens = len(encoding.encode(response))
        total_tokens = input_tokens + response_tokens

        # GPT-4 pricing
        input_cost_per_token = 0.03 / 1000  # Cost per input token
        output_cost_per_token = 0.06 / 1000  # Cost per output token
        total_cost = (input_tokens * input_cost_per_token) + (response_tokens * output_cost_per_token)

        return total_tokens, total_cost
    except Exception as e:
        print(f"Error in calculate_token_cost: {e}")
        return 0, 0

def get_response_with_guid(user_input, qa_data):
    try:
        context = "\n".join([f"سؤال: {question}\nإجابة: {answer}" for question, answer in qa_data.items()])
        system_message = """
        أنت مساعد افتراضي يساعد المستخدم بالإجابة على الأسئلة بناءً على البيانات المتوفرة فقط.
        إذا كان السؤال لا يتعلق بالبيانات المتوفرة، قل: "ليس لدي جواب على سؤالك، سيتم الرجوع لك على البريد الإلكتروني المسجل في طلبك."
        """

        for _ in range(3):  # Retry 3 times
            try:
                # Call the correct OpenAI API endpoint for chat models
                response = openai.ChatCompletion.create(
                    model="gpt-4",  # Specify the correct model
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "system", "content": context},
                        {"role": "user", "content": user_input},
                    ],
                )
                raw_response = response.choices[0].message['content'].strip()
                return raw_response  # Return the response text only
            except Exception as e:  # Catch all exceptions
                print(f"Error in get_response_with_guid (API call): {e}")
                time.sleep(2)  # Retry after 2 seconds
        return "حدث خطأ يرجى المحاولة لاحقاً."
    except Exception as e:
        print(f"Error in get_response_with_guid: {e}")
        return "حدث خطأ يرجى المحاولة لاحقاً."

def save_chat_history_to_db(user_id, chat_history, total_cost):
    try:
        # Prepare the JSON data as a string
        chat_history_json = json.dumps({
            "history": chat_history,
            "total_cost": total_cost
        })

        # Oracle query for updating the CLOB column
        query = """
            UPDATE osadm.INTERVIEWS_INTERVIEWS 
            SET user_chat_history = :chat_history, interview_status = '3'
            WHERE "USER_ID" = :user_id
        """
        params = {
            "chat_history": chat_history_json,
            "user_id": user_id  # Ensure this matches your database column name
        }

        # Execute the query
        db.execute(query, params)
        print(f"Chat history saved for user_id: {user_id}")
    except Exception as e:
        print(f"Error in save_chat_history_to_db: {e}")

@chatbot_pb.route('/start-session', methods=['GET'])
def start_session():
    try:
        session_id = str(uuid.uuid4())  # Generate a unique session ID
        sessions[session_id] = {
            "messages": [],
            "total_cost": 0,
            "question_count": 0  # Initialize question count
        }
        print("Session started with ID:", session_id)  # Debug log
        return jsonify({"message": "Session started", "session_id": session_id})
    except Exception as e:
        print(f"Error in start_session: {e}")
        return jsonify({"error": f"Failed to start session: {str(e)}"}), 500

@chatbot_pb.route('/chat', methods=['POST'])
@limiter.limit("5 per minute")
def chat():
    try:
        data = request.json
        session_id = data.get('session_id')
        user_input = data.get('user_input', '')
        user_id = data.get('user_id')  # Pass `user_id` from the frontend request

        if not session_id or session_id not in sessions:
            return jsonify({"error": "Invalid or expired session"}), 400

        if not user_input:
            return jsonify({"error": "No user input provided"}), 400

        session_data = sessions[session_id]

        # Enforce question limit
        if session_data['question_count'] >= 5:
            return jsonify({"response": "لقد وصلت إلى الحد الأقصى لعدد الأسئلة (5)."}), 400

        # Generate chatbot response
        bot_response = get_response_with_guid(user_input, qa_data)

        # Update session data
        session_data['messages'].append({"user": user_input, "bot": bot_response})
        session_data['question_count'] += 1

        # Save the chat history to the database
        try:
            save_chat_history_to_db(user_id, session_data['messages'], session_data.get('total_cost', 0))
        except Exception as e:
            print(f"Error saving chat history to database: {str(e)}")
            return jsonify({"error": "Failed to save chat history"}), 500

        return jsonify({
            "response": bot_response,  # Send only the response text
            "questions_remaining": 5 - session_data['question_count']
        })
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"error": f"An error occurred during the chat: {str(e)}"}), 500

@chatbot_pb.route('/end-session', methods=['POST'])
def end_session():
    try:
        data = request.json
        session_id = data.get('session_id')
        user_id = data.get('user_id')

        if not session_id or session_id not in sessions:
            return jsonify({"error": "Invalid or expired session"}), 400

        session_data = sessions.pop(session_id)
        return jsonify({
            "message": "Session ended",
            "messages": session_data['messages'],
            "total_cost": round(session_data['total_cost'], 2)
        })
    except Exception as e:
        print(f"Error in end_session: {e}")
        return jsonify({"error": f"An error occurred while ending the session: {str(e)}"}), 500
