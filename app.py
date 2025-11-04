from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, Game, Purchase, UserGame, Rating
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

app.permanent_session_lifetime = timedelta(minutes=30)

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
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                if user.role == "inactive":
                    flash("Your account has been deactivated. Please contact support.", "error")
                else:
                    session.permanent = True
                    session["username"] = user.username
                    session["role"] = user.role

                    if user.role == "admin":
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
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Please choose another.", "error")
            else:
                user = User(username=username, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
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
        total_games_count = Game.query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        # Get games with pagination
        games = Game.query.order_by(Game.id).offset(offset).limit(per_page).all()

        # Get statistics
        total_games = Game.query.count()
        sold_games = Purchase.query.count()
        total_users = User.query.filter_by(role='customer').count()
        active_users = User.query.filter_by(role='customer').count()  # All customers are active for now

    except Exception as e:
        flash("Error loading dashboard.", "error")
        games = []
        total_games = sold_games = total_users = active_users = total_pages = 0
        page = 1

    return render_template("admin.html", games=games, total_games=total_games, sold_games=sold_games, total_users=total_users, active_users=active_users, page=page, total_pages=total_pages)

# ---------- ADMIN: ADD GAME ----------
@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = request.form["title"]
        platform = request.form["platform"]
        quantity = request.form["quantity"]
        genre = request.form.get("genre", "Action")

        try:
            game = Game(title=title, platform=platform, quantity=int(quantity), genre=genre)
            db.session.add(game)
            db.session.commit()
            flash("Game added successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error adding game.", "error")
    return redirect(url_for("admin"))

# ---------- ADMIN: UPDATE GAME QUANTITY ----------
@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    if "username" in session and session["role"] == "admin":
        game_id = request.form["game_id"]
        additional_quantity = request.form["additional_quantity"]

        try:
            game = Game.query.get(int(game_id))
            if game:
                game.quantity += int(additional_quantity)
                db.session.commit()
                flash("Game quantity updated successfully.", "success")
            else:
                flash("Game not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error updating game quantity.", "error")
    return redirect(url_for("admin"))

# ---------- ADMIN: REMOVE GAME ----------
@app.route("/remove_game/<int:game_id>")
def remove_game(game_id):
    if "username" in session and session["role"] == "admin":
        try:
            game = Game.query.get(game_id)
            if game:
                db.session.delete(game)
                db.session.commit()
                flash("Game removed successfully.", "success")
            else:
                flash("Game not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error removing game.", "error")
    return redirect(url_for("admin"))

# ---------- ADMIN: USER MANAGEMENT ----------
@app.route("/user_management")
def user_management():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        users = User.query.filter(User.role.in_(['customer', 'inactive'])).order_by(User.username).all()

        # Get activity data for each user (purchases instead of rentals)
        for user in users:
            total_purchases = Purchase.query.filter_by(username=user.username).count()
            user.total_purchases = total_purchases
            user.active_purchases = total_purchases  # All purchases are active

    except Exception as e:
        flash("Error loading user management.", "error")
        users = []

    return render_template("user_management.html", users=users)

# ---------- ADMIN: DEACTIVATE USER ----------
@app.route("/deactivate_user/<username>")
def deactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.role = 'inactive'
                db.session.commit()
                flash(f"User '{username}' has been deactivated.", "success")
            else:
                flash("User not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error deactivating user.", "error")
    return redirect(url_for("user_management"))

# ---------- ADMIN: REACTIVATE USER ----------
@app.route("/reactivate_user/<username>")
def reactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.role = 'customer'
                db.session.commit()
                flash(f"User '{username}' has been reactivated.", "success")
            else:
                flash("User not found.", "error")
        except Exception as e:
            db.session.rollback()
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
        # Build the query with filters
        query = Game.query

        if search:
            query = query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            query = query.filter_by(platform=platform_filter)

        if genre_filter:
            query = query.filter_by(genre=genre_filter)

        # Get total count for pagination
        total_games_count = query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        # Add pagination
        games = query.order_by(Game.id).offset(offset).limit(per_page).all()

        # Get unique platforms for filter dropdown
        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]
    except Exception as e:
        flash("Error loading games.", "error")
        games = []
        platforms = []
        total_pages = 0
        page = 1
    return render_template("customer.html", games=games, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages)

# ---------- CUSTOMER: BUY GAME ----------
@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            game = Game.query.get(game_id)
            if not game or game.quantity <= 0:
                flash("Game is out of stock.", "error")
                return redirect(url_for("customer"))

            # Create purchase record
            purchase = Purchase(username=session["username"], game_id=game_id, price_paid=game.price)
            db.session.add(purchase)

            # Create user game entry
            user_game = UserGame(username=session["username"], game_id=game_id, condition='new')
            db.session.add(user_game)

            # Decrease game quantity
            game.quantity -= 1

            db.session.commit()
            flash("Game purchased successfully.", "success")
        except Exception as e:
            db.session.rollback()
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
            # Get user's purchase history, owned games, and ratings to render template with error
            try:
                purchases = Purchase.query.filter_by(username=session["username"]).join(Game).order_by(Purchase.purchase_date.desc()).all()
            except Exception as e:
                purchases = []
            try:
                user_games = UserGame.query.filter_by(username=session["username"]).join(Game).order_by(UserGame.purchase_date.desc()).all()
            except Exception as e:
                user_games = []
            try:
                ratings = Rating.query.filter_by(username=session["username"]).join(Game).order_by(Rating.date.desc()).all()
            except Exception as e:
                ratings = []
            return render_template("profile.html", purchases=purchases, user_games=user_games, ratings=ratings)
        try:
            user = User.query.filter_by(username=session["username"]).first()
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating password.", "error")

    # Get user's purchase history
    try:
        purchases = Purchase.query.filter_by(username=session["username"]).join(Game).order_by(Purchase.purchase_date.desc()).all()
    except Exception as e:
        purchases = []

    # Get user's owned games
    try:
        user_games = UserGame.query.filter_by(username=session["username"]).join(Game).order_by(UserGame.purchase_date.desc()).all()
    except Exception as e:
        user_games = []

    # Get user's ratings and reviews
    try:
        ratings = Rating.query.filter_by(username=session["username"]).join(Game).order_by(Rating.date.desc()).all()
    except Exception as e:
        ratings = []

    return render_template("profile.html", purchases=purchases, user_games=user_games, ratings=ratings)

# ---------- CUSTOMER: MARKETPLACE ----------
@app.route("/marketplace")
def marketplace():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    platform_filter = request.args.get('platform', '')
    genre_filter = request.args.get('genre', '')

    try:
        # Build the query with filters
        query = UserGame.query.filter_by(listed_for_sale=True).join(Game)

        if search:
            query = query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            query = query.filter(Game.platform == platform_filter)

        if genre_filter:
            query = query.filter(Game.genre == genre_filter)

        # Get total count for pagination
        total_games_count = query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        # Add pagination
        user_games = query.order_by(UserGame.purchase_date).offset(offset).limit(per_page).all()

        # Get unique platforms for filter dropdown
        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]
    except Exception as e:
        flash("Error loading marketplace.", "error")
        user_games = []
        platforms = []
        total_pages = 0
        page = 1

    return render_template("marketplace.html", user_games=user_games, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages)

# ---------- CUSTOMER: SELL GAME ----------
@app.route("/sell/<int:user_game_id>", methods=["GET", "POST"])
def sell(user_game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        user_game = UserGame.query.get(user_game_id)
        if not user_game or user_game.username != session["username"]:
            flash("Game not found or you don't own this game.", "error")
            return redirect(url_for("profile"))

        game = Game.query.get(user_game.game_id)
    except Exception as e:
        flash("Error loading game.", "error")
        return redirect(url_for("profile"))

    if request.method == "POST":
        sale_price = request.form.get("sale_price", "").strip()
        try:
            sale_price = float(sale_price)
            if sale_price <= 0:
                flash("Sale price must be greater than 0.", "error")
                return render_template("sell_game.html", user_game=user_game, game=game)
        except ValueError:
            flash("Invalid sale price.", "error")
            return render_template("sell_game.html", user_game=user_game, game=game)

        try:
            user_game.listed_for_sale = True
            user_game.sale_price = sale_price
            db.session.commit()
            flash("Game listed for sale successfully.", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            db.session.rollback()
            flash("Error listing game for sale.", "error")

    return render_template("sell_game.html", user_game=user_game, game=game)

# ---------- CUSTOMER: BUY USED GAME ----------
@app.route("/buy_used/<int:user_game_id>")
def buy_used(user_game_id):
    if "username" in session and session["role"] == "customer":
        try:
            user_game = UserGame.query.get(user_game_id)
            if not user_game or not user_game.listed_for_sale:
                flash("Game not found or not for sale.", "error")
                return redirect(url_for("marketplace"))

            if user_game.username == session["username"]:
                flash("You cannot buy your own game.", "error")
                return redirect(url_for("marketplace"))

            game = Game.query.get(user_game.game_id)
            if not game:
                flash("Game not found.", "error")
                return redirect(url_for("marketplace"))

            # Create purchase record
            purchase = Purchase(username=session["username"], game_id=user_game.game_id, condition='used', price_paid=user_game.sale_price, seller_username=user_game.username)
            db.session.add(purchase)

            # Transfer ownership
            user_game.username = session["username"]
            user_game.listed_for_sale = False
            user_game.sale_price = None
            user_game.purchase_date = datetime.utcnow()

            db.session.commit()
            flash("Used game purchased successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error purchasing used game.", "error")
    return redirect(url_for("marketplace"))

# ---------- CUSTOMER: RATE GAME ----------
@app.route("/rate_game/<int:game_id>", methods=["GET", "POST"])
def rate_game(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        game = Game.query.get(game_id)
        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("customer"))

        # Check if user owns this game
        owned = UserGame.query.filter_by(username=session["username"], game_id=game_id).first()
        if not owned:
            flash("You can only rate games you own.", "error")
            return redirect(url_for("customer"))
    except Exception as e:
        flash("Error loading game.", "error")
        return redirect(url_for("customer"))

    if request.method == "POST":
        rating = request.form["rating"]
        review = request.form.get("review", "").strip()

        try:
            # Check if user already rated this game
            existing = Rating.query.filter_by(username=session["username"], game_id=game_id).first()

            if existing:
                # Update existing rating
                existing.rating = int(rating)
                existing.review = review
                existing.date = datetime.utcnow()
            else:
                # Insert new rating
                new_rating = Rating(username=session["username"], game_id=game_id, rating=int(rating), review=review)
                db.session.add(new_rating)

            db.session.commit()
            flash("Rating submitted successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            db.session.rollback()
            flash("Error submitting rating.", "error")

    return render_template("rate_game.html", game=game)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
