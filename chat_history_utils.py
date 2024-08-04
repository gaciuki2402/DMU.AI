import sqlite3
from langchain_community.chat_message_histories import SQLChatMessageHistory

CHAT_HISTORY_DB = "chat_history.db"

def get_chat_history(session_id: str):
    history = SQLChatMessageHistory(session_id=session_id, connection_string=f"sqlite:///{CHAT_HISTORY_DB}")
    return history.messages


def query_chat_history(query: str, params: tuple = ()):
    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
# Example queries
def get_all_sessions():
    return query_chat_history("SELECT DISTINCT session_id FROM chat_messages")

def get_messages_for_session(session_id: str):
    return query_chat_history("SELECT message_type, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp", (session_id,))

def get_recent_messages(limit: int = 10):
    return query_chat_history("SELECT session_id, message_type, content, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT ?", (limit,))

