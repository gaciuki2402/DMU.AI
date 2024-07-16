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

def get_conversation_history(conversation_id, limit=5):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        SELECT question, answer 
        FROM interactions 
        WHERE conversation_id = ?
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (conversation_id, limit))
    history = c.fetchall()
    conn.close()
    return history[::-1]  # Reverse to get chronological order

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

def get_positive_interactions(threshold=3):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT question, answer FROM interactions WHERE user_feedback > ?", (threshold,))
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
