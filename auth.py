import sqlite3
import hashlib
import uuid

# =========================
# DATABASE CONNECTION
# =========================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# TABLES
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    chat_id TEXT,
    role TEXT,
    content TEXT
)
""")

conn.commit()

# =========================
# PASSWORD HASH
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# AUTH
# =========================
def create_user(username, password):
    try:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return cursor.fetchone()

# =========================
# SAVE CHAT
# =========================
def save_chat(username, chat_id, role, content):
    if chat_id is None:
        chat_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO chats (username, chat_id, role, content) VALUES (?, ?, ?, ?)",
        (username, chat_id, role, content)
    )
    conn.commit()
    return chat_id

# =========================
# LOAD CHATS (CHATGPT STYLE)
# =========================
def load_chats(username, grouped=False):
    cursor.execute(
        """
        SELECT chat_id, role, content
        FROM chats
        WHERE username=?
        ORDER BY id
        """,
        (username,)
    )
    rows = cursor.fetchall()

    if not grouped:
        return [(r[1], r[2]) for r in rows]

    chats = {}
    for chat_id, role, content in rows:
        if chat_id not in chats:
            chats[chat_id] = {
                "title": content[:30] if content else "New Chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful, friendly AI assistant."
                    }
                ]
            }

        chats[chat_id]["messages"].append(
            {"role": role, "content": content}
        )

    return chats



