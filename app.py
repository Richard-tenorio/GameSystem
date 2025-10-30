from flask import Flask, render_template, request, redirect, url_for, session
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
    database="gaming_rental_db" # UPDATED: Database name for game rental
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
                # UPDATED: Redirect to 'customer'
                return redirect(url_for("customer"))
        else:
            # Renders login.html
            return render_template("login.html", error="Invalid username or password")

    # Renders login.html
    return render_template("login.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    # UPDATED: Select from 'games' table
    cursor.execute("SELECT * FROM games")
    games = cursor.fetchall()
    # Renders admin.html
    return render_template("admin.html", games=games)

# ---------- ADMIN: ADD GAME ----------
@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = request.form["title"]
        # UPDATED: Changed 'author' to 'platform'
        platform = request.form["platform"] 
        # UPDATED: Changed 'copies' to 'quantity'
        quantity = request.form["quantity"]

        # UPDATED: Insert into 'games' table with new columns
        cursor.execute("INSERT INTO games (title, platform, quantity) VALUES (%s, %s, %s)", (title, platform, quantity))
        db.commit()
    return redirect(url_for("admin"))

# ---------- ADMIN: REMOVE GAME ----------
@app.route("/remove_game/<int:game_id>")
def remove_game(game_id):
    if "username" in session and session["role"] == "admin":
        # UPDATED: Delete from 'games' table
        cursor.execute("DELETE FROM games WHERE id=%s", (game_id,))
        db.commit()
    return redirect(url_for("admin"))

# ---------- CUSTOMER DASHBOARD (formerly STUDENT) ----------
@app.route("/customer")
def customer():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    # UPDATED: Select from 'games' table
    cursor.execute("SELECT * FROM games")
    games = cursor.fetchall()
    # Renders customer.html
    return render_template("customer.html", games=games)

# ---------- CUSTOMER: RENT (formerly BORROW) ----------
@app.route("/rent/<int:game_id>")
def rent(game_id):
    if "username" in session and session["role"] == "customer":
        # UPDATED: Update 'quantity' column in 'games' table
        cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s AND quantity > 0", (game_id,))
        db.commit()
    return redirect(url_for("customer"))

# ---------- CUSTOMER: RETURN GAME (formerly RETURN BOOK) ----------
@app.route("/return_game/<int:game_id>")
def return_game(game_id):
    if "username" in session and session["role"] == "customer":
        # UPDATED: Update 'quantity' column in 'games' table
        cursor.execute("UPDATE games SET quantity = quantity + 1 WHERE id=%s", (game_id,))
        db.commit()
    return redirect(url_for("customer"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)