from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

#بداية الداتا بيز
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'atm.db')

# تعريف الداتا بيز
def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 0.0
            )
        """)
        #حط عينه في الجدول لو فاضي
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0: 
            cursor.executemany("""
                INSERT INTO users (username, password, balance)
                VALUES (?, ?, ?)
            """, [
                ("jane_smith", generate_password_hash("password456"), 1000.0),
                ("alice_brown", generate_password_hash("password789"), 2000.0)
            ])
        conn.commit()

# شغل الفانكشن بتاعت الداتا بيز أول ما البرنامج يرن
init_db()

# نموذج الفرونت اند
front_end_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATM Machine</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f2f2f2; margin: 0; padding: 0; }
        h1, h2 { text-align: center; color: #333; }
        .container { width: 90%; max-width: 400px; margin: 50px auto; background-color: #fff; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2); padding: 20px; }
        .form-group { margin-bottom: 20px; }
        label { font-weight: bold; display: block; margin-bottom: 5px; color: #333; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        input[type="password"] { letter-spacing: 2px; }
        button { width: 100%; padding: 10px; background-color: #4CAF50; border: none; color: white; font-size: 16px; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        .menu-button { margin: 10px 0; background-color: #2196F3; }
        .menu-button:hover { background-color: #1976D2; }
        .error { color: red; text-align: center; }
    </style>
</head>
<body>
    <div class="container" id="login-page">
        <h1>ATM Machine</h1>
        <form id="login-form">
            <div class="form-group">
                <label for="username">Enter Username:</label>
                <input type="text" id="username" placeholder="Enter your username" required>
            </div>
            <div class="form-group">
                <label for="password">Enter Password:</label>
                <input type="password" id="password" placeholder="Enter your password" required>
            </div>
            <button type="button" onclick="checkLogin()">Login</button>
        </form>
        <p id="error-msg" class="error"></p>
    </div>

    <div class="container" id="menu-page" style="display:none;">
        <h2>Main Menu</h2>
        <button class="menu-button" onclick="checkBalance()">Check Balance</button>
        <button class="menu-button" onclick="withdraw()">Withdraw</button>
        <button class="menu-button" onclick="deposit()">Deposit</button>
        <button class="menu-button" onclick="logout()">Logout</button>
    </div>

    <div class="container" id="response-page" style="display:none;">
        <h2 id="response-header"></h2>
        <p id="response-body"></p>
        <button onclick="goBack()">Back</button>
    </div>

    <script>
        async function checkLogin() {
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const result = await response.json();

            if (result.success) {
                document.getElementById("login-page").style.display = "none";
                document.getElementById("menu-page").style.display = "block";
            } else {
                document.getElementById("error-msg").innerText = result.message;
            }
        }

        async function checkBalance() {
            const response = await fetch('/balance');
            const result = await response.json();
            showResponse("Your Balance", `Your balance is $${result.balance}`);
        }

        async function withdraw() {
            const amount = prompt("Enter the amount to withdraw:");
            if (isNaN(amount) || amount <= 0) {
                alert("Please enter a valid amount.");
                return;
            }
            const response = await fetch('/withdraw', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amount })
            });
            const result = await response.json();
            showResponse(result.status, result.message);
        }

        async function deposit() {
            const amount = prompt("Enter the amount to deposit:");
            if (isNaN(amount) || amount <= 0) {
                alert("Please enter a valid amount.");
                return;
            }
            const response = await fetch('/deposit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amount })
            });
            const result = await response.json();
            showResponse(result.status, result.message);
        }

        function showResponse(header, message) {
            document.getElementById("menu-page").style.display = "none";
            document.getElementById("response-page").style.display = "block";
            document.getElementById("response-header").innerText = header;
            document.getElementById("response-body").innerText = message;
        }

        function goBack() {
            document.getElementById("response-page").style.display = "none";
            document.getElementById("menu-page").style.display = "block";
        }

        async function logout() {
            const response = await fetch('/logout');
            if (response.ok) {
                document.getElementById("menu-page").style.display = "none";
                document.getElementById("login-page").style.display = "block";
            }
        }
    </script>
</body>
</html>
"""
#بداية الباك اند
@app.route("/")
def index():
    if 'logged_in' not in session:
        return render_template_string(front_end_template)
    return redirect(url_for('menu'))
#تعريف صفحة الدخول
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password, balance FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], password):
            session['logged_in'] = True
            session['username'] = username
            session['balance'] = user[1]
            return jsonify(success=True)
        return jsonify(success=False, message="Invalid username or password.")
#تعريف المنيو
@app.route("/menu")
def menu():
    # Your logic for the menu goes here
    return render_template_string(front_end_template)

#تعريف صفحة الbalance 
@app.route("/balance")
def check_balance():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    return jsonify(balance=session['balance'])
#تعريف صفحة الwithdraw
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    data = request.json
    try:
        amount = float(data["amount"])
    except ValueError:
        return jsonify(status="Error", message="Invalid amount.")

    if amount > 0 and amount <= session['balance']:
        session['balance'] -= amount
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (session['balance'], session['username']))
            conn.commit()
        return jsonify(status="Success", message=f"${amount} withdrawn successfully.")
    return jsonify(status="Error", message="Invalid amount or insufficient balance.")
#تعريف صفحة الdeposit
@app.route("/deposit", methods=["POST"])
def deposit():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    data = request.json
    try:
        amount = float(data["amount"])
    except ValueError:
        return jsonify(status="Error", message="Invalid amount.")

    if amount > 0:
        session['balance'] += amount
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (session['balance'], session['username']))
            conn.commit()
        return jsonify(status="Success", message=f"${amount} deposited successfully.")
    return jsonify(status="Error", message="Invalid amount.")
#تعريف الlog out
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()  # زيادة تأكيد علي الداتا بيز
    app.run(debug=True)
