from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import subprocess


app = Flask(__name__)

API_KEY = os.environ.get('API_KEY')

if not API_KEY:
    raise ValueError("API_KEY environment variable not set")


def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password) VALUES (1, 'admin', 'admin@example.com', 'admin123')")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password) VALUES (2, 'user', 'user@example.com', 'user123')")

    conn.commit()
    conn.close()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>User Management</title>
</head>
<body>
    <h1>User Management System</h1>

    <form action="/user" method="GET">
        <label>User ID:</label>
        <input type="text" name="id">
        <button type="submit">Get User</button>
    </form>

    <form action="/search" method="GET">
        <label>Search by username:</label>
        <input type="text" name="username">
        <button type="submit">Search</button>
    </form>

    <div>{content}</div>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE.format(content="Ready"))


@app.route('/user')
def get_user():
    user_id = request.args.get('id')

    if not user_id:
        return jsonify({"error": "Missing id parameter"}), 400

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"id": user[0], "username": user[1], "email": user[2]})
    return jsonify({"error": "User not found"}), 404


@app.route('/search')
def search_users():
    username = request.args.get('username', '')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE username LIKE ?"
    cursor.execute(query, (f"%{username}%",))

    users = cursor.fetchall()
    conn.close()

    result = [{"id": u[0], "username": u[1], "email": u[2]} for u in users]
    return jsonify(result)


@app.route('/api/data')
def get_data():
    return jsonify({"api_key": API_KEY})


@app.route('/execute')
def execute_command():
    cmd = request.args.get('cmd', '')
    ALLOWED_COMMANDS = ['echo', 'date', 'whoami']

    parts = cmd.split()

    if not parts or parts[0] not in ALLOWED_COMMANDS:
        return jsonify({"error": "Command not allowed"}), 403

    result = subprocess.check_output(parts)
    return jsonify({"output": result.decode()})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)