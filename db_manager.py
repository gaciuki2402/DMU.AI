import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Database connection parameters from environment variables
host = os.getenv('DB_HOST')
dbname = os.getenv('DB_NAME')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
port = os.getenv('DB_PORT')
schema = os.getenv('DB_SCHEMA')  # Specify your schema here

def execute_db_operation(operation, *args):
    connection = None
    cursor = None
    try:
        # Establish the connection
        connection = psycopg2.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            port=port,
            options=f'-c search_path={schema}'
        )

        # Create a cursor object
        cursor = connection.cursor()

        # Log the operation
        logger.info("Executing operation...")
        
        # Execute the provided operation
        result = operation(cursor, *args)

        # Commit the transaction
        connection.commit()

        logger.info("Operation executed successfully.")
        return result

    except Exception as error:
        logger.error(f"Database error: {error}")
        if connection:
            connection.rollback()
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def init_db():
    def _init(cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            format TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_feedback INTEGER,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
        ''')

    execute_db_operation(_init)

def store_interaction(conversation_id, question, answer, format):
    def _store(cursor):
        cursor.execute('''
        INSERT INTO interactions (conversation_id, question, answer, format)
        VALUES (%s, %s, %s, %s) RETURNING id
        ''', (conversation_id, question, answer, format))
        interaction_id = cursor.fetchone()[0]
        return interaction_id
    
    return execute_db_operation(_store)

def update_feedback(interaction_id, is_helpful):
    def _update(cursor):
        feedback_value = 1 if is_helpful else 0
        cursor.execute('''
        UPDATE interactions 
        SET user_feedback = %s
        WHERE id = %s
        ''', (feedback_value, interaction_id))
    
    execute_db_operation(_update)

def get_feedback_statistics():
    def _get(cursor):
        cursor.execute('''
        SELECT 
            AVG(CASE WHEN user_feedback = 1 THEN 1 ELSE 0 END) as helpful_ratio,
            AVG(CASE WHEN user_feedback = 0 THEN 1 ELSE 0 END) as not_helpful_ratio,
            AVG(user_feedback) as average_feedback
        FROM interactions 
        WHERE user_feedback IS NOT NULL
        ''')
        return cursor.fetchone()
    
    return execute_db_operation(_get)

def get_low_rated_interactions(limit=10):
    def _get(cursor):
        cursor.execute('''
        SELECT id, question, answer, user_feedback
        FROM interactions
        WHERE user_feedback = 0
        ORDER BY timestamp DESC
        LIMIT %s
        ''', (limit,))
        return cursor.fetchall()
    
    return execute_db_operation(_get)

def update_interaction_for_improvement(interaction_id, improved_answer):
    def _update(cursor):
        cursor.execute('''
        UPDATE interactions 
        SET answer = %s, user_feedback = NULL 
        WHERE id = %s
        ''', (improved_answer, interaction_id))
    
    execute_db_operation(_update)

def get_conversation(conversation_id):
    def _get(cursor):
        cursor.execute('''
        SELECT id, title FROM conversations WHERE id = %s
        ''', (conversation_id,))
        return cursor.fetchone()
    
    return execute_db_operation(_get)

def get_conversation_history(conversation_id):
    def _get(cursor):
        cursor.execute('''
        SELECT question, answer, timestamp
        FROM interactions 
        WHERE conversation_id = %s
        ORDER BY timestamp ASC
        ''', (conversation_id,))
        return cursor.fetchall()
    
    return execute_db_operation(_get)

def get_all_conversations():
    def _get(cursor):
        cursor.execute('''
        SELECT id, title FROM conversations ORDER BY created_at DESC
        ''')
        return cursor.fetchall()
    
    return execute_db_operation(_get)

def create_new_conversation(conversation_id: str, title: str):
    def _create(cursor):
        cursor.execute('''
        INSERT INTO conversations (id, title) VALUES (%s, %s)
        ''', (conversation_id, title))
    
    execute_db_operation(_create)

def update_conversation_title(conversation_id, title):
    def _update(cursor):
        cursor.execute('''
        UPDATE conversations SET title = %s WHERE id = %s
        ''', (title, conversation_id))
    
    execute_db_operation(_update)

def get_recent_positive_interactions(limit=10):
    def _get(cursor):
        cursor.execute('''
        SELECT question, answer 
        FROM interactions 
        WHERE user_feedback = 1
        ORDER BY timestamp DESC
        LIMIT %s
        ''', (limit,))
        return cursor.fetchall()
    
    return execute_db_operation(_get)

def get_interaction_count():
    def _get(cursor):
        cursor.execute("SELECT COUNT(*) FROM interactions")
        return cursor.fetchone()[0]
    
    return execute_db_operation(_get)

def get_average_feedback():
    def _get(cursor):
        cursor.execute('''
        SELECT AVG(user_feedback) FROM interactions WHERE user_feedback IS NOT NULL
        ''')
        return cursor.fetchone()[0]
    
    return execute_db_operation(_get)

def delete_conversation(conversation_id):
    def _delete(cursor):
        cursor.execute('''
        DELETE FROM interactions WHERE conversation_id = %s
        ''', (conversation_id,))
        cursor.execute('''
        DELETE FROM conversations WHERE id = %s
        ''', (conversation_id,))
    
    return execute_db_operation(_delete)