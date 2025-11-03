from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
# WARNING: In a production app, use a strong, secret key loaded from environment variables
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)

# ---------- DATABASE CONNECTION ----------
# Ensure your MySQL server is running and the database 'gaming_rental_db' exists.
db = mysql.connector.connect(
    host="localhost",
    user="root",        # your MySQL username
    password="",        # your MySQL password if any
    database="gaming_rental_db"
)
cursor = db.cursor(dictionary=True)

def validate_password(password):
    """
    Validate password: at least 8 characters, one uppercase, one lowercase, one digit, one special character.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (e.g., @, #, !)."
    return True, ""

# ---------- LOGIN (Root Route) ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user["password"], password):
                if user["role"] == "inactive":
                    flash("Your account has been deactivated. Please contact support.", "error")
                else:
                    session.permanent = True
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
        role = request.form["role"]

        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "error")
            return render_template("register.html")

        try:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("Username already exists. Please choose another.", "error")
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    (username, hashed_password, role)
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

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    try:
        # Get total games count for pagination
        cursor.execute("SELECT COUNT(*) as total FROM games")
        total_games_count = cursor.fetchone()["total"]
        total_pages = (total_games_count + per_page - 1) // per_page

        # Get games with rental counts with pagination
        cursor.execute("""
            SELECT g.*, COUNT(r.id) as rented_count
            FROM games g
            LEFT JOIN rentals r ON g.id = r.game_id AND r.status = 'active'
            GROUP BY g.id
            ORDER BY g.id
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        games = cursor.fetchall()

        # Get statistics
        cursor.execute("SELECT COUNT(*) as total_games FROM games")
        total_games = cursor.fetchone()["total_games"]

        cursor.execute("SELECT COUNT(*) as rented_games FROM rentals WHERE status='active'")
        rented_games = cursor.fetchone()["rented_games"]

        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE role='customer'")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE role='customer' AND username IN (SELECT DISTINCT username FROM rentals)")
        active_users = cursor.fetchone()["active_users"]

    except Exception as e:
        flash("Error loading dashboard.", "error")
        games = []
        total_games = rented_games = total_users = active_users = total_pages = 0
        page = 1

    return render_template("admin.html", games=games, total_games=total_games, rented_games=rented_games, total_users=total_users, active_users=active_users, page=page, total_pages=total_pages)

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

# ---------- ADMIN: USER MANAGEMENT ----------
@app.route("/user_management")
def user_management():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        cursor.execute("SELECT username, role FROM users WHERE role IN ('customer', 'inactive') ORDER BY username")
        users = cursor.fetchall()

        # Get activity data for each user
        for user in users:
            cursor.execute("""
                SELECT COUNT(*) as total_rentals,
                       COUNT(CASE WHEN status='active' THEN 1 END) as active_rentals,
                       COUNT(CASE WHEN status='returned' THEN 1 END) as returned_rentals,
                       COUNT(CASE WHEN status='overdue' THEN 1 END) as overdue_rentals
                FROM rentals WHERE username=%s
            """, (user["username"],))
            activity = cursor.fetchone()
            user.update(activity)

    except Exception as e:
        flash("Error loading user management.", "error")
        users = []

    return render_template("user_management.html", users=users)

# ---------- ADMIN: DEACTIVATE USER ----------
@app.route("/deactivate_user/<username>")
def deactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            cursor.execute("UPDATE users SET role='inactive' WHERE username=%s", (username,))
            db.commit()
            flash(f"User '{username}' has been deactivated.", "success")
        except Exception as e:
            db.rollback()
            flash("Error deactivating user.", "error")
    return redirect(url_for("user_management"))

# ---------- ADMIN: REACTIVATE USER ----------
@app.route("/reactivate_user/<username>")
def reactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            cursor.execute("UPDATE users SET role='customer' WHERE username=%s", (username,))
            db.commit()
            flash(f"User '{username}' has been reactivated.", "success")
        except Exception as e:
            db.rollback()
            flash("Error reactivating user.", "error")
    return redirect(url_for("user_management"))

# ---------- CUSTOMER DASHBOARD ----------
@app.route("/customer")
def customer():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    platform_filter = request.args.get('platform', '')
    genre_filter = request.args.get('genre', '')

    try:
        # Build the base query with filters
        query = "SELECT * FROM games WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM games WHERE 1=1"
        params = []

        if search:
            query += " AND title LIKE %s"
            count_query += " AND title LIKE %s"
            params.append(f"%{search}%")

        if platform_filter:
            query += " AND platform = %s"
            count_query += " AND platform = %s"
            params.append(platform_filter)

        if genre_filter:
            query += " AND genre = %s"
            count_query += " AND genre = %s"
            params.append(genre_filter)

        # Get total count for pagination
        cursor.execute(count_query, params)
        total_games_count = cursor.fetchone()["total"]
        total_pages = (total_games_count + per_page - 1) // per_page

        # Add pagination to the query
        query += " ORDER BY id LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        games = cursor.fetchall()

        # Get unique platforms for filter dropdown
        cursor.execute("SELECT DISTINCT platform FROM games")
        platforms = [row['platform'] for row in cursor.fetchall()]
    except Exception as e:
        flash("Error loading games.", "error")
        games = []
        platforms = []
        total_pages = 0
        page = 1
    return render_template("customer.html", games=games, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages)

# ---------- CUSTOMER: RENT GAME ----------
@app.route("/rent/<int:game_id>")
def rent(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            # Check if user already has this game rented
            cursor.execute("SELECT id FROM rentals WHERE username=%s AND game_id=%s AND status='active'", (session["username"], game_id))
            existing_rental = cursor.fetchone()

            if existing_rental:
                flash("You already have this game rented.", "error")
                return redirect(url_for("customer"))

            # Check if game is available
            cursor.execute("SELECT quantity FROM games WHERE id=%s", (game_id,))
            game = cursor.fetchone()

            if not game or game["quantity"] <= 0:
                flash("Game is out of stock.", "error")
                return redirect(url_for("customer"))

            # Calculate due date (7 days from now)
            due_date = (datetime.now() + timedelta(days=7)).date()

            # Insert rental record
            cursor.execute("""
                INSERT INTO rentals (username, game_id, due_date)
                VALUES (%s, %s, %s)
            """, (session["username"], game_id, due_date))

            # Decrease game quantity
            cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s", (game_id,))

            db.commit()
            flash(f"Game rented successfully! Due date: {due_date}", "success")
        except Exception as e:
            db.rollback()
            flash("Error renting game.", "error")
    return redirect(url_for("customer"))

# ---------- CUSTOMER: RETURN GAME ----------
@app.route("/return/<int:rental_id>")
def return_game(rental_id):
    if "username" in session and session["role"] == "customer":
        try:
            # Get rental details
            cursor.execute("""
                SELECT r.game_id, r.status, g.title
                FROM rentals r
                JOIN games g ON r.game_id = g.id
                WHERE r.id=%s AND r.username=%s AND r.status='active'
            """, (rental_id, session["username"]))
            rental = cursor.fetchone()

            if not rental:
                flash("Rental not found or already returned.", "error")
                return redirect(url_for("profile"))

            # Update rental status
            cursor.execute("""
                UPDATE rentals
                SET status='returned', return_date=NOW()
                WHERE id=%s
            """, (rental_id,))

            # Increase game quantity
            cursor.execute("UPDATE games SET quantity = quantity + 1 WHERE id=%s", (rental["game_id"],))

            db.commit()
            flash(f"Game '{rental['title']}' returned successfully!", "success")
        except Exception as e:
            db.rollback()
            flash("Error returning game.", "error")
    return redirect(url_for("profile"))

# ---------- CUSTOMER: BUY GAME ----------
@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            # Check if game is available
            cursor.execute("SELECT quantity FROM games WHERE id=%s", (game_id,))
            game = cursor.fetchone()

            if not game or game["quantity"] <= 0:
                flash("Game is out of stock.", "error")
                return redirect(url_for("customer"))

            # Insert purchase record as a rental with status 'purchased'
            cursor.execute("""
                INSERT INTO rentals (username, game_id, rental_date, status)
                VALUES (%s, %s, NOW(), 'purchased')
            """, (session["username"], game_id))

            # Decrease game quantity
            cursor.execute("UPDATE games SET quantity = quantity - 1 WHERE id=%s", (game_id,))

            db.commit()
            flash("Game purchased successfully.", "success")
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
        # Validate password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, "error")
            # Get user's rental history and ratings to render template with error
            try:
                cursor.execute("""
                    SELECT r.id, r.rental_date, r.due_date, r.return_date, r.status,
                           g.title, g.platform, g.genre
                    FROM rentals r
                    JOIN games g ON r.game_id = g.id
                    WHERE r.username = %s
                    ORDER BY r.rental_date DESC
                """, (session["username"],))
                rentals = cursor.fetchall()
            except Exception as e:
                rentals = []
            try:
                cursor.execute("""
                    SELECT r.rating, r.review, r.date, g.title, g.platform
                    FROM ratings r
                    JOIN games g ON r.game_id = g.id
                    WHERE r.username = %s
                    ORDER BY r.date DESC
                """, (session["username"],))
                ratings = cursor.fetchall()
            except Exception as e:
                ratings = []
            return render_template("profile.html", rentals=rentals, ratings=ratings)
        try:
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password=%s WHERE username=%s", (hashed_password, session["username"]))
            db.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.rollback()
            flash("Error updating password.", "error")

    # Get user's rental history
    try:
        cursor.execute("""
            SELECT r.id, r.rental_date, r.due_date, r.return_date, r.status,
                   g.title, g.platform, g.genre
            FROM rentals r
            JOIN games g ON r.game_id = g.id
            WHERE r.username = %s
            ORDER BY r.rental_date DESC
        """, (session["username"],))
        rentals = cursor.fetchall()
    except Exception as e:
        rentals = []

    # Get user's ratings and reviews
    try:
        cursor.execute("""
            SELECT r.rating, r.review, r.date, g.title, g.platform
            FROM ratings r
            JOIN games g ON r.game_id = g.id
            WHERE r.username = %s
            ORDER BY r.date DESC
        """, (session["username"],))
        ratings = cursor.fetchall()
    except Exception as e:
        ratings = []

    return render_template("profile.html", rentals=rentals, ratings=ratings)

# ---------- CUSTOMER: RATE GAME ----------
@app.route("/rate_game/<int:game_id>", methods=["GET", "POST"])
def rate_game(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        cursor.execute("SELECT * FROM games WHERE id=%s", (game_id,))
        game = cursor.fetchone()
        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("customer"))
    except Exception as e:
        flash("Error loading game.", "error")
        return redirect(url_for("customer"))

    if request.method == "POST":
        rating = request.form["rating"]
        review = request.form.get("review", "").strip()

        try:
            # Check if user already rated this game
            cursor.execute("SELECT id FROM ratings WHERE username=%s AND game_id=%s", (session["username"], game_id))
            existing = cursor.fetchone()

            if existing:
                # Update existing rating
                cursor.execute("UPDATE ratings SET rating=%s, review=%s WHERE id=%s", (rating, review, existing["id"]))
            else:
                # Insert new rating
                cursor.execute("INSERT INTO ratings (username, game_id, rating, review) VALUES (%s, %s, %s, %s)",
                             (session["username"], game_id, rating, review))

            db.commit()
            flash("Rating submitted successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            db.rollback()
            flash("Error submitting rating.", "error")

    return render_template("rate_game.html", game=game)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
