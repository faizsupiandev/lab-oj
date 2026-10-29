import os
import asyncio
import csv
import io
import sqlite3
import hashlib
import json
import time
import hmac
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

MYT = timezone(timedelta(hours=8))  # Malaysia Time (UTC+8)
def now_myt() -> datetime:
    return datetime.now(MYT)
def now_myt_str() -> str:
    return now_myt().strftime('%Y-%m-%dT%H:%M')
def now_myt_iso() -> str:
    return now_myt().isoformat()

# Semaphore to limit concurrent Piston submissions (avoid overloading)
PISTON_SEMAPHORE = None  # initialized at startup

def call_piston(payload: bytes, timeout: int = 30, max_retries: int = 2) -> dict:
    """Call Piston API with retry on transient errors."""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            req_obj = urllib.request.Request(
                f"{PISTON_URL}/api/v2/execute",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req_obj, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))  # backoff
                last_err = e
                continue
            raise
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                last_err = e
                continue
            raise
    raise last_err
from typing import Optional

import pymysql
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# --- Config ---
DB_PATH      = os.getenv("DB_PATH", "/data/lab.db")
SECRET_KEY   = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
PISTON_URL   = os.getenv("PISTON_URL", "http://piston-api:2000")
MYSQL_HOST   = os.getenv("MYSQL_HOST", "mysql-main")
MYSQL_USER   = os.getenv("MYSQL_USER", "root")
MYSQL_PASS   = os.getenv("MYSQL_PASS", "faiz")
MYSQL_DB     = os.getenv("MYSQL_DB", "studmon")
COOKIE_NAME  = "laboj_session"
ADMIN_MATRIC = "FAIZ"
ADMIN_PASS   = "Ad@lah77"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def format_myt(dt_str):
    if not dt_str: return '-'
    try:
        dt = datetime.fromisoformat(str(dt_str))
        return dt.strftime('%-d %b %Y, %I:%M %p')
    except:
        return str(dt_str)
templates.env.filters['myt'] = format_myt
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass

# --- DB ---
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)  # wait up to 30s for lock
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")  # 30s busy timeout
    conn.execute("PRAGMA synchronous=NORMAL")   # faster writes, safe with WAL
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            input_format TEXT DEFAULT '',
            output_format TEXT DEFAULT '',
            sample_input TEXT DEFAULT '',
            sample_output TEXT DEFAULT '',
            hidden_tests TEXT DEFAULT '[]',
            difficulty TEXT DEFAULT 'Mudah',
            time_limit_sec REAL DEFAULT 5.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL,
            stdout TEXT DEFAULT '',
            stderr TEXT DEFAULT '',
            runtime_ms INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        );
        CREATE TABLE IF NOT EXISTS question_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            course_code TEXT NOT NULL,
            chapter INTEGER DEFAULT 1,
            difficulty TEXT DEFAULT 'Mudah',
            default_template TEXT DEFAULT '',
            input_format TEXT DEFAULT '',
            output_format TEXT DEFAULT '',
            sample_input TEXT DEFAULT '',
            sample_output TEXT DEFAULT '',
            hidden_tests TEXT DEFAULT '[]',
            time_limit_sec REAL DEFAULT 5.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS lab_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            course_code TEXT NOT NULL,
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS session_questions (
            session_id INTEGER REFERENCES lab_sessions(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES question_bank(id) ON DELETE CASCADE,
            question_order INTEGER DEFAULT 1,
            PRIMARY KEY (session_id, question_id)
        );
        CREATE TABLE IF NOT EXISTS student_session_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT NOT NULL,
            session_id INTEGER REFERENCES lab_sessions(id),
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            submitted_at TEXT NULL,
            status TEXT DEFAULT 'IN_PROGRESS'
        );
        CREATE TABLE IF NOT EXISTS session_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER REFERENCES student_session_attempts(id),
            matric_no TEXT NOT NULL,
            session_id INTEGER REFERENCES lab_sessions(id),
            question_id INTEGER REFERENCES question_bank(id),
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL,
            stdout TEXT DEFAULT '',
            stderr TEXT DEFAULT '',
            runtime_ms INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS session_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            final_score REAL DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            time_seconds INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(matric_no, session_id)
        );
    """)

    # Seed / migrate admin user
    ph = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (matric_no, full_name, phone_hash, is_admin) VALUES (?,?,?,1)",
            (ADMIN_MATRIC, "Pensyarah", ph)
        )
        # Migrate old ADMIN → FAIZ if present
        conn.execute("UPDATE users SET matric_no=? WHERE matric_no='ADMIN'", (ADMIN_MATRIC,))
        conn.commit()
    except Exception:
        pass

    # Seed standalone problems
    try:
        conn.execute("""INSERT OR IGNORE INTO problems
            (title, slug, description, input_format, output_format, sample_input, sample_output, hidden_tests, difficulty, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            "Hello World", "hello-world",
            "Tulis program yang mencetak teks `Hello World` ke output standard.",
            "No input.", "Print one line: `Hello World`",
            "", "Hello World",
            json.dumps([{"input": "", "expected_output": "Hello World"}]),
            "Mudah", 5.0
        ))
        conn.execute("""INSERT OR IGNORE INTO problems
            (title, slug, description, input_format, output_format, sample_input, sample_output, hidden_tests, difficulty, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            "Tambah Dua Nombor", "tambah-dua-nombor",
            "Diberi dua nombor integer `a` dan `b`, cetak hasil penambahan mereka.",
            "Satu baris mengandungi dua integer `a` dan `b` dipisahkan dengan ruang.",
            "Cetak satu integer: hasil `a + b`.",
            "3 5", "8",
            json.dumps([{"input": "1 2", "expected_output": "3"}, {"input": "10 20", "expected_output": "30"}]),
            "Mudah", 5.0
        ))
        conn.commit()
    except Exception:
        pass

    # Seed question_bank with 2 BITP1113 samples
    try:
        conn.execute("""INSERT OR IGNORE INTO question_bank
            (id, title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            1, "Hello World (C++)",
            "Tulis program C++ yang mencetak teks Hello World ke output standard.",
            "BITP1113", 1, "Mudah",
            "#include <iostream>\nusing namespace std;\nint main() {\n    // tulis kod anda di sini\n    return 0;\n}",
            "No input.",
            "Print one line: Hello World",
            "", "Hello World",
            json.dumps([{"input": "", "expected_output": "Hello World"}]),
            5.0
        ))
        conn.execute("""INSERT OR IGNORE INTO question_bank
            (id, title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            2, "Jumlah Dua Integer",
            "Diberi dua integer a dan b, cetak hasil penambahan a + b.",
            "BITP1113", 1, "Mudah",
            "#include <iostream>\nusing namespace std;\nint main() {\n    int a, b;\n    cin >> a >> b;\n    // cetak jawapan di sini\n    return 0;\n}",
            "Satu baris: dua integer a dan b dipisah ruang.",
            "Cetak satu integer: a + b.",
            "3 5", "8",
            json.dumps([
                {"input": "1 2", "expected_output": "3"},
                {"input": "10 20", "expected_output": "30"},
                {"input": "0 0", "expected_output": "0"}
            ]),
            5.0
        ))
        conn.commit()
    except Exception:
        pass

    conn.close()


# --- Cookie auth ---
def sign_value(val: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), val.encode(), hashlib.sha256).hexdigest()
    return f"{val}.{sig}"


def unsign_value(signed: str) -> Optional[str]:
    try:
        val, sig = signed.rsplit(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), val.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return val
    except Exception:
        pass
    return None


def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def get_current_user(request: Request) -> Optional[dict]:
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    matric = unsign_value(cookie)
    if not matric:
        return None
    # Hardcoded admin shortcut
    if matric == ADMIN_MATRIC:
        return {"id": -1, "matric_no": ADMIN_MATRIC, "full_name": "Lecturer", "is_admin": 1}
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE matric_no=?", (matric,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# --- Admin context helper ---
def _admin_ctx(conn) -> dict:
    """Lightweight context: sessions (with sq_list/q_count) + questions for dropdowns."""
    sessions_raw = conn.execute("SELECT * FROM lab_sessions ORDER BY id DESC").fetchall()
    sessions = []
    for s in sessions_raw:
        s = dict(s)
        q_count = conn.execute(
            "SELECT COUNT(*) FROM session_questions WHERE session_id=?", (s["id"],)
        ).fetchone()[0]
        s["q_count"] = q_count
        sq = conn.execute("""
            SELECT qb.id, qb.title, qb.course_code, sq.question_order
            FROM question_bank qb
            JOIN session_questions sq ON sq.question_id=qb.id
            WHERE sq.session_id=?
            ORDER BY sq.question_order
        """, (s["id"],)).fetchall()
        s["sq_list"] = [dict(r) for r in sq]
        sessions.append(s)
    # Lightweight questions list — only what's needed for session add-question dropdowns
    questions_raw = conn.execute(
        "SELECT id, title, course_code, chapter FROM question_bank ORDER BY course_code, chapter, id"
    ).fetchall()
    questions = [dict(q) for q in questions_raw]
    return {"sessions": sessions, "questions": questions}


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        if user["is_admin"]:
            return RedirectResponse("/admin?msg=done", status_code=302)
        return RedirectResponse("/sessions", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/", response_class=HTMLResponse)
async def login_post(request: Request, matric: str = Form(...), phone: str = Form(...)):
    matric = matric.strip().upper()

    # Admin hardcoded check
    if matric == ADMIN_MATRIC and phone == ADMIN_PASS:
        resp = RedirectResponse("/admin", status_code=302)
        resp.set_cookie(COOKIE_NAME, sign_value(ADMIN_MATRIC), httponly=True, samesite="lax", max_age=86400 * 7)
        return resp

    # Local SQLite bypass — for test/excused users (is_admin=1 in local DB)
    local_db = get_db()
    local_user = local_db.execute(
        "SELECT * FROM users WHERE matric_no=? AND is_admin=1",
        (matric,)
    ).fetchone()
    local_db.close()
    if local_user:
        ph = hashlib.sha256(phone.encode()).hexdigest()
        stored_ph = local_user["phone_hash"]
        if ph == stored_ph or stored_ph == "studmon_auth" or stored_ph == ph:
            resp = RedirectResponse("/sessions", status_code=302)
            resp.set_cookie(COOKIE_NAME, sign_value(matric), httponly=True, samesite="lax", max_age=86400 * 7)
            return resp

    # studmon MySQL auth
    try:
        mysql_conn = pymysql.connect(
            host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASS,
            database=MYSQL_DB, connect_timeout=5, charset="utf8mb4"
        )
        with mysql_conn.cursor() as cur:
            cur.execute("""
                SELECT s.full_name FROM students s
                JOIN student_groups sg ON sg.id = s.group_id
                JOIN group_courses gc ON gc.group_id = sg.id
                JOIN courses c ON c.id = gc.course_id
                WHERE s.matric_no = %s AND s.phone = %s
                  AND c.course_code IN ('BITP1113','DFDS1513')
                LIMIT 1
            """, (matric, phone))
            row = cur.fetchone()
        mysql_conn.close()
    except Exception as e:
        return templates.TemplateResponse(request, "login.html", {
            "error": f"Database connection error: {e}"
        })

    if row:
        full_name = row[0]
        # Upsert student in local SQLite for FK references
        db = get_db()
        db.execute(
            "INSERT OR IGNORE INTO users (matric_no, full_name, phone_hash, is_admin) VALUES (?,?,?,0)",
            (matric, full_name, "studmon_auth")
        )
        db.execute("UPDATE users SET full_name=? WHERE matric_no=?", (full_name, matric))
        db.commit()
        db.close()
        resp = RedirectResponse("/sessions", status_code=302)
        resp.set_cookie(COOKIE_NAME, sign_value(matric), httponly=True, samesite="lax", max_age=86400 * 7)
        return resp

    return templates.TemplateResponse(request, "login.html", {
        "error": "Access restricted: No active enrollment in authorized programming courses."
    })


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


# --- Sessions (student landing) ---

@app.get("/sessions", response_class=HTMLResponse)
async def sessions_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    if user["is_admin"]:
        return RedirectResponse("/admin?msg=done", status_code=302)

    conn = get_db()
    sessions_raw = conn.execute(
        "SELECT * FROM lab_sessions WHERE is_active=1 ORDER BY window_start DESC"
    ).fetchall()

    now = now_myt_str()
    session_data = []
    for s in sessions_raw:
        s = dict(s)
        attempt = conn.execute(
            "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=? ORDER BY id DESC LIMIT 1",
            (s["id"], user["matric_no"])
        ).fetchone()
        window_open = s["window_start"] <= now <= s["window_end"]
        s["window_open"] = window_open
        s["student_status"] = attempt["status"] if attempt else "NOT_STARTED"
        s["attempt"] = dict(attempt) if attempt else None
        session_data.append(s)

    conn.close()
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "sessions.html", {
        "user": user,
        "sessions": session_data,
        "error": error
    })


@app.post("/sessions/{sid}/start", response_class=HTMLResponse)
async def start_session(request: Request, sid: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    conn = get_db()
    session = conn.execute(
        "SELECT * FROM lab_sessions WHERE id=? AND is_active=1", (sid,)
    ).fetchone()
    if not session:
        conn.close()
        raise HTTPException(404, "Session not found")

    session = dict(session)
    now = now_myt_str()

    if now < session["window_start"] or now > session["window_end"]:
        conn.close()
        return RedirectResponse("/sessions?error=window_closed", status_code=302)

    existing = conn.execute(
        "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=?",
        (sid, user["matric_no"])
    ).fetchone()

    if existing:
        conn.close()
        return RedirectResponse(f"/sessions/{sid}/attempt", status_code=302)

    now_full = now_myt_iso()
    conn.execute(
        "INSERT INTO student_session_attempts (matric_no, session_id, started_at, status) VALUES (?,?,?,?)",
        (user["matric_no"], sid, now_full, "IN_PROGRESS")
    )
    conn.commit()
    conn.close()
    return RedirectResponse(f"/sessions/{sid}/attempt", status_code=302)


@app.get("/sessions/{sid}/attempt", response_class=HTMLResponse)
async def attempt_workspace(request: Request, sid: int, q: int = 1):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    conn = get_db()
    attempt = conn.execute(
        "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=? ORDER BY id DESC LIMIT 1",
        (sid, user["matric_no"])
    ).fetchone()

    if not attempt:
        conn.close()
        return RedirectResponse("/sessions", status_code=302)

    attempt = dict(attempt)
    session = conn.execute("SELECT * FROM lab_sessions WHERE id=?", (sid,)).fetchone()
    if not session:
        conn.close()
        raise HTTPException(404)
    session = dict(session)

    questions_raw = conn.execute("""
        SELECT qb.*, sq.question_order
        FROM question_bank qb
        JOIN session_questions sq ON sq.question_id = qb.id
        WHERE sq.session_id = ?
        ORDER BY sq.question_order
    """, (sid,)).fetchall()
    questions = [dict(r) for r in questions_raw]

    # Compute remaining time
    remaining = 0
    try:
        started = datetime.fromisoformat(attempt["started_at"])
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        now_utc = now_myt()
        elapsed = (now_utc - started).total_seconds()
        remaining = max(0, int(session["duration_minutes"] * 60 - elapsed))
    except Exception:
        pass

    if attempt["status"] == "SUBMITTED":
        remaining = 0

    q_idx = max(0, min(q - 1, len(questions) - 1)) if questions else 0
    current_q = questions[q_idx] if questions else None

    # Last submission per question for this attempt
    submissions = {}
    for qr in questions:
        sub = conn.execute("""
            SELECT * FROM session_submissions
            WHERE attempt_id=? AND question_id=?
            ORDER BY id DESC LIMIT 1
        """, (attempt["id"], qr["id"])).fetchone()
        if sub:
            submissions[qr["id"]] = dict(sub)

    conn.close()

    questions_json = json.dumps(questions)
    submissions_json = json.dumps({str(k): v for k, v in submissions.items()})

    return templates.TemplateResponse(request, "session_attempt.html", {
        "user": user,
        "session": session,
        "attempt": attempt,
        "questions": questions,
        "questions_json": questions_json,
        "submissions": submissions,
        "submissions_json": submissions_json,
        "current_q": current_q,
        "q_idx": q_idx,
        "remaining_seconds": remaining,
        "sid": sid,
    })


@app.get("/sessions/{sid}/time-remaining")
async def get_time_remaining(request: Request, sid: int):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"remaining_seconds": 0})

    conn = get_db()
    attempt = conn.execute(
        "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=? ORDER BY id DESC LIMIT 1",
        (sid, user["matric_no"])
    ).fetchone()
    session = conn.execute("SELECT * FROM lab_sessions WHERE id=?", (sid,)).fetchone()
    conn.close()

    if not attempt or not session or attempt["status"] == "SUBMITTED":
        return JSONResponse({"remaining_seconds": 0})

    try:
        started = datetime.fromisoformat(attempt["started_at"])
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        now_utc = now_myt()
        elapsed = (now_utc - started).total_seconds()
        remaining = max(0, int(session["duration_minutes"] * 60 - elapsed))
    except Exception:
        remaining = 0

    return JSONResponse({"remaining_seconds": remaining})


@app.post("/sessions/{sid}/submit")
async def submit_session_code(
    request: Request, sid: int,
    question_id: int = Form(...),
    code: str = Form(...),
    language: str = Form("c++")
):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "not logged in"}, status_code=401)

    conn = get_db()
    attempt = conn.execute(
        "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=? AND status='IN_PROGRESS' ORDER BY id DESC LIMIT 1",
        (sid, user["matric_no"])
    ).fetchone()
    if not attempt:
        conn.close()
        return JSONResponse({"error": "No active attempt"}, status_code=403)

    question = conn.execute("SELECT * FROM question_bank WHERE id=?", (question_id,)).fetchone()
    if not question:
        conn.close()
        return JSONResponse({"error": "Question not found"}, status_code=404)

    attempt = dict(attempt)
    question = dict(question)

    hidden_tests = json.loads(question.get("hidden_tests") or "[]")
    if not hidden_tests:
        hidden_tests = [{"input": question.get("sample_input", ""), "expected_output": question.get("sample_output", "")}]

    lang_map = {"python": ("python", "3.10.0"), "c++": ("c++", "10.2.0"), "cpp": ("c++", "10.2.0")}
    piston_lang, piston_ver = lang_map.get(language, ("c++", "10.2.0"))

    overall_status = "Accepted"
    passed = 0
    total = len(hidden_tests)
    last_stdout = ""
    last_stderr = ""
    total_ms = 0

    for test in hidden_tests:
        stdin_data = test.get("input", "")
        expected = (test.get("expected_output") or test.get("expected", "")).strip()
        fname = "main.py" if piston_lang == "python" else "main.cpp"
        payload = json.dumps({
            "language": piston_lang,
            "version": piston_ver,
            "files": [{"name": fname, "content": code}],
            "stdin": stdin_data,
            "args": []
        }).encode()

        t0 = time.time()
        try:
            piston_result = call_piston(payload, timeout=30)
        except Exception as e:
            overall_status = "Runtime Error"
            last_stderr = f"Execution service unavailable. Please retry. ({e})"
            break

        elapsed_ms = int((time.time() - t0) * 1000)
        total_ms += elapsed_ms

        run = piston_result.get("run", {})
        stdout = run.get("stdout", "").strip()
        stderr = run.get("stderr", "")
        exit_code = run.get("code", 0)
        last_stdout = stdout
        last_stderr = stderr

        if exit_code != 0:
            overall_status = "Runtime Error"
            break
        elif stdout == expected:
            passed += 1
        else:
            if overall_status == "Accepted":
                overall_status = "Wrong Answer"

    conn.execute("""
        INSERT INTO session_submissions
        (attempt_id, matric_no, session_id, question_id, code, language, status, stdout, stderr, runtime_ms, passed, total)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (attempt["id"], user["matric_no"], sid, question_id, code, language,
          overall_status, last_stdout, last_stderr, total_ms, passed, total))
    conn.commit()

    # Upsert session_scores
    try:
        matric_no = user["matric_no"]
        session_info = conn.execute("SELECT course_code FROM lab_sessions WHERE id=?", (sid,)).fetchone()
        course_code = session_info["course_code"] if session_info else "UNKNOWN"

        best_scores = conn.execute("""
            SELECT question_id, MAX(CAST(passed AS REAL)/CASE WHEN total=0 THEN 1 ELSE total END * 100) as best
            FROM session_submissions
            WHERE matric_no=? AND session_id=?
            GROUP BY question_id
        """, (matric_no, sid)).fetchall()
        final_score = sum(r["best"] for r in best_scores)

        attempt_row = conn.execute(
            "SELECT * FROM student_session_attempts WHERE session_id=? AND matric_no=? ORDER BY id DESC LIMIT 1",
            (sid, matric_no)
        ).fetchone()
        time_secs = int((now_myt().replace(tzinfo=None) - datetime.fromisoformat(attempt_row["started_at"]).replace(tzinfo=None)).total_seconds()) if attempt_row else 0
        total_attempts_count = conn.execute(
            "SELECT COUNT(*) FROM session_submissions WHERE matric_no=? AND session_id=?",
            (matric_no, sid)
        ).fetchone()[0]

        conn.execute("""
            INSERT INTO session_scores (matric_no, session_id, course_code, final_score, total_attempts, time_seconds, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(matric_no, session_id) DO UPDATE SET
                final_score=excluded.final_score,
                total_attempts=excluded.total_attempts,
                time_seconds=excluded.time_seconds,
                last_updated=excluded.last_updated
        """, (matric_no, sid, course_code, final_score, total_attempts_count, time_secs))
        conn.commit()
    except Exception:
        pass

    conn.close()

    return JSONResponse({
        "status": overall_status,
        "passed": passed,
        "total": total,
        "stdout": last_stdout,
        "stderr": last_stderr,
        "ms": total_ms
    })


@app.post("/sessions/{sid}/finalize")
async def finalize_session(request: Request, sid: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("""
        UPDATE student_session_attempts
        SET status='SUBMITTED', submitted_at=datetime('now')
        WHERE session_id=? AND matric_no=? AND status='IN_PROGRESS'
    """, (sid, user["matric_no"]))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/sessions/{sid}/attempt", status_code=302)


# --- Standalone Problems (admin/testing) ---

@app.get("/problems", response_class=HTMLResponse)
async def problem_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    if not user["is_admin"]:
        return RedirectResponse("/sessions", status_code=302)
    conn = get_db()
    problems = conn.execute("SELECT * FROM problems WHERE is_active=1 ORDER BY id").fetchall()
    solved_ids = set()
    conn.close()
    return templates.TemplateResponse(request, "problems.html", {
        "user": user, "problems": [dict(p) for p in problems], "solved_ids": solved_ids
    })


@app.get("/problems/{problem_id}", response_class=HTMLResponse)
async def problem_detail(request: Request, problem_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    problem = conn.execute("SELECT * FROM problems WHERE id=? AND is_active=1", (problem_id,)).fetchone()
    if not problem:
        conn.close()
        raise HTTPException(404, "Problem not found")
    last_sub = None
    if user["id"] and user["id"] > 0:
        last_sub = conn.execute(
            "SELECT * FROM submissions WHERE user_id=? AND problem_id=? ORDER BY id DESC LIMIT 1",
            (user["id"], problem_id)
        ).fetchone()
    conn.close()
    return templates.TemplateResponse(request, "problem_detail.html", {
        "user": user,
        "problem": dict(problem),
        "last_sub": dict(last_sub) if last_sub else None,
        "result": None
    })


@app.post("/problems/{problem_id}/submit", response_class=HTMLResponse)
async def submit_code(request: Request, problem_id: int,
                      code: str = Form(...), language: str = Form("c++")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    if user["id"] == -1:
        raise HTTPException(403, "Admin cannot submit")
    conn = get_db()
    problem = conn.execute("SELECT * FROM problems WHERE id=? AND is_active=1", (problem_id,)).fetchone()
    if not problem:
        conn.close()
        raise HTTPException(404)
    problem = dict(problem)

    hidden_tests = json.loads(problem.get("hidden_tests") or "[]")
    if not hidden_tests:
        hidden_tests = [{"input": problem.get("sample_input", ""), "expected_output": problem.get("sample_output", "")}]

    lang_map = {"python": ("python", "3.10.0"), "c++": ("c++", "10.2.0"), "cpp": ("c++", "10.2.0")}
    piston_lang, piston_ver = lang_map.get(language, ("c++", "10.2.0"))

    overall_status = "Accepted"
    last_stdout = ""
    last_stderr = ""
    total_ms = 0

    for test in hidden_tests:
        stdin_data = test.get("input", "")
        expected = (test.get("expected_output") or test.get("expected", "")).strip()
        fname = "main.py" if piston_lang == "python" else "main.cpp"
        payload = json.dumps({
            "language": piston_lang,
            "version": piston_ver,
            "files": [{"name": fname, "content": code}],
            "stdin": stdin_data,
            "args": []
        }).encode()

        t0 = time.time()
        try:
            result = call_piston(payload, timeout=30)
        except Exception as e:
            overall_status = "Runtime Error"
            last_stderr = f"Execution service unavailable. Please retry. ({e})"
            break

        elapsed = int((time.time() - t0) * 1000)
        total_ms += elapsed
        run = result.get("run", {})
        stdout = run.get("stdout", "").strip()
        stderr = run.get("stderr", "")
        exit_code = run.get("code", 0)
        last_stdout = stdout
        last_stderr = stderr

        if elapsed > problem["time_limit_sec"] * 1000:
            overall_status = "Time Limit Exceeded"
            break
        if exit_code != 0:
            overall_status = "Runtime Error"
            break
        if stdout != expected:
            overall_status = "Wrong Answer"

    conn.execute(
        "INSERT INTO submissions (user_id, problem_id, code, language, status, stdout, stderr, runtime_ms) VALUES (?,?,?,?,?,?,?,?)",
        (user["id"], problem_id, code, language, overall_status, last_stdout, last_stderr, total_ms)
    )
    conn.commit()
    last_sub = conn.execute(
        "SELECT * FROM submissions WHERE user_id=? AND problem_id=? ORDER BY id DESC LIMIT 1",
        (user["id"], problem_id)
    ).fetchone()
    conn.close()

    return templates.TemplateResponse(request, "problem_detail.html", {
        "user": user,
        "problem": problem,
        "last_sub": dict(last_sub) if last_sub else None,
        "result": {"status": overall_status, "stdout": last_stdout, "stderr": last_stderr, "ms": total_ms}
    })


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    conn = get_db()
    matric_no = user["matric_no"]

    # Get selected session from query param
    selected_sid = request.query_params.get("session_id")
    selected_course = request.query_params.get("course_code")

    if user["is_admin"]:
        # Admin: see all sessions, filter by course if selected
        if selected_course:
            available_sessions = conn.execute(
                "SELECT * FROM lab_sessions WHERE course_code=? ORDER BY window_start DESC",
                (selected_course,)
            ).fetchall()
        else:
            available_sessions = conn.execute(
                "SELECT * FROM lab_sessions ORDER BY window_start DESC"
            ).fetchall()
        all_courses = [r[0] for r in conn.execute(
            "SELECT DISTINCT course_code FROM lab_sessions ORDER BY course_code"
        ).fetchall()]
    else:
        # Student: sessions they have participated in
        participated = conn.execute("""
            SELECT DISTINCT ls.* FROM lab_sessions ls
            JOIN student_session_attempts ssa ON ssa.session_id=ls.id
            WHERE ssa.matric_no=?
            ORDER BY ls.window_start DESC
        """, (matric_no,)).fetchall()
        available_sessions = participated if participated else []
        all_courses = None

    available_sessions = [dict(s) for s in available_sessions]

    # Pick default session
    current_session = None
    if selected_sid:
        try:
            sid_int = int(selected_sid)
            for s in available_sessions:
                if s["id"] == sid_int:
                    current_session = s
                    break
        except ValueError:
            pass
    if not current_session and available_sessions:
        current_session = available_sessions[0]

    entries = []
    max_score = 0
    if current_session:
        sid_val = current_session["id"]
        cc_val = current_session["course_code"]

        # Count questions in session to compute max score
        q_count = conn.execute(
            "SELECT COUNT(*) FROM session_questions WHERE session_id=?", (sid_val,)
        ).fetchone()[0]
        max_score = q_count * 100

        rows = conn.execute("""
            SELECT
                DENSE_RANK() OVER (ORDER BY ss.final_score DESC, ss.time_seconds ASC, ss.total_attempts ASC) as rank,
                ss.matric_no,
                ss.final_score,
                ss.time_seconds,
                ss.total_attempts
            FROM session_scores ss
            WHERE ss.session_id = ? AND ss.course_code = ?
            ORDER BY ss.final_score DESC, ss.time_seconds ASC, ss.total_attempts ASC
        """, (sid_val, cc_val)).fetchall()

        for r in rows:
            rd = dict(r)
            secs = rd["time_seconds"] or 0
            rd["time_display"] = f"{secs // 60:02d}:{secs % 60:02d}"
            rd["score_display"] = f"{int(rd['final_score'])}/{max_score}"
            entries.append(rd)

    conn.close()
    return templates.TemplateResponse(request, "leaderboard.html", {
        "user": user,
        "entries": entries,
        "available_sessions": available_sessions,
        "current_session": current_session,
        "all_courses": all_courses,
        "selected_course": selected_course,
        "max_score": max_score,
    })


# --- Admin Routes ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, msg: str = None):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    ctx = _admin_ctx(conn)
    conn.close()
    toast_map = {
        "done": "✅ Done!",
        "saved": "✅ Changes saved!",
        "added": "✅ Added successfully!",
        "deleted": "🗑️ Deleted.",
        "toggled": "✅ Status updated.",
    }
    ctx["toast"] = toast_map.get(msg, None)
    return templates.TemplateResponse(request, "admin.html", {
        "user": user, **ctx, "msg": None, "error": None
    })


@app.post("/admin/problems/add", response_class=HTMLResponse)
async def admin_add_problem(
    request: Request,
    title: str = Form(...), description: str = Form(...),
    input_format: str = Form(""), output_format: str = Form(""),
    sample_input: str = Form(""), sample_output: str = Form(""),
    hidden_tests: str = Form("[]"), difficulty: str = Form("Mudah"),
    time_limit_sec: float = Form(5.0)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    slug = title.lower().replace(" ", "-").replace("/", "-")[:60]
    try:
        json.loads(hidden_tests)
    except Exception:
        hidden_tests = "[]"
    conn = get_db()
    try:
        conn.execute("""INSERT INTO problems
            (title, slug, description, input_format, output_format, sample_input, sample_output, hidden_tests, difficulty, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, slug, description, input_format, output_format, sample_input, sample_output, hidden_tests, difficulty, time_limit_sec))
        conn.commit()
        msg, error = f"Question '{title}' added successfully.", None
    except Exception as e:
        msg, error = None, str(e)
    ctx = _admin_ctx(conn)
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {"user": user, **ctx, "msg": msg, "error": error})


@app.post("/admin/students/add", response_class=HTMLResponse)
async def admin_add_student(
    request: Request,
    matric: str = Form(...), full_name: str = Form(...), phone: str = Form(...)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    matric = matric.strip().upper()
    ph = hash_phone(phone)
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (matric_no, full_name, phone_hash) VALUES (?,?,?)", (matric, full_name, ph))
        conn.commit()
        msg, error = f"Student '{matric}' added successfully.", None
    except Exception as e:
        msg, error = None, str(e)
    ctx = _admin_ctx(conn)
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {"user": user, **ctx, "msg": msg, "error": error})


@app.post("/admin/problems/{pid}/toggle")
async def toggle_problem(request: Request, pid: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("UPDATE problems SET is_active = 1-is_active WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin?msg=done", status_code=302)


# --- Admin: Question Bank ---

@app.post("/admin/questions/add", response_class=HTMLResponse)
async def admin_add_question(
    request: Request,
    title: str = Form(...), description: str = Form(...),
    course_code: str = Form("BITP1113"), chapter: int = Form(1),
    difficulty: str = Form("Mudah"), default_template: str = Form(""),
    input_format: str = Form(""), output_format: str = Form(""),
    sample_input: str = Form(""), sample_output: str = Form(""),
    hidden_tests: str = Form("[]"), time_limit_sec: float = Form(5.0)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    try:
        json.loads(hidden_tests)
    except Exception:
        hidden_tests = "[]"
    conn = get_db()
    try:
        conn.execute("""INSERT INTO question_bank
            (title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests, time_limit_sec))
        conn.commit()
        msg, error = f"Question '{title}' successfully added to question bank.", None
    except Exception as e:
        msg, error = None, str(e)
    ctx = _admin_ctx(conn)
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {"user": user, **ctx, "msg": msg, "error": error})


@app.get("/admin/questions/{qid}/edit", response_class=HTMLResponse)
async def admin_edit_question_form(request: Request, qid: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    q = conn.execute("SELECT * FROM question_bank WHERE id=?", (qid,)).fetchone()
    conn.close()
    if not q:
        raise HTTPException(404, "Question not found")
    ctx = {"user": user, "q": dict(q), "msg": None, "error": None}
    return templates.TemplateResponse(request, "question_edit.html", ctx)


@app.post("/admin/questions/{qid}/edit", response_class=HTMLResponse)
async def admin_edit_question_save(
    request: Request, qid: int,
    title: str = Form(...), description: str = Form(...),
    course_code: str = Form("BITP1113"), chapter: int = Form(1),
    difficulty: str = Form("Mudah"), default_template: str = Form(""),
    input_format: str = Form(""), output_format: str = Form(""),
    sample_input: str = Form(""), sample_output: str = Form(""),
    hidden_tests: str = Form("[]"), time_limit_sec: float = Form(5.0)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    try:
        json.loads(hidden_tests)
    except Exception:
        hidden_tests = "[]"
    conn = get_db()
    try:
        conn.execute("""UPDATE question_bank SET
            title=?, description=?, course_code=?, chapter=?, difficulty=?,
            default_template=?, input_format=?, output_format=?,
            sample_input=?, sample_output=?, hidden_tests=?, time_limit_sec=?
            WHERE id=?""",
            (title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests,
             time_limit_sec, qid))
        conn.commit()
        conn.close()
        return RedirectResponse("/admin#tab-questions", status_code=302)
    except Exception as e:
        conn.close()
        q_row = {"id": qid, "title": title, "description": description, "course_code": course_code,
                 "chapter": chapter, "difficulty": difficulty, "default_template": default_template,
                 "input_format": input_format, "output_format": output_format,
                 "sample_input": sample_input, "sample_output": sample_output,
                 "hidden_tests": hidden_tests, "time_limit_sec": time_limit_sec}
        return templates.TemplateResponse(request, "question_edit.html", {
            "user": user, "q": q_row, "msg": None, "error": str(e)
        })



@app.post("/admin/questions/{qid}/delete")
async def admin_delete_question(request: Request, qid: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("DELETE FROM question_bank WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin#tab-questions", status_code=302)


# --- Admin: Lab Sessions ---

@app.post("/admin/sessions/add", response_class=HTMLResponse)
async def admin_add_session(
    request: Request,
    title: str = Form(...), course_code: str = Form("BITP1113"),
    window_start: str = Form(...), window_end: str = Form(...),
    duration_minutes: int = Form(60)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    try:
        conn.execute("""INSERT INTO lab_sessions
            (title, course_code, window_start, window_end, duration_minutes, is_active, created_by)
            VALUES (?,?,?,?,?,1,?)""",
            (title, course_code, window_start, window_end, duration_minutes, ADMIN_MATRIC))
        conn.commit()
        msg, error = f"Session '{title}' created successfully.", None
    except Exception as e:
        msg, error = None, str(e)
    ctx = _admin_ctx(conn)
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {"user": user, **ctx, "msg": msg, "error": error})


@app.post("/admin/sessions/{sid}/add-question", response_class=HTMLResponse)
async def admin_session_add_question(request: Request, sid: int, question_id: int = Form(...)):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    try:
        max_order = conn.execute(
            "SELECT COALESCE(MAX(question_order),0) FROM session_questions WHERE session_id=?", (sid,)
        ).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO session_questions (session_id, question_id, question_order) VALUES (?,?,?)",
            (sid, question_id, max_order + 1)
        )
        conn.commit()
        msg, error = "Soalan successfully added to session.", None
    except Exception as e:
        msg, error = None, str(e)
    ctx = _admin_ctx(conn)
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {"user": user, **ctx, "msg": msg, "error": error})


@app.post("/admin/sessions/{sid}/remove-question")
async def admin_session_remove_question(request: Request, sid: int, question_id: int = Form(...)):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("DELETE FROM session_questions WHERE session_id=? AND question_id=?", (sid, question_id))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin?msg=done", status_code=302)


@app.post("/admin/sessions/{sid}/toggle")
async def admin_toggle_session(request: Request, sid: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("UPDATE lab_sessions SET is_active=1-is_active WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin?msg=done", status_code=302)


@app.get("/admin/sessions/{sid}/edit", response_class=HTMLResponse)
async def admin_session_edit_get(request: Request, sid: int, msg: str = None):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    session = conn.execute("SELECT * FROM lab_sessions WHERE id=?", (sid,)).fetchone()
    if not session:
        conn.close()
        return RedirectResponse("/admin?msg=done", status_code=302)
    session = dict(session)
    # Questions assigned to this session
    assigned = conn.execute("""
        SELECT qb.id, qb.title, qb.course_code, qb.chapter, qb.difficulty
        FROM session_questions sq
        JOIN question_bank qb ON sq.question_id = qb.id
        WHERE sq.session_id = ?
        ORDER BY sq.question_order
    """, (sid,)).fetchall()
    assigned = [dict(q) for q in assigned]
    assigned_ids = set(q["id"] for q in assigned)
    # All questions not yet in this session
    all_q_rows = conn.execute(
        "SELECT id, title, course_code, chapter, difficulty, description FROM question_bank ORDER BY course_code, chapter, id"
    ).fetchall()
    all_questions = [dict(q) for q in all_q_rows if q["id"] not in assigned_ids]
    conn.close()
    return templates.TemplateResponse(request, "session_edit.html", {
        "user": user, "session": session,
        "assigned": assigned, "all_questions": all_questions,
        "toast": "✅ Changes saved!" if msg == "saved" else None
    })


@app.post("/admin/sessions/{sid}/edit", response_class=HTMLResponse)
async def admin_session_edit_post(
    request: Request, sid: int,
    title: str = Form(...), course_code: str = Form(...),
    window_start: str = Form(...), window_end: str = Form(...),
    duration_minutes: int = Form(...), is_active: int = Form(0)
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    conn.execute("""
        UPDATE lab_sessions
        SET title=?, course_code=?, window_start=?, window_end=?, duration_minutes=?, is_active=?
        WHERE id=?
    """, (title, course_code, window_start, window_end, duration_minutes, is_active, sid))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/admin/sessions/{sid}/edit?msg=saved", status_code=302)


# ─── Admin Report ──────────────────────────────────────────────────────────────

@app.get("/admin/report", response_class=HTMLResponse)
async def admin_report(request: Request, session_id: int = None):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    sessions = [dict(s) for s in conn.execute(
        "SELECT * FROM lab_sessions ORDER BY created_at DESC"
    ).fetchall()]
    report_data = None
    current_session = None
    sid = session_id or (sessions[0]["id"] if sessions else None)
    if sid:
        current_session = next((s for s in sessions if s["id"] == sid), None)
    if current_session:
        questions = [dict(q) for q in conn.execute("""
            SELECT qb.id, qb.title, qb.chapter, qb.difficulty
            FROM session_questions sq JOIN question_bank qb ON sq.question_id=qb.id
            WHERE sq.session_id=? ORDER BY sq.question_order
        """, (current_session["id"],)).fetchall()]
        students = [dict(s) for s in conn.execute(
            "SELECT DISTINCT matric_no, started_at, status FROM student_session_attempts WHERE session_id=? ORDER BY matric_no",
            (current_session["id"],)
        ).fetchall()]
        matrix = {}
        for st in students:
            matric = st["matric_no"]
            matrix[matric] = {}
            for q in questions:
                best = conn.execute("""
                    SELECT MAX(CAST(passed AS REAL)/CASE WHEN total=0 THEN 1 ELSE total END * 100)
                    FROM session_submissions WHERE matric_no=? AND session_id=? AND question_id=?
                """, (matric, current_session["id"], q["id"])).fetchone()[0]
                matrix[matric][q["id"]] = round(best, 1) if best is not None else None
        q_stats = {}
        for q in questions:
            attempted = conn.execute(
                "SELECT COUNT(DISTINCT matric_no) FROM session_submissions WHERE session_id=? AND question_id=?",
                (current_session["id"], q["id"])
            ).fetchone()[0]
            passed_count = conn.execute("""
                SELECT COUNT(DISTINCT matric_no) FROM (
                    SELECT matric_no FROM session_submissions
                    WHERE session_id=? AND question_id=? AND passed=total AND total>0
                    GROUP BY matric_no
                )
            """, (current_session["id"], q["id"])).fetchone()[0]
            q_stats[str(q["id"])] = {"attempted": attempted, "passed": passed_count}
        total_students = len(students)
        scores = []
        totals = {}  # matric -> total score
        for st in students:
            matric = st["matric_no"]
            t = sum(v for v in matrix[matric].values() if v is not None)
            totals[matric] = round(t, 1)
            scores.append(t)
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        max_possible = len(questions) * 100
        full_marks = sum(1 for s in scores if s >= max_possible) if max_possible else 0
        report_data = {
            "questions": questions, "students": students, "matrix": matrix,
            "q_stats": q_stats, "total_students": total_students,
            "avg_score": avg_score, "max_possible": max_possible,
            "full_marks": full_marks, "totals": totals,
        }
    conn.close()
    return templates.TemplateResponse(request, "report.html", {
        "user": user, "sessions": sessions, "current_session": current_session,
        "report_data": report_data, "selected_sid": sid,
    })


@app.get("/admin/report/export-csv")
async def export_report_csv(request: Request, session_id: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    sess_row = conn.execute("SELECT * FROM lab_sessions WHERE id=?", (session_id,)).fetchone()
    if not sess_row:
        conn.close()
        return JSONResponse({"error": "Session not found"}, status_code=404)
    session = dict(sess_row)
    questions = [dict(q) for q in conn.execute("""
        SELECT qb.id, qb.title FROM session_questions sq
        JOIN question_bank qb ON sq.question_id=qb.id
        WHERE sq.session_id=? ORDER BY sq.question_order
    """, (session_id,)).fetchall()]
    students = [dict(s) for s in conn.execute(
        "SELECT DISTINCT matric_no FROM student_session_attempts WHERE session_id=? ORDER BY matric_no",
        (session_id,)
    ).fetchall()]
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["Matric No"] + [f"Q{i+1}: {q['title'][:25]}" for i, q in enumerate(questions)] + ["Total", "Max"]
    writer.writerow(header)
    max_score = len(questions) * 100
    for st in students:
        matric = st["matric_no"]
        row = [matric]
        total_score = 0
        for q in questions:
            best = conn.execute("""
                SELECT MAX(CAST(passed AS REAL)/CASE WHEN ss.total=0 THEN 1 ELSE ss.total END * 100)
                FROM session_submissions ss WHERE ss.matric_no=? AND ss.session_id=? AND ss.question_id=?
            """, (matric, session_id, q["id"])).fetchone()[0]
            score = round(best, 1) if best is not None else 0
            total_score += score
            row.append(score)
        row.extend([round(total_score, 1), max_score])
        writer.writerow(row)
    conn.close()
    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8-sig')  # BOM for Excel
    safe_title = ''.join(c for c in session["title"] if c.isalnum() or c in ' _-').replace(' ', '_')
    filename = f"report_{safe_title}_{session_id}.csv"
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/admin/submissions/{sub_id}", response_class=HTMLResponse)
async def admin_submission_detail(request: Request, sub_id: int):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    conn = get_db()
    sub = conn.execute("SELECT * FROM session_submissions WHERE id=?", (sub_id,)).fetchone()
    if not sub:
        conn.close()
        raise HTTPException(404, "Submission not found")
    sub = dict(sub)
    q = conn.execute("SELECT title FROM question_bank WHERE id=?", (sub["question_id"],)).fetchone()
    sess = conn.execute("SELECT title FROM lab_sessions WHERE id=?", (sub["session_id"],)).fetchone()
    sub["question_title"] = q["title"] if q else "Unknown"
    sub["session_title"] = sess["title"] if sess else "Unknown"
    conn.close()
    return templates.TemplateResponse(request, "submission_detail.html", {"user": user, "sub": sub})


# ─── Admin AJAX API endpoints ──────────────────────────────────────────────────

@app.get("/admin/api/sessions")
async def api_admin_sessions(request: Request, page: int = 1, limit: int = 20):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM lab_sessions").fetchone()[0]
    offset = (page - 1) * limit
    rows = conn.execute(
        "SELECT id, title, course_code, window_start, window_end, duration_minutes, is_active FROM lab_sessions ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    sessions = []
    for r in rows:
        s = dict(r)
        s["q_count"] = conn.execute(
            "SELECT COUNT(*) FROM session_questions WHERE session_id=?", (s["id"],)
        ).fetchone()[0]
        sessions.append(s)
    conn.close()
    pages = max(1, (total + limit - 1) // limit)
    return JSONResponse({"sessions": sessions, "total": total, "page": page, "pages": pages})


@app.get("/admin/api/questions")
async def api_admin_questions(
    request: Request, page: int = 1, limit: int = 50,
    search: str = None, course: str = None, chapter: int = None
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = get_db()
    where, params = [], []
    if search:
        where.append("title LIKE ?")
        params.append(f"%{search}%")
    if course:
        where.append("course_code = ?")
        params.append(course)
    if chapter:
        where.append("chapter = ?")
        params.append(chapter)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    total = conn.execute(f"SELECT COUNT(*) FROM question_bank {w}", params).fetchone()[0]
    offset = (page - 1) * limit
    rows = conn.execute(
        f"SELECT id, title, course_code, chapter, difficulty, hidden_tests FROM question_bank {w} ORDER BY id LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    questions = []
    for r in rows:
        q = dict(r)
        try:
            q["hidden_test_count"] = len(json.loads(q.get("hidden_tests") or "[]"))
        except Exception:
            q["hidden_test_count"] = 0
        del q["hidden_tests"]
        questions.append(q)
    conn.close()
    pages = max(1, (total + limit - 1) // limit)
    return JSONResponse({"questions": questions, "total": total, "page": page, "pages": pages})


@app.get("/admin/api/students")
async def api_admin_students(
    request: Request, page: int = 1, limit: int = 50, search: str = None
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = get_db()
    where = "u.is_admin = 0"
    params: list = []
    if search:
        where += " AND (u.matric_no LIKE ? OR u.full_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    total = conn.execute(f"SELECT COUNT(*) FROM users u WHERE {where}", params).fetchone()[0]
    offset = (page - 1) * limit
    rows = conn.execute(f"""
        SELECT u.matric_no, u.full_name, u.is_admin, u.created_at,
               COUNT(ss.id) as submission_count
        FROM users u
        LEFT JOIN session_submissions ss ON ss.matric_no = u.matric_no
        WHERE {where}
        GROUP BY u.matric_no
        ORDER BY u.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    students = [dict(r) for r in rows]
    conn.close()
    pages = max(1, (total + limit - 1) // limit)
    return JSONResponse({"students": students, "total": total, "page": page, "pages": pages})


@app.get("/admin/api/submissions")
async def api_admin_submissions(
    request: Request, page: int = 1, limit: int = 50,
    session_id: int = None, matric: str = None, status: str = None
):
    user = get_current_user(request)
    if not user or not user["is_admin"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = get_db()
    where, params = [], []
    if session_id:
        where.append("ss.session_id = ?")
        params.append(session_id)
    if matric:
        where.append("ss.matric_no LIKE ?")
        params.append(f"%{matric}%")
    if status:
        where.append("ss.status = ?")
        params.append(status)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    total = conn.execute(f"SELECT COUNT(*) FROM session_submissions ss {w}", params).fetchone()[0]
    offset = (page - 1) * limit
    rows = conn.execute(f"""
        SELECT ss.id, ss.matric_no, ss.session_id, ls.title as session_title,
               ss.question_id, qb.title as question_title,
               ss.language, ss.status, ss.passed, ss.total, ss.runtime_ms, ss.created_at
        FROM session_submissions ss
        LEFT JOIN lab_sessions ls ON ls.id = ss.session_id
        LEFT JOIN question_bank qb ON qb.id = ss.question_id
        {w}
        ORDER BY ss.id DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    submissions = [dict(r) for r in rows]
    conn.close()
    pages = max(1, (total + limit - 1) // limit)
    return JSONResponse({"submissions": submissions, "total": total, "page": page, "pages": pages})


@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(auto_finalize_expired_sessions())


async def auto_finalize_expired_sessions():
    """Background task: every 60s, auto-finalize sessions where time ran out."""
    import asyncio
    while True:
        await asyncio.sleep(60)
        try:
            conn = get_db()
            # Find IN_PROGRESS attempts where started_at + duration_minutes has passed
            expired = conn.execute("""
                SELECT a.id, a.matric_no, a.session_id, a.started_at, s.duration_minutes,
                       s.window_end
                FROM student_session_attempts a
                JOIN lab_sessions s ON a.session_id = s.id
                WHERE a.status = 'IN_PROGRESS'
            """).fetchall()

            now = now_myt()
            finalized = 0
            for row in expired:
                started = datetime.fromisoformat(row["started_at"]).replace(tzinfo=None)
                duration_secs = row["duration_minutes"] * 60
                elapsed = (now.replace(tzinfo=None) - started).total_seconds()
                # Also check window_end
                window_end = datetime.fromisoformat(row["window_end"]).replace(tzinfo=None)
                time_expired = elapsed >= duration_secs
                window_expired = now.replace(tzinfo=None) > window_end
                if time_expired or window_expired:
                    conn.execute("""
                        UPDATE student_session_attempts
                        SET status='SUBMITTED', submitted_at=datetime('now')
                        WHERE id=?
                    """, (row["id"],))
                    finalized += 1

            if finalized > 0:
                conn.commit()
                print(f"[auto-finalize] Finalized {finalized} expired session(s)")
            conn.close()
        except Exception as e:
            print(f"[auto-finalize] Error: {e}")
