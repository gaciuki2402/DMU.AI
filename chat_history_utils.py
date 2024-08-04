import psycopg2
from psycopg2 import pool
import os
from langchain_community.chat_message_histories import PostgresChatMessageHistory

DATABASE_URL = os.environ.get('DATABASE_URL')


# Create a connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)

def get_chat_history(session_id: str):
    history = PostgresChatMessageHistory(
        session_id=session_id,
        connection_string=DATABASE_URL,
        table_name="chat_messages"
    )
    return history.messages

def query_chat_history(query: str, params: tuple = ()):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        connection_pool.putconn(conn)

    
# Example queries
def get_all_sessions():
    return query_chat_history("SELECT DISTINCT session_id FROM chat_messages")

def get_messages_for_session(session_id: str):
    return query_chat_history("SELECT message_type, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp", (session_id,))

def get_recent_messages(limit: int = 10):
    return query_chat_history("SELECT session_id, message_type, content, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT ?", (limit,))

