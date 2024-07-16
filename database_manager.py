import sqlite3
from datetime import datetime

DATABASE = 'bot_interactions.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id TEXT NOT NULL,
                  question TEXT NOT NULL,
                  answer TEXT NOT NULL,
                  format TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  user_feedback INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id TEXT PRIMARY KEY,
                  title TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def store_interaction(conversation_id, question, answer, format):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO interactions (conversation_id, question, answer, format) VALUES (?, ?, ?, ?)",
              (conversation_id, question, answer, format))
    interaction_id = c.lastrowid
    conn.commit()
    conn.close()
    return interaction_id

def update_feedback(interaction_id, feedback):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE interactions SET user_feedback = ? WHERE id = ?", (feedback, interaction_id))
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        SELECT question, answer, timestamp
        FROM interactions 
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,))
    history = c.fetchall()
    conn.close()
    return history

def get_all_conversations():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, title FROM conversations ORDER BY created_at DESC")
    conversations = c.fetchall()
    conn.close()
    return conversations

def create_new_conversation(conversation_id, title):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (conversation_id, title))
    conn.commit()
    conn.close()

def update_conversation_title(conversation_id, title):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
    conn.commit()
    conn.close()

def get_recent_positive_interactions(limit=10, threshold=3):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        SELECT question, answer 
        FROM interactions 
        WHERE user_feedback > ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (threshold, limit))
    positive_interactions = c.fetchall()
    conn.close()
    return positive_interactions

def get_interaction_count():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM interactions")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_average_feedback():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT AVG(user_feedback) FROM interactions WHERE user_feedback IS NOT NULL")
    avg_feedback = c.fetchone()[0]
    conn.close()
    return avg_feedback