from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, Game, Purchase, UserGame, Rating, GameSuggestion
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re
import logging
import secrets
from datetime import datetime, timedelta

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

def check_user_balance(username, required_amount):
    """
    Check if user has sufficient balance for a purchase.
    Returns (has_balance, current_balance)
    """
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            return user.balance >= required_amount, user.balance
        return False, 0.0
    except Exception:
        return False, 0.0

def deduct_user_balance(username, amount):
    """
    Deduct amount from user's balance.
    Returns True if successful, False otherwise.
    """
    try:
        user = User.query.filter_by(username=username).first()
        if user and user.balance >= amount:
            user.balance -= amount
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False

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
        email = request.form["email"]
        full_name = request.form["full_name"]
        age = request.form["age"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = "customer"  # Users can only register as customers

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "error")
            return render_template("register.html")

        # Validate age
        try:
            age_int = int(age)
            if age_int < 13 or age_int > 120:
                flash("Age must be between 13 and 120.", "error")
                return render_template("register.html")
        except ValueError:
            flash("Invalid age.", "error")
            return render_template("register.html")

        # Validate email format
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("Invalid email format.", "error")
            return render_template("register.html")

        try:
            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user:
                flash("Username already exists. Please choose another.", "error")
            elif existing_email:
                flash("Email address already registered. Please use another.", "error")
            else:
                user = User(username=username, email=email, full_name=full_name, age=age_int, role=role)
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

        # Calculate sold count for each game
        for game in games:
            game.sold_count = Purchase.query.filter_by(game_id=game.id).count()

        # Get statistics
        total_games = Game.query.count()
        sold_games = Purchase.query.count()
        total_users = User.query.filter_by(role='customer').count()
        active_users = User.query.filter_by(role='customer').count()  # All customers are active for now

        # Get all users for the list
        users = User.query.order_by(User.username).all()

        # Check for pending suggestions and notify admin
        pending_count = GameSuggestion.query.filter_by(status='pending').count()

    except Exception as e:
        flash("Error loading dashboard.", "error")
        games = []
        users = []
        total_games = sold_games = total_users = active_users = total_pages = 0
        page = 1

    return render_template("admin.html", games=games, users=users, total_games=total_games, sold_games=sold_games, total_users=total_users, active_users=active_users, page=page, total_pages=total_pages, errors={}, pending_count=pending_count)

# ---------- ADMIN: ADD GAME ----------
@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = request.form["title"].strip()
        platform = request.form["platform"].strip()
        quantity = request.form["quantity"].strip()
        genre = request.form.get("genre", "Action").strip()
        price = request.form["price"].strip()

        # Validate inputs
        if not title:
            flash("Game title cannot be empty.", "error")
            return redirect(url_for("admin"))
        if len(title) > 100:
            flash("Game title must be 100 characters or less.", "error")
            return redirect(url_for("admin"))
        if not platform:
            flash("Platform cannot be empty.", "error")
            return redirect(url_for("admin"))
        if len(platform) > 50:
            flash("Platform must be 50 characters or less.", "error")
            return redirect(url_for("admin"))
        if not genre:
            flash("Genre cannot be empty.", "error")
            return redirect(url_for("admin"))
        try:
            quantity_int = int(quantity)
            if quantity_int <= 0:
                flash("Quantity must be a positive integer.", "error")
                return redirect(url_for("admin"))
        except ValueError:
            flash("Quantity must be a valid integer.", "error")
            return redirect(url_for("admin"))
        try:
            price_float = float(price)
            if price_float <= 0:
                flash("Price must be a positive number.", "error")
                return redirect(url_for("admin"))
        except ValueError:
            flash("Price must be a valid number.", "error")
            return redirect(url_for("admin"))

        # Check if game title already exists
        existing_game = Game.query.filter_by(title=title).first()
        if existing_game:
            flash("A game with this title already exists.", "error")
            return redirect(url_for("admin"))

        try:
            game = Game(title=title, platform=platform, quantity=quantity_int, genre=genre, price=price_float)
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

# ---------- ADMIN: ADD CREDITS ----------
@app.route("/add_credits/<username>", methods=["GET", "POST"])
def add_credits(username):
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin"))
    except Exception as e:
        flash("Error loading user.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        credits_to_add = request.form.get("credits", "").strip()
        try:
            credits_float = float(credits_to_add)
            if credits_float <= 0:
                flash("Credits must be a positive number.", "error")
                return render_template("add_credits.html", user=user)
        except ValueError:
            flash("Invalid credits amount.", "error")
            return render_template("add_credits.html", user=user)

        try:
            user.balance += credits_float
            db.session.commit()
            flash(f"Added ${credits_float:.2f} to {username}'s balance.", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            db.session.rollback()
            flash("Error adding credits.", "error")

    return render_template("add_credits.html", user=user)

# ---------- ADMIN: MANAGE SUGGESTIONS ----------
@app.route("/manage_suggestions")
def manage_suggestions():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        suggestions = GameSuggestion.query.order_by(GameSuggestion.date_suggested.desc()).all()
    except Exception as e:
        flash("Error loading suggestions.", "error")
        suggestions = []

    return render_template("manage_suggestions.html", suggestions=suggestions)

# ---------- ADMIN: APPROVE SUGGESTION ----------
@app.route("/approve_suggestion/<int:suggestion_id>")
def approve_suggestion(suggestion_id):
    if "username" in session and session["role"] == "admin":
        try:
            suggestion = GameSuggestion.query.get(suggestion_id)
            if suggestion:
                suggestion.status = 'approved'
                db.session.commit()
                flash("Suggestion approved successfully.", "success")
            else:
                flash("Suggestion not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error approving suggestion.", "error")
    return redirect(url_for("manage_suggestions"))

# ---------- ADMIN: REJECT SUGGESTION ----------
@app.route("/reject_suggestion/<int:suggestion_id>")
def reject_suggestion(suggestion_id):
    if "username" in session and session["role"] == "admin":
        try:
            suggestion = GameSuggestion.query.get(suggestion_id)
            if suggestion:
                suggestion.status = 'rejected'
                db.session.commit()
                flash("Suggestion rejected.", "success")
            else:
                flash("Suggestion not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error rejecting suggestion.", "error")
    return redirect(url_for("manage_suggestions"))

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
        # Get user balance
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0

        # Get official games (added by admin)
        official_query = Game.query

        if search:
            official_query = official_query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            official_query = official_query.filter_by(platform=platform_filter)

        if genre_filter:
            official_query = official_query.filter_by(genre=genre_filter)

        official_games = official_query.order_by(Game.id).offset(offset).limit(per_page).all()

        # Get used games for sale (only official games)
        used_query = UserGame.query.filter_by(listed_for_sale=True).filter(UserGame.game_id.isnot(None)).join(Game)

        if search:
            used_query = used_query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            used_query = used_query.filter(Game.platform == platform_filter)

        if genre_filter:
            used_query = used_query.filter(Game.genre == genre_filter)

        user_games = used_query.order_by(UserGame.purchase_date).all()

        # Get genres for filter dropdown
        genres = [g[0] for g in db.session.query(Game.genre).distinct().all()]

        # Get approved community games
        community_query = GameSuggestion.query.filter_by(status='approved')

        if search:
            community_query = community_query.filter(GameSuggestion.title.ilike(f"%{search}%"))

        if platform_filter:
            community_query = community_query.filter_by(platform=platform_filter)

        if genre_filter:
            community_query = community_query.filter_by(genre=genre_filter)

        approved_suggestions = community_query.order_by(GameSuggestion.date_suggested.desc()).all()

        # Load image filenames for suggestions
        for suggestion in approved_suggestions:
            image_file = os.path.join('static', 'uploads', f'suggestion_{suggestion.id}.txt')
            if os.path.exists(image_file):
                with open(image_file, 'r') as f:
                    suggestion.image = f.read().strip()

        # Combine games for pagination (simplified)
        total_games_count = official_query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        # Get unique platforms for filter dropdown
        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]
    except Exception as e:
        flash(f"Error loading games: {str(e)}", "error")
        official_games = []
        user_games = []
        approved_suggestions = []
        platforms = []
        total_pages = 0
        page = 1
        user_balance = 0.0
    return render_template("customer.html", games=official_games, user_games=user_games, approved_suggestions=approved_suggestions, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages, user_balance=user_balance)

# ---------- CUSTOMER: BUY GAME ----------
@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            user = User.query.filter_by(username=session["username"]).first()
            game = Game.query.get(game_id)
            if game:
                if game.quantity <= 0:
                    flash("Game is out of stock.", "error")
                    return redirect(url_for("customer"))

                # Redirect to confirmation page
                return redirect(url_for('confirm_purchase', game_id=game_id, condition='new'))
            else:
                # Check if it's a community game
                suggestion = GameSuggestion.query.get(game_id)
                if suggestion and suggestion.status == 'approved':
                    # For community games, no purchase record needed, just add to user games
                    user_game = UserGame(username=session["username"], game_id=None, condition='new',
                                       title=suggestion.title, platform=suggestion.platform, genre=suggestion.genre)
                    db.session.add(user_game)
                    db.session.commit()
                    flash("Community game added to your library!", "success")
                else:
                    flash("Game not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error purchasing game.", "error")
    return redirect(url_for("customer"))

# ---------- CUSTOMER: CONFIRM PURCHASE ----------
@app.route("/confirm_purchase/<int:game_id>")
def confirm_purchase(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    condition = request.args.get('condition', 'new')

    try:
        user = User.query.filter_by(username=session["username"]).first()
        game = Game.query.get(game_id)

        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("customer"))

        if condition == 'new':
            if game.quantity <= 0:
                flash("Game is out of stock.", "error")
                return redirect(url_for("customer"))
            price = game.price
        else:
            # For used games, get from marketplace
            user_game = UserGame.query.filter_by(game_id=game_id, listed_for_sale=True).first()
            if not user_game:
                flash("Game not found for sale.", "error")
                return redirect(url_for("marketplace"))
            price = user_game.sale_price

        user_balance = user.balance if user else 0.0

    except Exception as e:
        flash("Error loading purchase details.", "error")
        return redirect(url_for("customer"))

    return render_template("confirm_purchase.html", game=game, condition=condition.title(), price=price, user_balance=user_balance)

# ---------- CUSTOMER: PROCESS PURCHASE ----------
@app.route("/process_purchase/<int:game_id>")
def process_purchase(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    condition = request.args.get('condition', 'new')

    try:
        user = User.query.filter_by(username=session["username"]).first()
        game = Game.query.get(game_id)

        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("customer"))

        if condition == 'new':
            if game.quantity <= 0:
                flash("Game is out of stock.", "error")
                return redirect(url_for("customer"))
            price = game.price
        else:
            # For used games, get from marketplace
            user_game = UserGame.query.filter_by(game_id=game_id, listed_for_sale=True).first()
            if not user_game:
                flash("Game not found for sale.", "error")
                return redirect(url_for("marketplace"))
            price = user_game.sale_price

        # Check if user has sufficient balance
        has_balance, current_balance = check_user_balance(session["username"], price)
        if not has_balance:
            flash(f"Insufficient balance. You need ${price:.2f} but only have ${current_balance:.2f}.", "error")
            return redirect(url_for("confirm_purchase", game_id=game_id, condition=condition))

        # Deduct balance
        if not deduct_user_balance(session["username"], price):
            flash("Error processing payment.", "error")
            return redirect(url_for("confirm_purchase", game_id=game_id, condition=condition))

        if condition == 'new':
            # Create purchase record
            purchase = Purchase(username=session["username"], game_id=game_id, price_paid=price)
            db.session.add(purchase)

            # Create user game entry
            user_game = UserGame(username=session["username"], game_id=game_id, condition='new')
            db.session.add(user_game)

            # Decrease game quantity
            game.quantity -= 1
        else:
            # Used game purchase
            seller_user_game = UserGame.query.filter_by(game_id=game_id, listed_for_sale=True).first()

            # Create purchase record
            purchase = Purchase(username=session["username"], game_id=game_id, condition='used', price_paid=price, seller_username=seller_user_game.username)
            db.session.add(purchase)

            # Transfer ownership
            seller_user_game.username = session["username"]
            seller_user_game.condition = 'used'
            seller_user_game.listed_for_sale = False
            seller_user_game.sale_price = None
            seller_user_game.purchase_date = datetime.utcnow()

        db.session.commit()
        flash("Game purchased successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash("Error processing purchase.", "error")

    return redirect(url_for("customer"))

# ---------- CUSTOMER: PROFILE ----------
@app.route("/profile")
def profile():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    # Get user's purchase history
    try:
        purchases = Purchase.query.filter_by(username=session["username"]).join(Game).order_by(Purchase.purchase_date.desc()).all()
    except Exception as e:
        purchases = []

    # Get user's ratings and reviews
    try:
        ratings = Rating.query.filter_by(username=session["username"]).join(Game).order_by(Rating.date.desc()).all()
    except Exception as e:
        ratings = []

    # Get user balance
    try:
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0
    except Exception as e:
        user_balance = 0.0

    return render_template("profile.html", purchases=purchases, ratings=ratings, user_balance=user_balance)

# ---------- CUSTOMER: SETTINGS ----------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # Verify current password
        user = User.query.filter_by(username=session["username"]).first()
        if not user or not user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("settings.html")

        # Check if new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("settings.html")

        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, "error")
            return render_template("settings.html")

        try:
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating password.", "error")

    return render_template("settings.html")

# ---------- CUSTOMER: LIBRARY ----------
@app.route("/library")
def library():
    if "username" not in session:
        return redirect(url_for("login"))

    # Get user's owned games (both official and community)
    try:
        # Official games
        official_games = UserGame.query.filter_by(username=session["username"]).filter(UserGame.game_id.isnot(None)).join(Game).order_by(UserGame.purchase_date.desc()).all()
        # Community games
        community_games = UserGame.query.filter_by(username=session["username"]).filter(UserGame.game_id.is_(None)).order_by(UserGame.purchase_date.desc()).all()
        user_games = official_games + community_games
    except Exception as e:
        user_games = []

    return render_template("library.html", user_games=user_games)

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

        # Get approved community games
        approved_query = GameSuggestion.query.filter_by(status='approved')

        if search:
            approved_query = approved_query.filter(GameSuggestion.title.ilike(f"%{search}%"))

        if platform_filter:
            approved_query = approved_query.filter_by(platform=platform_filter)

        if genre_filter:
            approved_query = approved_query.filter_by(genre=genre_filter)

        approved_suggestions = approved_query.order_by(GameSuggestion.date_suggested.desc()).all()

        # Get unique platforms for filter dropdown
        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]
    except Exception as e:
        flash("Error loading marketplace.", "error")
        user_games = []
        approved_suggestions = []
        platforms = []
        total_pages = 0
        page = 1

    return render_template("marketplace.html", user_games=user_games, approved_suggestions=approved_suggestions, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages)

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

            # Redirect to confirmation page
            return redirect(url_for('confirm_purchase', game_id=user_game.game_id, condition='used'))
        except Exception as e:
            flash("Error loading game.", "error")
    return redirect(url_for("marketplace"))

# ---------- CUSTOMER: SUGGEST GAME ----------
@app.route("/suggest_game", methods=["GET", "POST"])
def suggest_game():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        platform = request.form["platform"].strip()
        genre = request.form.get("genre", "Action").strip()
        description = request.form.get("description", "").strip()

        # Validate inputs
        if not title:
            flash("Game title cannot be empty.", "error")
            return render_template("suggest_game.html")
        if len(title) > 100:
            flash("Game title must be 100 characters or less.", "error")
            return render_template("suggest_game.html")
        if not platform:
            flash("Platform cannot be empty.", "error")
            return render_template("suggest_game.html")
        if len(platform) > 50:
            flash("Platform must be 50 characters or less.", "error")
            return render_template("suggest_game.html")
        if not genre:
            flash("Genre cannot be empty.", "error")
            return render_template("suggest_game.html")

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generate unique filename
                    import uuid
                    filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                    image_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image_file.save(image_path)
                    image_filename = filename
                else:
                    flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, or WebP.", "error")
                    return render_template("suggest_game.html")

        # Check if suggestion already exists
        existing_suggestion = GameSuggestion.query.filter_by(title=title, platform=platform).first()
        if existing_suggestion:
            flash("A suggestion for this game already exists.", "error")
            return render_template("suggest_game.html")

        try:
            suggestion = GameSuggestion(
                title=title,
                platform=platform,
                genre=genre,
                description=description,
                suggested_by=session["username"],
                status='pending'
            )
            db.session.add(suggestion)
            db.session.commit()

            # Store image filename in a simple way - we'll use a global variable approach
            # or just rely on the file being saved with the suggestion ID
            if image_filename:
                # Rename the uploaded file to include suggestion ID for easy retrieval
                import uuid
                new_filename = f'suggestion_{suggestion.id}_{str(uuid.uuid4())[:8]}.{image_filename.split(".")[-1]}'
                old_path = os.path.join('static', 'uploads', image_filename)
                new_path = os.path.join('static', 'uploads', new_filename)
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    # Store the filename in a simple text file for retrieval
                    with open(os.path.join('static', 'uploads', f'suggestion_{suggestion.id}.txt'), 'w') as f:
                        f.write(new_filename)

            flash("Game suggestion submitted successfully!", "success")
            return redirect(url_for("customer"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting suggestion: {str(e)}", "error")

    return render_template("suggest_game.html")

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

# ---------- FORGOT PASSWORD ----------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    username = None
    user_found = False

    if request.method == "POST":
        username = request.form["username"].strip()

        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user_found = True
            else:
                flash("Username not found.", "error")
        except Exception as e:
            flash("An error occurred. Please try again.", "error")

    if request.method == "POST" and user_found:
        # Show password reset form
        return render_template("forgot_password.html", username=username, show_reset=True)

    # Handle password reset
    if request.method == "POST" and "new_password" in request.form:
        username = request.form["username"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("forgot_password.html", username=username, show_reset=True)

        # Validate password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, "error")
            return render_template("forgot_password.html", username=username, show_reset=True)

        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.set_password(new_password)
                db.session.commit()
                flash("Password changed successfully. Please log in.", "success")
                return redirect(url_for("login"))
            else:
                flash("User not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Please try again.", "error")

    return render_template("forgot_password.html", username=username, show_reset=False)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
