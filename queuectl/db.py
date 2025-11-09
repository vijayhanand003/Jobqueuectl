# queuectl/db.py
import sqlite3
import os
from datetime import datetime

DB_FILE = "queuectl.db"

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Main jobs table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            next_attempt_at TEXT,
            locked_by INTEGER
        )
    ''')

    # DLQ table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dlq (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            attempts INTEGER,
            max_retries INTEGER,
            created_at TEXT,
            updated_at TEXT,
            failed_at TEXT
        )
    ''')

    # Config table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Default config
    cur.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ('max_retries', '3'))
    cur.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ('backoff_base', '2'))

    conn.commit()
    conn.close()

# --- CRUD Functions ---
def get_conn():
    return sqlite3.connect(DB_FILE, timeout=10)

def enqueue_job(job_data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO jobs 
        (id, command, state, attempts, max_retries, created_at, updated_at)
        VALUES (?, ?, 'pending', 0, ?, ?, ?)
    ''', (
        job_data['id'],
        job_data['command'],
        job_data.get('max_retries', 3),
        now_iso(),
        now_iso()
    ))
    conn.commit()
    conn.close()

def get_pending_job(worker_pid):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    now = now_iso()

    try:
        conn.execute("BEGIN IMMEDIATE")
        cur.execute('''
            SELECT * FROM jobs
            WHERE state = 'pending'
              AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            ORDER BY created_at ASC
            LIMIT 1
        ''', (now,))
        job = cur.fetchone()
        if job:
            cur.execute('''
                UPDATE jobs SET state = 'processing', locked_by = ?, updated_at = ?
                WHERE id = ?
            ''', (worker_pid, now_iso(), job['id']))
            conn.commit()
            return dict(job)
    except sqlite3.OperationalError:
        conn.rollback()
    finally:
        conn.close()
    return None

def update_job(job_id, updates):
    conn = get_conn()
    cur = conn.cursor()
    set_parts = [f"{k} = ?" for k in updates]
    values = list(updates.values()) + [now_iso(), job_id]
    sql = f"UPDATE jobs SET {', '.join(set_parts)}, updated_at = ? WHERE id = ?"
    cur.execute(sql, values)
    conn.commit()
    conn.close()

def move_to_dlq(job):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO dlq (id, command, attempts, max_retries, created_at, updated_at, failed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (job['id'], job['command'], job['attempts'], job['max_retries'],
          job['created_at'], now_iso(), now_iso()))
    cur.execute("DELETE FROM jobs WHERE id = ?", (job['id'],))
    conn.commit()
    conn.close()

def get_config(key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_config(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def list_jobs(state=None):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if state:
        cur.execute("SELECT * FROM jobs WHERE state = ?", (state,))
    else:
        cur.execute("SELECT * FROM jobs")
    jobs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jobs

def list_dlq():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM dlq")
    jobs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jobs

def retry_dlq_job(job_id):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM dlq WHERE id = ?", (job_id,))
    job = cur.fetchone()
    if job:
        job_dict = dict(job)
        job_dict['attempts'] = 0
        enqueue_job(job_dict)
        cur.execute("DELETE FROM dlq WHERE id = ?", (job_id,))
        conn.commit()
    conn.close()
    return job_dict if job else None