import sqlite3
from datetime import datetime, timezone

from flask import g

DATABASE = "file::memory:?cache=shared"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, uri=True)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            completed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)
    db.commit()


def _fetch_row(todo_id):
    db = get_db()
    return db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()


def row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


def get_all_todos(completed=None):
    db = get_db()
    if completed is not None:
        rows = db.execute(
            "SELECT * FROM todos WHERE completed = ?", (int(completed),)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM todos").fetchall()
    return [row_to_dict(r) for r in rows]


def get_todo_by_id(todo_id):
    row = _fetch_row(todo_id)
    if row is None:
        return None
    return row_to_dict(row)


def create_todo(title, description=""):
    db = get_db()
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = db.execute(
        "INSERT INTO todos (title, description, created_at) VALUES (?, ?, ?)",
        (title, description, created_at),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "title": title,
        "description": description,
        "completed": False,
        "created_at": created_at,
    }


def update_todo(todo_id, data):
    row = _fetch_row(todo_id)
    if row is None:
        return None
    title = data.get("title", row["title"])
    description = data.get("description", row["description"])
    completed = data.get("completed", row["completed"])
    db = get_db()
    db.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (title, description, completed, todo_id),
    )
    db.commit()
    return {
        "id": todo_id,
        "title": title,
        "description": description,
        "completed": bool(completed),
        "created_at": row["created_at"],
    }


def delete_todo(todo_id):
    db = get_db()
    cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return cursor.rowcount > 0
