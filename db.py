import oracledb
import os
from dotenv import load_dotenv


load_dotenv(dotenv_path='/home/Asem.Aydi/projects/APIs/interviews_APIs/.env')

# Set environment variable for encoding
os.environ["NLS_LANG"] = ".AL32UTF8"

class Database:
    def __init__(self):
        # Hardcode database credentials
        self.username = os.getenv('DB_USERNAME')        
        self.password = os.getenv('DB_PASSWORD')
        self.dsn = os.getenv('DB_DSN')
        self.connection = None

    def connect(self):
        try:
            # Close the existing connection if stale or invalid
            if self.connection and not self.connection.is_healthy():
                self.close()

            # Establish a new connection if not already open
            if not self.connection:
                self.connection = oracledb.connect(
                    user=self.username,
                    password=self.password,
                    dsn=self.dsn
                )
                print("Database connection established.")
        except oracledb.DatabaseError as e:
            print(f"Failed to connect to the database: {e}")
            raise

    def execute(self, query, params=None):
        cursor = None
        try:
            self.connect()  # Always ensure the connection is active
            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
            self.connection.commit()  # Commit after execution
            return cursor
        except oracledb.DatabaseError as e:
            self.connection.rollback()  # Rollback on error
            print(f"Database error during execute: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()

    def fetch_all(self, query, params=None):
        cursor = None
        try:
            self.connect()  # Always ensure the connection is active
            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
            result = cursor.fetchall()
            return result
        except oracledb.DatabaseError as e:
            print(f"Database error during fetch_all: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
                
    def fetch_one(self, query, params=None):
        cursor = None
        try:
            self.connect()  # Ensure the connection is active
            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
        
            # Fetch one row
            result = cursor.fetchone()
        
            # If a row is returned, map column names to values in a dictionary
            if result:
                columns = [desc[0] for desc in cursor.description]  # Get column names
                result_dict = dict(zip(columns, result))  # Map column names to row values
                return result_dict
            else:
                return None  # Return None if no result is found
        
        except oracledb.DatabaseError as e:
            print(f"Database error during fetch_one: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()


# Initialize the database instance
db = Database()
