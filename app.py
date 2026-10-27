
import sqlite3
import uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "phishguard-student-project-key"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "complaints.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            reporter_name TEXT NOT NULL,
            reporter_email TEXT NOT NULL,
            report_type TEXT NOT NULL,
            suspicious_url TEXT,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    connection = get_db_connection()

    reports = connection.execute("""
        SELECT complaint_id, report_type, status, created_at
        FROM complaints
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    connection.close()

    return render_template("index.html", reports=reports)


@app.route("/submit", methods=["POST"])
def submit_report():
    reporter_name = request.form.get("reporter_name", "").strip()
    reporter_email = request.form.get("reporter_email", "").strip()
    report_type = request.form.get("report_type", "").strip()
    suspicious_url = request.form.get("suspicious_url", "").strip()
    description = request.form.get("description", "").strip()

    allowed_types = ["Phishing Website", "Phishing Email", "Suspicious Message"]

    if not reporter_name or not reporter_email or not description:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("home"))

    if report_type not in allowed_types:
        flash("Please select a valid report type.", "error")
        return redirect(url_for("home"))

    complaint_id = "PG-" + uuid.uuid4().hex[:8].upper()

    connection = get_db_connection()

    connection.execute("""
        INSERT INTO complaints (
            complaint_id, reporter_name, reporter_email,
            report_type, suspicious_url, description
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        reporter_name,
        reporter_email,
        report_type,
        suspicious_url,
        description
    ))

    connection.commit()
    connection.close()

    return render_template(
        "index.html",
        reports=get_recent_reports(),
        submitted_id=complaint_id
    )


def get_recent_reports():
    connection = get_db_connection()

    reports = connection.execute("""
        SELECT complaint_id, report_type, status, created_at
        FROM complaints
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    connection.close()
    return reports


@app.route("/track", methods=["POST"])
def track_report():
    complaint_id = request.form.get("complaint_id", "").strip().upper()

    connection = get_db_connection()

    report = connection.execute("""
        SELECT complaint_id, report_type, status, created_at
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,)).fetchone()

    connection.close()

    if report is None:
        flash("No report was found with that complaint ID.", "error")
        return redirect(url_for("home"))

    return render_template(
        "index.html",
        reports=get_recent_reports(),
        tracked_report=report
    )


initialize_database()

if __name__ == "__main__":
    app.run(debug=True)