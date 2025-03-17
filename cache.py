import json
import os
from db import db
from datetime import datetime
from dotenv import load_dotenv


load_dotenv(dotenv_path='/home/Asem.Aydi/projects/APIs/interviews_APIs/.env')


CACHE_FILE = os.getenv("CACHE_FILE")



def fetch_users_for_today():
    """Fetch users allowed to log in today, joining AI_INTERVIEWS, AI_USERS, and AI_SCHEDULE."""
    try:
        

        
        # Query to fetch users with interview and schedule details
        query = """
       SELECT a.INTERVIEW_ID, a.POSITION_ID, a.USER_ID, 
               b.REFERENCE_NUMBER, b.FILE_NAME, b.NAME, b.EMAIL, 
               b.MOBILE, b.PHONE, b.PINCODE, b.CREATED_AT, 
               b.LOGIN_ATTEMPTS, b.IS_LOGGEDIN, b.password, 
               c.SLOT_DATE, c.SLOT_TIME, c.SLOT_DURATION
        FROM osadm.INTERVIEWS_INTERVIEWS a
        LEFT JOIN osadm.INTERVIEWS_USERS b ON a.USER_ID = b.USER_ID
        LEFT JOIN osadm.INTERVIEWS_SCHEDULE c ON a.SCHEDULE_ID = c.SCHEDULE_ID
        WHERE TRUNC(c.SLOT_DATE) = TRUNC(sysdate)
        
        """
        
        # Fetch user data
        result = db.fetch_all(query)
        users = []
        
        for row in result:
            (
                interview_id, position_id, user_id, 
                reference_number, file_name, name, email, 
                mobile, phone, pincode, created_at, 
                login_attempts, is_logged_in, password, 
                slot_date, slot_time, slot_duration
            ) = row
            
            # Ensure slot_date is properly formatted
            slot_date = slot_date.strftime('%Y-%m-%d') if isinstance(slot_date, datetime) else slot_date

            # Fetch questions related to the position
            question_query = """
            SELECT QUESTION_ID FROM osadm.INTERVIEWS_QUESTIONS WHERE POSITION_ID = :position_id
            """
            question_results = db.fetch_all(question_query, {'position_id': position_id})

            # Store questions with initial state 0
            questions = {str(q[0]): 0 for q in question_results}

            # Append all retrieved data
            users.append({
                "interview_id": interview_id,
                "position_id": position_id,
                "user_id": user_id,
                "reference_number": reference_number,
                "file_name": file_name,
                "name": name,
                "email": email,
                "mobile": mobile,
                "phone": phone,
                "pincode": pincode,
                "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(created_at, datetime) else created_at,
                "login_attempts": login_attempts,
                "is_logged_in": bool(is_logged_in),
                "password": password,  # Consider handling security (e.g., hashing)
                "slot_date": slot_date,
                "slot_time": slot_time.strftime('%H:%M:%S') if isinstance(slot_time, datetime) else slot_time,
                "slot_duration": slot_duration,
                "questions": questions
            })

        return users

    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

    
def update_cache():
    """Deletes old data and updates the cache with today's users."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Delete old cache file if it exists
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)  # Remove old data completely

    # Fetch new users and create a fresh cache
    users = fetch_users_for_today()
    data = {"date": today, "users": users}

    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("Cache updated successfully with fresh data.")
    except Exception as e:
        print(f"Error updating cache: {e}")

def get_cached_users():
    """Returns the list of all cached users."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            return data.get("users", [])
        except Exception as e:
            print(f"Error reading cache: {e}")
            return []
    else:
        return []


def get_cached_user_by_id(user_id):
    """Returns a specific cached user by user_id."""
    users = get_cached_users()
    # Find the user with the specified user_id
    user = next((user for user in users if user["user_id"] == user_id), None)
    return user



if __name__ == '__main__':
    update_cache()
    

