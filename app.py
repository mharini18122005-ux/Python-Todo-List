
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date, datetime

app = Flask(__name__)

# Database connection
def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create database and update existing table
def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    ]

    if "due_date" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")

    # Assign today's date to older tasks
    conn.execute(
        "UPDATE tasks SET due_date = ? WHERE due_date IS NULL",
        (date.today().isoformat(),)
    )

    conn.commit()
    conn.close()


# Home page with calendar and tasks
@app.route("/")
def home():
    selected_date = request.args.get("date", date.today().isoformat())

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        selected_date = date.today().isoformat()

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE due_date = ? ORDER BY id DESC",
        (selected_date,)
    ).fetchall()

    conn.close()

    pending_count = sum(1 for task in tasks if not task["completed"])
    completed_count = sum(1 for task in tasks if task["completed"])

    return render_template(
        "index.html",
        tasks=tasks,
        selected_date=selected_date,
        pending_count=pending_count,
        completed_count=completed_count
    )


# Add task
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    task_date = request.form.get("due_date", date.today().isoformat())

    try:
        datetime.strptime(task_date, "%Y-%m-%d")
    except ValueError:
        task_date = date.today().isoformat()

    if title:
        conn = get_db()
        conn.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            (title, task_date)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("home", date=task_date))


# Complete or undo task
@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    conn = get_db()

    task = conn.execute(
        "SELECT due_date FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if task:
        conn.execute(
            "UPDATE tasks SET completed = 1 - completed WHERE id = ?",
            (task_id,)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("home", date=task["due_date"] if task else date.today().isoformat()))


# Delete task
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()

    task = conn.execute(
        "SELECT due_date FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if task:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("home", date=task["due_date"] if task else date.today().isoformat()))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
