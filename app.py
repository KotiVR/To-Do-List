import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ------------------ DATABASE CONNECTION (Neon PostgreSQL) ------------------
def get_db_connection():
    return psycopg2.connect(
        host="ep-falling-grass-a40q9cy3-pooler.us-east-1.aws.neon.tech",          # e.g. ep-calm-dawn-12345.ap-southeast-1.aws.neon.tech
        port=5432,
        user="neondb_owner",          # e.g. neondb_owner
        password="npg_VSt5nCNLq1Ak",  # from Neon dashboard
        dbname="todoflow",    # e.g. neondb
        sslmode="require",                   # required for Neon
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# ------------------ ROUTES ------------------

@app.route("/sub.html")
def sub():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("sub.html", user=user)

# ✅ FIXED LOGOUT (works for both link and form)
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        identity = request.form.get("designation")
        gender = request.form.get("gender")
        college = request.form.get("college")
        company = request.form.get("company")

        if password != confirm_password:
            flash("Passwords do not match!")
            return render_template("register.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, pass, identity, gender, college, company)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, email, password, identity, gender, college, company))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))
        except Exception as e:
            print("Registration error:", e)
            flash("Email already registered or database error.")
            return render_template("register.html")
    return render_template("register.html")

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s AND pass = %s', (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["user"] = user
            flash("Login successful!")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials!")
            return render_template("login.html")
    return render_template("login.html")

# ------------------ PROFILE ------------------
@app.route("/profile")
def profile():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_type FROM users WHERE email = %s', (user["email"],))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    subscription_type = row["subscription_type"] if row and "subscription_type" in row else "Free"
    user["subscription_type"] = subscription_type
    return render_template("profile.html", user=user)

# ------------------ HOME ------------------
@app.route("/")
def home():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("home.html", user=user)

# ------------------ TASKS PAGE ------------------
@app.route("/mytasks")
def mytasks():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("task.html", user=user, tasks=tasks)

# ------------------ CRUD FOR TASKS ------------------

# CREATE
@app.route("/add_task", methods=["POST"])
def add_task():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    task_name = request.form.get("task_name")
    note = request.form.get("note", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tasks (task_name, status, note) VALUES (%s, %s, %s)',
        (task_name, "pending", note)
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Task added!")
    return redirect(url_for("mytasks"))

# ✅ EDIT TASK
@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        new_name = request.form.get("task_name")
        new_note = request.form.get("note")
        new_status = request.form.get("status")

        cursor.execute(
            'UPDATE tasks SET task_name = %s, note = %s, status = %s WHERE id = %s',
            (new_name, new_note, new_status, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Task updated successfully!")
        return redirect(url_for("mytasks"))

    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()

    if not task:
        flash("Task not found.")
        return redirect(url_for("mytasks"))

    return render_template("edit_task.html", task=task, user=user)

# ✅ TOGGLE STATUS
@app.route("/toggle_status/<int:task_id>", methods=["POST"])
def toggle_status(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()

    if not task:
        flash("Task not found.")
        return redirect(url_for("mytasks"))

    new_status = "completed" if task["status"] == "pending" else "pending"
    cursor.execute('UPDATE tasks SET status = %s WHERE id = %s', (new_status, task_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f"Task marked as {new_status}!")
    return redirect(url_for("mytasks"))

# DELETE
@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Task deleted!")
    return redirect(url_for("mytasks"))

# ------------------ API ENDPOINTS ------------------
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    user = session.get("user")
    if not user:
        return {"error": "Not logged in"}, 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_name, status, note FROM tasks')
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    mapped_tasks = [
        {"id": t["id"], "task": t["task_name"], "status1": t["status"], "notes": t["note"]}
        for t in tasks
    ]
    return {"tasks": mapped_tasks}

@app.route("/api/tasks", methods=["POST"])
def api_post_tasks():
    user = session.get("user")
    if not user:
        return {"error": "Not logged in"}, 401
    data = request.get_json()
    tasks = data.get("tasks", [])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks')
    for task in tasks:
        cursor.execute(
            'INSERT INTO tasks (task_name, status, note) VALUES (%s, %s, %s)',
            (task.get("task", ""), task.get("status1", "pending"), task.get("notes", "")),
        )
    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True}

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
