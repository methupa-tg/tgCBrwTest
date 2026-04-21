import mysql.connector
from datetime import datetime

import os

def get_conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "thyaga_chatbot")
    )

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Database ready.")

def save_message(session_id, role, content):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (%s, %s, %s, %s)",
        (session_id, role, content, datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_all_sessions():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT session_id, MIN(timestamp) as started, COUNT(*) as message_count
        FROM messages
        GROUP BY session_id
        ORDER BY started DESC
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_session_messages(session_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE session_id = %s ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows