import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                name TEXT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'Present',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.conn.commit()

    # ── Students ──

    def get_next_serial(self):
        c = self.conn.cursor()
        c.execute("SELECT COALESCE(MAX(serial), 0) + 1 FROM students")
        return c.fetchone()[0]

    def add_student(self, serial, student_id, name):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO students (serial, student_id, name) VALUES (?, ?, ?)",
            (serial, student_id, name),
        )
        self.conn.commit()
        return c.lastrowid

    def get_student_by_serial(self, serial):
        c = self.conn.cursor()
        c.execute("SELECT * FROM students WHERE serial = ?", (serial,))
        return c.fetchone()

    def get_all_students(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM students ORDER BY serial")
        return c.fetchall()

    def get_student_count(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM students")
        return c.fetchone()[0]

    # ── Attendance ──

    def add_attendance(self, student_id, name, date, time, status="Present"):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO attendance (student_id, name, date, time, status) VALUES (?, ?, ?, ?, ?)",
            (student_id, name, date, time, status),
        )
        self.conn.commit()
        return c.lastrowid

    def get_attendance_by_date(self, date):
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM attendance WHERE date = ? ORDER BY time DESC",
            (date,),
        )
        return c.fetchall()

    def get_all_attendance(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM attendance ORDER BY date DESC, time DESC")
        return c.fetchall()

    def get_today_count(self):
        c = self.conn.cursor()
        c.execute(
            "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = date('now','localtime')"
        )
        result = c.fetchone()[0]
        return result or 0

    def clear_attendance(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM attendance")
        self.conn.commit()

    # ── Settings ──

    def get_setting(self, key):
        c = self.conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        c = self.conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    # ── Cleanup ──

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
