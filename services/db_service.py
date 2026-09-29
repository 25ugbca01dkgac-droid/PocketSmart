import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables for PocketSmart AI if not existing"""
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Recommendations History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_type TEXT NOT NULL,
        title TEXT NOT NULL,
        total_budget REAL NOT NULL,
        total_estimated_cost REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        summary TEXT,
        data_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recs_user ON recommendations(user_id);")

    conn.commit()
    conn.close()

# --- User DB Operations ---

def create_user(username: str, email: str, password_hash: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?, ?)",
            (username.strip().lower(), email.strip().lower(), password_hash, full_name, now)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "username": username.strip().lower(),
            "email": email.strip().lower(),
            "full_name": full_name,
            "created_at": now
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    ident = identifier.strip().lower()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ? LIMIT 1",
        (ident, ident)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# --- Recommendation History Operations ---

def save_recommendation(
    user_id: Optional[int],
    plan_type: str,
    title: str,
    total_budget: float,
    total_estimated_cost: float,
    currency: str,
    summary: str,
    data_dict: Dict[str, Any]
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    json_str = json.dumps(data_dict)
    cursor.execute(
        """
        INSERT INTO recommendations 
        (user_id, plan_type, title, total_budget, total_estimated_cost, currency, summary, data_json, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, plan_type, title, total_budget, total_estimated_cost, currency, summary, json_str, now)
    )
    conn.commit()
    rec_id = cursor.lastrowid
    conn.close()
    return rec_id

def get_recommendations_by_user(user_id: Optional[int], limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute(
            """
            SELECT id, user_id, plan_type, title, total_budget, total_estimated_cost, currency, summary, data_json, created_at 
            FROM recommendations 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit)
        )
    else:
        cursor.execute(
            """
            SELECT id, user_id, plan_type, title, total_budget, total_estimated_cost, currency, summary, data_json, created_at 
            FROM recommendations 
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recommendation_by_id(rec_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recommendations WHERE id = ? LIMIT 1", (rec_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        result = dict(row)
        try:
            result["data"] = json.loads(result["data_json"])
        except Exception:
            result["data"] = {}
        return result
    return None

def delete_recommendation(rec_id: int, user_id: Optional[int] = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM recommendations WHERE id = ? AND user_id = ?", (rec_id, user_id))
    else:
        cursor.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
