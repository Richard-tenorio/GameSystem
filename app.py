from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os

app = Flask(__name__)
# WARNING: In a production app, use a strong, secret key loaded from environment variables
app.secret_key = os.urandom(24) 

# ---------- DATABASE CONNECTION ----------
# Ensure your MySQL server is running and the database 'gaming_rental_db' exists.
db = mysql.connector.connect(
    host="localhost",
    user="root",        # your MySQL username
    password="",        # your MySQL password if any
    database="gaming_rental_db"
)
cursor = db.cursor(dictionary=True)

# ---------- LOGIN (Root Route) ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("customer"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# ---------- ACCOUNT REGISTRATION ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "customer" 

        try:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                error = "Username already exists. Please choose another."
            else:
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    (username, password, role)
                )
                db.commit()
                return redirect(url_for("login"))
        
        except Exception as e:
            db.rollback()
            error = f"An internal error occurred." 

    return render_template("register.html", error=error)

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    cursor.execute("SELECT * FROM games")
    games = cursor.fetchall()
    return render_template("admin.html", games=games)

# ---------- ADMIN: ADD GAME ----------
@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = request.form["title"]
        platform = request.form["platform"] 
        quantity = request.form["quantity"]

        cursor.execute("INSERT INTO games (title, platform, quantity) VALUES (%s, %s, %s)", (title, platform, quantity))
        db.commit()
    return redirect(url_for("admin"))

# ---------- ADMIN: REMOVE GAME ----------
@app.route("/remove_game/<int:game_id>")
def remove_game(game_id):
    if "username" in session and session["role"] == "admin":
        cursor.execute("DELETE FROM games WHERE id=%s", (game_id,))
        db.commit()
    return redirect(url_for("admin"))

# ---------- CUSTOMER DASHBOARD ----------
@app.route("/customer")
def customer():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    cursor.execute("SELECT * FROM games")
    games = cursor.fetchall()
    return render_template("customer.html", games=games)

# ---------- CUSTOMER: TRIAL (REPLACES RENT) ----------
@app.route("/trial/<int:game_id>")
def trial(game_id):
    if "username" in session and session["role"] == "customer":
        # Decrements quantity: Game is temporarily held for trial
        cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s AND quantity > 0", (game_id,))
        db.commit()
    return redirect(url_for("customer"))

# ---------- CUSTOMER: BUY (REPLACES RETURN) ----------
@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        # Deletes game from inventory: Represents a permanent purchase and removal from stock
        cursor.execute("DELETE FROM games WHERE id=%s", (game_id,))
        db.commit()
    return redirect(url_for("customer"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)