import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("queue.db")

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            service_id INTEGER NOT NULL REFERENCES services(id),
            ticket_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        for title in ("Справки / Анықтамалар", "Академические вопросы / Академиялық сұрақтар",
                      "Расписание / Сабақ кестесі", "Другие вопросы / Басқа сұрақтар"):
            db.execute("INSERT OR IGNORE INTO services(title) VALUES (?)", (title,))
