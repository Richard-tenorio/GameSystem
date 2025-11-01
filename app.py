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

        try:
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
                flash("Invalid username or password", "error")
        except Exception as e:
            flash("An internal error occurred.", "error")

    return render_template("login.html")

# ---------- ACCOUNT REGISTRATION ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "customer"

        try:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("Username already exists. Please choose another.", "error")
            else:
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    (username, password, role)
                )
                db.commit()
                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))
        except Exception as e:
            db.rollback()
            flash("An internal error occurred.", "error")

    return render_template("register.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        cursor.execute("SELECT * FROM games")
        games = cursor.fetchall()
    except Exception as e:
        flash("Error loading games.", "error")
        games = []
    return render_template("admin.html", games=games)

# ---------- ADMIN: ADD GAME ----------
@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = request.form["title"]
        platform = request.form["platform"]
        quantity = request.form["quantity"]
        genre = request.form.get("genre", "Action")

        try:
            cursor.execute("INSERT INTO games (title, platform, quantity, genre) VALUES (%s, %s, %s, %s)", (title, platform, quantity, genre))
            db.commit()
            flash("Game added successfully.", "success")
        except Exception as e:
            db.rollback()
            flash("Error adding game.", "error")
    return redirect(url_for("admin"))

# ---------- ADMIN: UPDATE GAME QUANTITY ----------
@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    if "username" in session and session["role"] == "admin":
        game_id = request.form["game_id"]
        additional_quantity = request.form["additional_quantity"]

        try:
            cursor.execute("UPDATE games SET quantity = quantity + %s WHERE id=%s", (additional_quantity, game_id))
            db.commit()
            flash("Game quantity updated successfully.", "success")
        except Exception as e:
            db.rollback()
            flash("Error updating game quantity.", "error")
    return redirect(url_for("admin"))

# ---------- ADMIN: REMOVE GAME ----------
@app.route("/remove_game/<int:game_id>")
def remove_game(game_id):
    if "username" in session and session["role"] == "admin":
        try:
            cursor.execute("DELETE FROM games WHERE id=%s", (game_id,))
            db.commit()
            flash("Game removed successfully.", "success")
        except Exception as e:
            db.rollback()
            flash("Error removing game.", "error")
    return redirect(url_for("admin"))

# ---------- CUSTOMER DASHBOARD ----------
@app.route("/customer")
def customer():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    search = request.args.get('search', '')
    platform_filter = request.args.get('platform', '')
    genre_filter = request.args.get('genre', '')

    try:
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if search:
            query += " AND title LIKE %s"
            params.append(f"%{search}%")

        if platform_filter:
            query += " AND platform = %s"
            params.append(platform_filter)

        if genre_filter:
            query += " AND genre = %s"
            params.append(genre_filter)

        cursor.execute(query, params)
        games = cursor.fetchall()

        # Get unique platforms for filter dropdown
        cursor.execute("SELECT DISTINCT platform FROM games")
        platforms = [row['platform'] for row in cursor.fetchall()]
    except Exception as e:
        flash("Error loading games.", "error")
        games = []
        platforms = []
    return render_template("customer.html", games=games, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter)

# ---------- CUSTOMER: TRIAL (REPLACES RENT) ----------
@app.route("/trial/<int:game_id>")
def trial(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s AND quantity > 0", (game_id,))
            if cursor.rowcount > 0:
                db.commit()
                flash("Trial started successfully.", "success")
            else:
                flash("Game is out of stock.", "error")
        except Exception as e:
            db.rollback()
            flash("Error starting trial.", "error")
    return redirect(url_for("customer"))

# ---------- CUSTOMER: BUY (REPLACES RETURN) ----------
@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s AND quantity > 0", (game_id,))
            if cursor.rowcount > 0:
                db.commit()
                flash("Game purchased successfully.", "success")
            else:
                flash("Game is out of stock.", "error")
        except Exception as e:
            db.rollback()
            flash("Error purchasing game.", "error")
    return redirect(url_for("customer"))

# ---------- CUSTOMER: PROFILE ----------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["password"]
        try:
            cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, session["username"]))
            db.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.rollback()
            flash("Error updating password.", "error")

    # No rental history since rentals table is not used
    history = []

    return render_template("profile.html", history=history)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
