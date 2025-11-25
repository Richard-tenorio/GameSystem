from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, Game, Purchase, UserGame, Rating, GameSuggestion, TopupRequest, Notification
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

app.permanent_session_lifetime = timedelta(minutes=30)

PLATFORMS = [

    "PlayStation 1 (PS1)",
    "PlayStation 2 (PS2)",
    "PlayStation 3 (PS3)",
    "PlayStation 4 (PS4 / Slim / Pro)",
    "PlayStation 5 (PS5 / Digital Edition)",
    "PlayStation Portable (PSP)",
    "PlayStation Vita (PS Vita)",
    "PlayStation Portal (Remote device)",

    "Xbox (Original)",
    "Xbox 360",
    "Xbox One / One S / One X",
    "Xbox Series S",
    "Xbox Series X",

    "Nintendo Entertainment System (NES)",
    "Super Nintendo (SNES)",
    "Nintendo 64 (N64)",
    "Nintendo GameCube",
    "Nintendo Wii",
    "Nintendo Wii U",
    "Nintendo Switch",
    "Nintendo Switch OLED",
    "Nintendo Switch Lite",
    "Game Boy",
    "Game Boy Color",
    "Game Boy Advance",
    "Nintendo DS",
    "Nintendo DS Lite",
    "DSi / DSi XL",
    "Nintendo 3DS",
    "Nintendo 3DS XL",
    "New 2DS XL",

    "Sega Master System",
    "Sega Genesis / Mega Drive",
    "Sega Saturn",
    "Sega Dreamcast",
    "Game Gear",

    "Atari 2600",
    "Atari 5200",
    "Atari 7800",
    "Atari Jaguar",
    "Atari Lynx",
    "Atari VCS (Modern re-release)",

    "Neo Geo",
    "Neo Geo Pocket",
    "TurboGrafx-16 (PC Engine)",
    "Philips CD-i",
    "Intellivision",
    "ColecoVision",
    "Panasonic 3DO"
]

def validate_password(password):
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
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            return user.balance >= required_amount, user.balance
        return False, 0.0
    except Exception:
        return False, 0.0

def deduct_user_balance(username, amount):
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

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        smtp_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = app.config.get('MAIL_PORT', 587)
        smtp_username = app.config.get('MAIL_USERNAME')
        smtp_password = app.config.get('MAIL_PASSWORD')

        # Always print OTP to console for testing/fallback
        print(f"OTP code for {email}: {otp}")

        # If SMTP credentials are not configured, return True (console OTP)
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured. Using console OTP for testing.")
            return True

        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = 'Your OTP Code for GameSystem'

        body = f'Your OTP code is: {otp}. It will expire in 5 minutes. Please enter this code to complete your login.'
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()
        print(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        # Always return True to allow login with console OTP
        print(f"Using console OTP due to email error. OTP code for {email}: {otp}")
        return True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                if user.status == "inactive":
                    flash("Your account has been deactivated. Please contact support.", "error")
                    return render_template("login.html")
                else:
                    if user.role == "admin":
                        # Log in admin directly
                        session.permanent = True
                        session["username"] = user.username
                        session["role"] = user.role
                        return redirect(url_for("admin"))
                    else:
                        # Generate new OTP for customers (automated, no DB storage)
                        otp = generate_otp()
                        session["otp_code"] = otp
                        session["otp_expires"] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

                        # Send OTP via email
                        if send_otp_email(user.email, otp):
                            session["pending_username"] = user.username
                            return redirect(url_for("verify_otp"))
                        else:
                            flash("Failed to send OTP. Please try again.", "error")
            else:
                flash("Invalid username or password", "error")
        except Exception as e:
            flash("An internal error occurred.", "error")

    return render_template("login.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        otp = request.form.get("otp", "")

        try:
            user = User.query.filter_by(username=session["pending_username"]).first()
            if user and session.get("otp_code") == otp and session.get("otp_expires") and session["otp_expires"] > datetime.utcnow().timestamp():
                # Clear OTP from session
                session.pop("otp_code", None)
                session.pop("otp_expires", None)
                session.pop("pending_username", None)

                # Log in user
                session.permanent = True
                session["username"] = user.username
                session["role"] = user.role

                if user.role == "admin":
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("customer"))
            else:
                flash("Invalid or expired OTP.", "error")
        except Exception as e:
            flash("An internal error occurred.", "error")

    return render_template("verify_otp.html")

@app.route("/resend_otp")
def resend_otp():
    if "pending_username" not in session:
        return redirect(url_for("login"))

    try:
        user = User.query.filter_by(username=session["pending_username"]).first()
        if user:
            # Check if we recently sent an OTP (prevent spam)
            recently_sent = session.get("otp_expires") and (datetime.utcnow().timestamp() - session["otp_expires"]) < 60 if session.get("otp_expires") else False
            if recently_sent:
                flash("Please wait before requesting a new OTP.", "error")
                return redirect(url_for("verify_otp"))

            # Generate new OTP
            otp = generate_otp()
            session["otp_code"] = otp
            session["otp_expires"] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

            # Send OTP via email
            if send_otp_email(user.email, otp):
                flash("New OTP sent to your email.", "success")
            else:
                flash("Failed to send OTP. Please try again.", "error")
        else:
            flash("User not found.", "error")
    except Exception as e:
        flash("An error occurred while resending OTP.", "error")

    return redirect(url_for("verify_otp"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        full_name = request.form["full_name"]
        age = request.form["age"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = "customer"

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "error")
            return render_template("register.html")

        try:
            age_int = int(age)
            if age_int < 13 or age_int > 120:
                flash("Age must be between 13 and 120.", "error")
                return render_template("register.html")
        except ValueError:
            flash("Invalid age.", "error")
            return render_template("register.html")

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
                user = User(username=username, email=email, full_name=full_name, age=age_int, role=role, status='active')
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("An internal error occurred.", "error")

    return render_template("register.html")

@app.route("/admin")
def admin():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    page_suggestions = int(request.args.get('page_suggestions', 1))
    per_page_suggestions = 10
    offset_suggestions = (page_suggestions - 1) * per_page_suggestions

    # Initialize variables
    total_games = 0
    sold_games = 0
    total_users = 0
    active_users = 0
    total_revenue = 0.0
    games = []
    users = []
    total_games_count = 0
    total_pages = 0
    pending_count = 0
    pending_topup_count = 0
    approved_suggestions = []
    total_suggestions_count = 0
    total_pages_suggestions = 0

    try:
        total_games = Game.query.count()
        sold_games = Purchase.query.count()
        total_users = User.query.filter_by(status='active').count()
        active_users = total_users

        total_revenue = db.session.query(db.func.sum(Purchase.price_paid)).scalar() or 0.0

        # Simplified query for MySQL compatibility
        games = Game.query.order_by(Game.id).offset(offset).limit(per_page).all()

        # Add sold_count to each game
        for game in games:
            game.sold_count = Purchase.query.filter_by(game_id=game.id).count()

        total_games_count = total_games
        total_pages = (total_games_count + per_page - 1) // per_page

        users = User.query.order_by(User.username).all()

        pending_count = GameSuggestion.query.filter_by(status='pending').count()
        try:
            pending_topup_count = TopupRequest.query.filter_by(status='pending').count()
        except Exception as e:
            print(f"Error getting topup count: {e}")
            pending_topup_count = 0

        total_suggestions_count = GameSuggestion.query.filter_by(status='approved').count()
        total_pages_suggestions = (total_suggestions_count + per_page_suggestions - 1) // per_page_suggestions

        approved_suggestions = GameSuggestion.query.filter_by(status='approved').order_by(GameSuggestion.date_suggested.desc()).offset(offset_suggestions).limit(per_page_suggestions).all()

    except Exception as e:
        print(f"Dashboard error: {e}")
        flash("Error loading dashboard.", "error")
        # Variables already initialized to defaults

    if pending_count > 0:
        flash(f"You have {pending_count} pending game suggestion(s) to review.", "info")

    return render_template("admin.html", games=games, users=users, total_games=total_games, sold_games=sold_games, total_revenue=total_revenue, total_users=total_users, active_users=active_users, approved_suggestions=approved_suggestions, platforms=PLATFORMS, page=page, total_pages=total_pages, page_suggestions=page_suggestions, total_pages_suggestions=total_pages_suggestions, total_suggestions_count=total_suggestions_count, errors={}, pending_count=pending_count, pending_topup_count=pending_topup_count)

@app.route("/admin_games")
def admin_games():
    if "username" not in session or session["role"] != "admin":
        return error
    return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    try:

        game_rows = db.session.query(
            Game,
            db.func.count(Purchase.id).label('sold_count')
        ).outerjoin(Purchase, Game.id == Purchase.game_id)\
         .group_by(Game.id)\
         .order_by(Game.id)\
         .offset(offset)\
         .limit(per_page)\
         .all()

        games = []
        for row in game_rows:
            game = row[0]
            sold_count = row[1]
            game.sold_count = sold_count
            games.append(game)

        total_games_count = Game.query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

    except Exception as e:
        flash("Error loading games.", "error")
        games = []
        total_pages = 0
        page = 1

    return render_template("admin_games.html", games=games, platforms=PLATFORMS, page=page, total_pages=total_pages, errors={})

@app.route("/add_game", methods=["POST"])
def add_game():
    if "username" in session and session["role"] == "admin":
        title = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["title"].strip())
        if len(title) > 100:
            title = title[:100]
        platform = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["platform"].strip())
        if len(platform) > 50:
            platform = platform[:50]
        genre = request.form.get("genre", "Action").strip()
        price = request.form["price"].strip()

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
            price_float = float(price)
            if price_float <= 0:
                flash("Price must be a positive number.", "error")
                return redirect(url_for("admin"))
        except ValueError:
            flash("Price must be a valid number.", "error")
            return redirect(url_for("admin"))

        if 'image' not in request.files:
            flash("Image file is required.", "error")
            return redirect(url_for("admin"))

        image_file = request.files['image']
        if not image_file or image_file.filename == '':
            flash("Image file is required.", "error")
            return redirect(url_for("admin"))

        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'jfif'}
        if '.' not in image_file.filename or image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, WebP, or JFIF.", "error")
            return redirect(url_for("admin"))

        installation_filename = None
        if 'installation_file' in request.files:
            installation_file = request.files['installation_file']
            if installation_file and installation_file.filename != '':

                allowed_app_extensions = {'exe', 'msi', 'zip', 'rar', '7z', 'bat', 'cmd', 'txt'}
                if '.' in installation_file.filename and installation_file.filename.rsplit('.', 1)[1].lower() in allowed_app_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + installation_file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    installation_file.save(file_path)
                    installation_filename = filename
                else:
                    flash("Invalid installation file type. Please upload EXE, MSI, ZIP, RAR, 7Z, BAT, CMD, or TXT files.", "error")
                    return redirect(url_for("admin"))

        existing_game = Game.query.filter_by(title=title).first()
        if existing_game:
            flash("A game with this title already exists.", "error")
            return redirect(url_for("admin"))

        try:

            import uuid
            filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            image_path = os.path.join('static', 'uploads', filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)

            game = Game(title=title, platform=platform, genre=genre, price=price_float, image=filename, installation_file=installation_filename)
            db.session.add(game)
            db.session.commit()
            flash("Game added successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error adding game.", "error")
    return redirect(url_for("admin"))



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

@app.route("/user_management")
def user_management():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    try:
        total_users_count = User.query.filter(User.role.in_(['customer', 'inactive'])).count()
        total_pages = (total_users_count + per_page - 1) // per_page

        users = User.query.filter(User.status.in_(['active', 'inactive'])).order_by(User.username).offset(offset).limit(per_page).all()

        for user in users:
            total_purchases = Purchase.query.filter_by(username=user.username).count()
            user.total_purchases = total_purchases
            user.active_purchases = total_purchases

    except Exception as e:
        flash("Error loading user management.", "error")
        users = []
        total_pages = 0
        page = 1

    return render_template("user_management.html", users=users, page=page, total_pages=total_pages)

@app.route("/deactivate_user/<username>")
def deactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.status = 'inactive'
                db.session.commit()
                flash(f"User '{username}' has been deactivated.", "success")
            else:
                flash("User not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error deactivating user.", "error")
    return redirect(url_for("user_management"))

@app.route("/reactivate_user/<username>")
def reactivate_user(username):
    if "username" in session and session["role"] == "admin":
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.status = 'active'
                db.session.commit()
                flash(f"User '{username}' has been reactivated.", "success")
            else:
                flash("User not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error reactivating user.", "error")
    return redirect(url_for("user_management"))

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
            flash(f"Added ₱{credits_float:.2f} to {username}'s balance.", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            db.session.rollback()
            flash("Error adding credits.", "error")

    return render_template("add_credits.html", user=user)

@app.route("/change_logo", methods=["POST"])
def change_logo():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    if 'logo' not in request.files:
        flash("Logo file is required.", "error")
        return redirect(url_for("admin"))

    logo_file = request.files['logo']
    if not logo_file or logo_file.filename == '':
        flash("Logo file is required.", "error")
        return redirect(url_for("admin"))

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in logo_file.filename or logo_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash("Invalid logo file type. Please upload PNG, JPG, JPEG, GIF, or WebP.", "error")
        return redirect(url_for("admin"))

    if not request.form.get('confirm_logo'):
        flash("Please confirm the logo change.", "error")
        return redirect(url_for("admin"))

    try:

        import uuid
        filename = 'logo.' + logo_file.filename.rsplit('.', 1)[1].lower()
        logo_path = os.path.join('static', filename)
        os.makedirs(os.path.dirname(logo_path), exist_ok=True)
        logo_file.save(logo_path)

        old_logo_path = os.path.join('static', 'logo.png')
        if os.path.exists(old_logo_path):
            backup_path = os.path.join('static', 'logo_backup.png')
            import shutil
            shutil.copy2(old_logo_path, backup_path)

        import shutil
        shutil.move(logo_path, old_logo_path)

        flash("Logo updated successfully.", "success")
    except Exception as e:
        flash("Error updating logo.", "error")

    return redirect(url_for("admin"))

@app.route("/manage_suggestions")
def manage_suggestions():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        suggestions = GameSuggestion.query.filter_by(status='pending').order_by(GameSuggestion.date_suggested.desc()).all()
        pending_count = GameSuggestion.query.filter_by(status='pending').count()
        pending_topup_count = TopupRequest.query.filter_by(status='pending').count()
    except Exception as e:
        flash("Error loading suggestions.", "error")
        suggestions = []
        pending_count = 0
        pending_topup_count = 0

    return render_template("manage_suggestions.html", suggestions=suggestions, pending_count=pending_count, pending_topup_count=pending_topup_count)

@app.route("/approve_suggestion/<int:suggestion_id>")
def approve_suggestion(suggestion_id):
    if "username" in session and session["role"] == "admin":
        try:
            suggestion = GameSuggestion.query.get(suggestion_id)
            if suggestion:
                suggestion.status = 'approved'
                db.session.commit()

                # Add to suggester's library if not already there
                existing_user_game = UserGame.query.filter_by(
                    username=suggestion.suggested_by,
                    game_id=None,
                    title=suggestion.title,
                    platform=suggestion.platform
                ).first()

                if not existing_user_game:
                    user_game = UserGame(
                        username=suggestion.suggested_by,
                        game_id=None,
                        condition='approved',
                        title=suggestion.title,
                        platform=suggestion.platform,
                        genre=suggestion.genre
                    )
                    db.session.add(user_game)

                # Add to all active customers' libraries (excluding the suggester)
                active_customers = User.query.filter_by(role='customer', status='active').filter(User.username != suggestion.suggested_by).all()
                for customer in active_customers:
                    existing_customer_game = UserGame.query.filter_by(
                        username=customer.username,
                        game_id=None,
                        title=suggestion.title,
                        platform=suggestion.platform
                    ).first()
                    if not existing_customer_game:
                        customer_game = UserGame(
                            username=customer.username,
                            game_id=None,
                            condition='added',
                            title=suggestion.title,
                            platform=suggestion.platform,
                            genre=suggestion.genre
                        )
                        db.session.add(customer_game)

                # Create notification for the suggester
                notification = Notification(
                    username=suggestion.suggested_by,
                    message=f"Your game suggestion '{suggestion.title}' has been approved and added to the community games!"
                )
                db.session.add(notification)

                db.session.commit()

                flash("Suggestion approved successfully.", "success")
            else:
                flash("Suggestion not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error approving suggestion.", "error")
    return redirect(url_for("manage_suggestions"))

@app.route("/manage_topup_requests")
def manage_topup_requests():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        topup_requests = TopupRequest.query.filter_by(status='pending').order_by(TopupRequest.date_requested.desc()).all()
    except Exception as e:
        flash("Error loading topup requests.", "error")
        topup_requests = []

    return render_template("manage_topup_requests.html", topup_requests=topup_requests)

@app.route("/approve_topup/<int:request_id>", methods=["POST"])
def approve_topup(request_id):
    if "username" in session and session["role"] == "admin":
        try:
            topup_request = TopupRequest.query.get(request_id)
            if topup_request and topup_request.status == 'pending':
                user = User.query.filter_by(username=topup_request.username).first()
                if user:
                    user.balance += topup_request.amount
                    topup_request.status = 'approved'
                    topup_request.date_processed = datetime.utcnow()
                    topup_request.processed_by = session["username"]

                    # Create notification for the user
                    notification = Notification(
                        username=topup_request.username,
                        message=f"Your top-up request of ₱{topup_request.amount:.2f} has been approved! The amount has been added to your balance."
                    )
                    db.session.add(notification)

                    db.session.commit()
                    flash(f"Top-up request approved. Added ₱{topup_request.amount:.2f} to {topup_request.username}'s balance.", "success")
                else:
                    flash("User not found.", "error")
            else:
                flash("Top-up request not found or already processed.", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error approving top-up request: {str(e)}", "error")
    return redirect(url_for("manage_topup_requests"))

@app.route("/reject_topup/<int:request_id>", methods=["POST"])
def reject_topup(request_id):
    if "username" in session and session["role"] == "admin":
        try:
            topup_request = TopupRequest.query.get(request_id)
            if topup_request and topup_request.status == 'pending':
                topup_request.status = 'rejected'
                topup_request.date_processed = datetime.utcnow()
                topup_request.processed_by = session["username"]

                # Create notification for the user
                notification = Notification(
                    username=topup_request.username,
                    message=f"Your top-up request of ₱{topup_request.amount:.2f} has been rejected."
                )
                db.session.add(notification)

                db.session.commit()
                flash("Top-up request rejected.", "success")
            else:
                flash("Top-up request not found or already processed.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error rejecting top-up request.", "error")
    return redirect(url_for("manage_topup_requests"))

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
    return redirect(url_for("admin"))

@app.route("/delete_suggestion/<int:suggestion_id>")
def delete_suggestion(suggestion_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        suggestion = GameSuggestion.query.get(suggestion_id)
        if not suggestion or suggestion.suggested_by != session["username"]:
            flash("Suggestion not found or you don't have permission to delete it.", "error")
            return redirect(url_for("library"))

        user_games = UserGame.query.filter_by(
            username=session["username"],
            game_id=None,
            title=suggestion.title,
            platform=suggestion.platform
        ).all()

        for user_game in user_games:
            db.session.delete(user_game)

        db.session.delete(suggestion)
        db.session.commit()

        flash("Suggestion deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting suggestion.", "error")

    return redirect(url_for("library"))

@app.route("/edit_game/<int:game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        game = Game.query.get(game_id)
        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("admin"))
    except Exception as e:
        flash("Error loading game.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        title = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["title"].strip())
        if len(title) > 100:
            title = title[:100]
        platform = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["platform"].strip())
        if len(platform) > 50:
            platform = platform[:50]
        genre = request.form.get("genre", "Action").strip()
        price = request.form["price"].strip()

        if not title:
            flash("Game title cannot be empty.", "error")
            return render_template("edit_game.html", game=game)
        if len(title) > 100:
            flash("Game title must be 100 characters or less.", "error")
            return render_template("edit_game.html", game=game)
        if not platform:
            flash("Platform cannot be empty.", "error")
            return render_template("edit_game.html", game=game)
        if len(platform) > 50:
            flash("Platform must be 50 characters or less.", "error")
            return render_template("edit_game.html", game=game)
        if not genre:
            flash("Genre cannot be empty.", "error")
            return render_template("edit_game.html", game=game)

        try:
            price_float = float(price)
            if price_float < 0:
                flash("Price cannot be negative.", "error")
                return render_template("edit_game.html", game=game)
        except ValueError:
            flash("Price must be a valid number.", "error")
            return render_template("edit_game.html", game=game)

        if title != game.title:
            existing_game = Game.query.filter_by(title=title).first()
            if existing_game:
                flash("A game with this title already exists.", "error")
                return render_template("edit_game.html", game=game)

        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            if image_file:

                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'jfif'}
                if '.' not in image_file.filename or image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, WebP, or JFIF.", "error")
                    return render_template("edit_game.html", game=game)

                import uuid
                filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                image_path = os.path.join('static', 'uploads', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
                game.image = filename

        if 'installation_file' in request.files and request.files['installation_file'].filename != '':
            installation_file = request.files['installation_file']
            if installation_file:

                allowed_app_extensions = {'exe', 'msi', 'zip', 'rar', '7z', 'bat', 'cmd', 'txt'}
                if '.' in installation_file.filename and installation_file.filename.rsplit('.', 1)[1].lower() in allowed_app_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + installation_file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    installation_file.save(file_path)
                    game.installation_file = filename
                else:
                    flash("Invalid installation file type. Please upload EXE, MSI, ZIP, RAR, 7Z, BAT, CMD, or TXT files.", "error")
                    return render_template("edit_game.html", game=game)

        try:
            game.title = title
            game.platform = platform
            game.genre = genre
            game.price = price_float
            db.session.commit()
            flash("Game updated successfully.", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating game.", "error")

    return render_template("edit_game.html", game=game, platforms=PLATFORMS, errors={})

@app.route("/edit_suggestion/<int:suggestion_id>", methods=["GET", "POST"])
def edit_suggestion(suggestion_id):
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        suggestion = GameSuggestion.query.get(suggestion_id)
        if not suggestion:
            flash("Suggestion not found.", "error")
            return redirect(url_for("admin"))
    except Exception as e:
        flash("Error loading suggestion.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        title = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["title"].strip())
        if len(title) > 100:
            title = title[:100]
        platform = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["platform"].strip())
        if len(platform) > 50:
            platform = platform[:50]
        genre = request.form.get("genre", "Action").strip()
        description = re.sub(r'[^\w\s\-\.\(\)\,\!\?\:\;\'\"\n\r]', '', request.form.get("description", "").strip())
        if len(description) > 1000:
            description = description[:1000]

        if not title:
            flash("Game title cannot be empty.", "error")
            return render_template("edit_suggestion.html", suggestion=suggestion)
        if len(title) > 100:
            flash("Game title must be 100 characters or less.", "error")
            return render_template("edit_suggestion.html", suggestion=suggestion)
        if not platform:
            flash("Platform cannot be empty.", "error")
            return render_template("edit_suggestion.html", suggestion=suggestion)
        if len(platform) > 50:
            flash("Platform must be 50 characters or less.", "error")
            return render_template("edit_suggestion.html", suggestion=suggestion)
        if not genre:
            flash("Genre cannot be empty.", "error")
            return render_template("edit_suggestion.html", suggestion=suggestion)

        if title != suggestion.title or platform != suggestion.platform:
            existing_suggestion = GameSuggestion.query.filter_by(title=title, platform=platform).first()
            if existing_suggestion and existing_suggestion.id != suggestion_id:
                flash("A suggestion for this game already exists.", "error")
                return render_template("edit_suggestion.html", suggestion=suggestion)

        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            if image_file:

                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'jfif'}

                if '.' not in image_file.filename or image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:

                    flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, WebP, or JFIF.", "error")
                    return render_template("edit_suggestion.html", suggestion=suggestion)

                import uuid
                filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                image_path = os.path.join('static', 'uploads', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)

                with open(os.path.join('static', 'uploads', f'suggestion_{suggestion.id}.txt'), 'w') as f:
                    f.write(filename)

        try:
            suggestion.title = title
            suggestion.platform = platform
            suggestion.genre = genre
            suggestion.description = description
            db.session.commit()
            flash("Suggestion updated successfully.", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating suggestion.", "error")

    return render_template("edit_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

@app.route("/customer")
def customer():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    if len(search) > 100:
        search = search[:100]
    platform_filter = request.args.get('platform', '')
    if len(platform_filter) > 50:
        platform_filter = platform_filter[:50]
    genre_filter = request.args.get('genre', '')
    if len(genre_filter) > 50:
        genre_filter = genre_filter[:50]

    try:

        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0

        official_query = Game.query

        if search:
            official_query = official_query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            official_query = official_query.filter_by(platform=platform_filter)

        if genre_filter:
            official_query = official_query.filter_by(genre=genre_filter)

        total_games_count = official_query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        official_games = official_query.order_by(Game.id).offset(offset).limit(per_page).all()

        for game in official_games:
            game.is_owned = UserGame.query.filter_by(username=session["username"], game_id=game.id).first() is not None
            # Check if image file exists, else set to None for fallback
            if game.image and not os.path.exists(os.path.join('static', 'uploads', game.image)):
                game.image = None

        used_query = UserGame.query.filter_by(listed_for_sale=True).filter(UserGame.game_id.isnot(None)).join(Game)

        if search:
            used_query = used_query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            used_query = used_query.filter(Game.platform == platform_filter)

        if genre_filter:
            used_query = used_query.filter(Game.genre == genre_filter)

        user_games = used_query.order_by(UserGame.purchase_date).all()

        # Check image existence for used games
        for user_game in user_games:
            if user_game.game.image and not os.path.exists(os.path.join('static', 'uploads', user_game.game.image)):
                user_game.game.image = None

        genres = [g[0] for g in db.session.query(Game.genre).distinct().all()]
        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]

        community_query = GameSuggestion.query.filter_by(status='approved')

        if search:
            community_query = community_query.filter(GameSuggestion.title.ilike(f"%{search}%"))

        if platform_filter:
            community_query = community_query.filter_by(platform=platform_filter)

        if genre_filter:
            community_query = community_query.filter_by(genre=genre_filter)

        approved_suggestions = community_query.order_by(GameSuggestion.date_suggested.desc()).all()

        # Check image existence for community games
        for suggestion in approved_suggestions:
            if suggestion.image and not os.path.exists(os.path.join('static', 'uploads', suggestion.image)):
                suggestion.image = None

    except Exception as e:
        flash(f"Error loading games: {re.escape(str(e))}", "error")
        official_games = []
        user_games = []
        approved_suggestions = []
        platforms = []
        genres = []
        total_pages = 0
        page = 1
        user_balance = 0.0
        search = ''
        platform_filter = ''
        genre_filter = ''

    # Check for unread notifications
    unread_notifications_count = 0
    try:
        unread_notifications_count = Notification.query.filter_by(username=session["username"], is_read=False).count()
        if unread_notifications_count > 0:
            flash(f"You have {unread_notifications_count} unread notification(s).", "info")
    except Exception as e:
        pass

    return render_template("customer.html", games=official_games, user_games=user_games, approved_suggestions=approved_suggestions, platforms=platforms, genres=genres, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages, user_balance=user_balance, unread_notifications_count=unread_notifications_count)

@app.route("/buy/<int:game_id>")
def buy(game_id):
    if "username" in session and session["role"] == "customer":
        try:
            user = User.query.filter_by(username=session["username"]).first()
            game = Game.query.get(game_id)
            if game:
                return redirect(url_for('confirm_purchase', game_id=game_id, condition='new'))
            else:

                suggestion = GameSuggestion.query.get(game_id)
                if suggestion and suggestion.status == 'approved':

                    return redirect(url_for('confirm_purchase', game_id=game_id, condition='free'))
                else:
                    flash("Game not found.", "error")
        except Exception as e:
            db.session.rollback()
            flash("Error purchasing game.", "error")
    return redirect(url_for("customer"))

@app.route("/add_to_library/<int:game_id>")
def add_to_library(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:

        suggestion = GameSuggestion.query.get(game_id)
        if not suggestion or suggestion.status != 'approved':
            flash("Game not found or not available.", "error")
            return redirect(url_for("customer"))

        existing = UserGame.query.filter_by(username=session["username"], game_id=None, title=suggestion.title, platform=suggestion.platform).first()
        if existing:
            flash("This game is already in your library.", "info")
            return redirect(url_for("customer"))

        user_game = UserGame(username=session["username"], game_id=None, condition='added',
                           title=suggestion.title, platform=suggestion.platform, genre=suggestion.genre)
        db.session.add(user_game)
        db.session.commit()
        flash("Game added to your library!", "success")

    except Exception as e:
        db.session.rollback()
        flash("Error adding game to library.", "error")

    return redirect(url_for("customer"))

@app.route("/confirm_purchase/<int:game_id>")
def confirm_purchase(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    condition = request.args.get('condition', 'new')

    try:
        user = User.query.filter_by(username=session["username"]).first()

        if condition == 'free':

            suggestion = GameSuggestion.query.get(game_id)
            if not suggestion or suggestion.status != 'approved':
                flash("Game not found.", "error")
                return redirect(url_for("customer"))

            class MockGame:
                def __init__(self, suggestion):
                    self.id = suggestion.id
                    self.title = suggestion.title
                    self.platform = suggestion.platform
                    self.genre = suggestion.genre
                    self.image = f"static/uploads/{suggestion.image}" if suggestion.image else "static/logo.png"

            game = MockGame(suggestion)
            price = suggestion.price
        else:
            game = Game.query.get(game_id)

            if not game:
                flash("Game not found.", "error")
                return redirect(url_for("customer"))

            if condition == 'new':
                price = game.price
            else:

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

@app.route("/process_purchase/<int:game_id>")
def process_purchase(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    condition = request.args.get('condition', 'new')

    try:
        user = User.query.filter_by(username=session["username"]).first()

        if condition == 'free':

            suggestion = GameSuggestion.query.get(game_id)
            if not suggestion or suggestion.status != 'approved':
                flash("Game not found.", "error")
                return redirect(url_for("customer"))

            user_game = UserGame(username=session["username"], game_id=None, condition='new',
                               title=suggestion.title, platform=suggestion.platform, genre=suggestion.genre)
            db.session.add(user_game)
            db.session.commit()
            flash("Community game added to your library!", "success")
            return redirect(url_for("customer"))
        else:
            game = Game.query.get(game_id)

            if not game:
                flash("Game not found.", "error")
                return redirect(url_for("customer"))

            if condition == 'new':
                price = game.price
            else:

                user_game = UserGame.query.filter_by(game_id=game_id, listed_for_sale=True).first()
                if not user_game:
                    flash("Game not found for sale.", "error")
                    return redirect(url_for("marketplace"))
                price = user_game.sale_price

            has_balance, current_balance = check_user_balance(session["username"], price)
            if not has_balance:
                flash(f"Insufficient balance. You need ₱{price:.2f} but only have ₱{current_balance:.2f}.", "error")
                return redirect(url_for("confirm_purchase", game_id=game_id, condition=condition))

            if not deduct_user_balance(session["username"], price):
                flash("Error processing payment.", "error")
                return redirect(url_for("confirm_purchase", game_id=game_id, condition=condition))

            if condition == 'new':

                purchase = Purchase(username=session["username"], game_id=game_id, price_paid=price)
                db.session.add(purchase)

                user_game = UserGame(username=session["username"], game_id=game_id, condition='new')
                db.session.add(user_game)

            else:

                sale_user_game = UserGame.query.filter_by(game_id=game_id, listed_for_sale=True).first()

                purchase = Purchase(username=session["username"], game_id=game_id, condition='used', price_paid=price, sale_username=sale_user_game.username)
                db.session.add(purchase)

                sale_user_game.username = session["username"]
                sale_user_game.condition = 'used'
                sale_user_game.listed_for_sale = False
                sale_user_game.sale_price = None
                sale_user_game.purchase_date = datetime.utcnow()

            db.session.commit()

            # Create notification for the buyer
            notification = Notification(
                username=session["username"],
                message=f"You have successfully purchased '{game.title}' for ₱{price:.2f}."
            )
            db.session.add(notification)
            db.session.commit()

            flash("Game purchased successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash("Error processing purchase.", "error")

    return redirect(url_for("customer"))

@app.route("/profile")
def profile():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        purchases = Purchase.query.filter_by(username=session["username"]).join(Game).order_by(Purchase.purchase_date.desc()).all()
    except Exception as e:
        purchases = []

    try:
        ratings = Rating.query.filter_by(username=session["username"]).join(Game).order_by(Rating.date.desc()).all()
    except Exception as e:
        ratings = []

    try:
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0
    except Exception as e:
        user_balance = 0.0

    return render_template("profile.html", purchases=purchases, ratings=ratings, user_balance=user_balance)

@app.route("/transactions")
def transactions():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0
    except Exception as e:
        user_balance = 0.0

    # Get purchase transactions
    purchase_transactions = []
    try:
        purchases = Purchase.query.filter_by(username=session["username"]).join(Game).order_by(Purchase.purchase_date.desc()).all()
        for purchase in purchases:
            purchase_transactions.append({
                'date': purchase.purchase_date,
                'type': 'Purchase',
                'description': f'Purchased {purchase.game.title}',
                'amount': -purchase.price_paid,
                'status': 'Completed'
            })
    except Exception as e:
        pass

    # Get topup transactions
    topup_transactions = []
    try:
        topups = TopupRequest.query.filter_by(username=session["username"], status='approved').order_by(TopupRequest.date_processed.desc()).all()
        for topup in topups:
            topup_transactions.append({
                'date': topup.date_processed,
                'type': 'Top Up',
                'description': f'Top up via {topup.payment_method}',
                'amount': topup.amount,
                'status': 'Completed'
            })
    except Exception as e:
        pass

    # Combine and sort transactions
    all_transactions = purchase_transactions + topup_transactions
    all_transactions.sort(key=lambda x: x['date'], reverse=True)

    return render_template("transactions.html", transactions=all_transactions, user_balance=user_balance)

@app.route("/topup", methods=["GET", "POST"])
def topup():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        user = User.query.filter_by(username=session["username"]).first()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("customer"))
    except Exception as e:
        flash("Error loading user.", "error")
        return redirect(url_for("customer"))

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        reference_number = request.form.get("reference_number", "").strip()

        if not amount or not payment_method or not reference_number:
            flash("Amount, payment method, and reference number are required.", "error")
            return render_template("topup.html", user_balance=user.balance)

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                flash("Top-up amount must be positive.", "error")
                return render_template("topup.html", user_balance=user.balance)
            if amount_float > 50000:
                flash("Maximum top-up amount is ₱50,000.", "error")
                return render_template("topup.html", user_balance=user.balance)
        except ValueError:
            flash("Invalid amount.", "error")
            return render_template("topup.html", user_balance=user.balance)

        try:
            screenshot_filename = None
            if 'screenshot' in request.files:
                screenshot_file = request.files['screenshot']
                if screenshot_file and screenshot_file.filename != '':
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if '.' in screenshot_file.filename and screenshot_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        import uuid
                        filename = str(uuid.uuid4()) + '.' + screenshot_file.filename.rsplit('.', 1)[1].lower()
                        screenshot_path = os.path.join('static', 'uploads', filename)
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        screenshot_file.save(screenshot_path)
                        screenshot_filename = filename

            # Create topup request instead of directly adding to balance
            topup_request = TopupRequest(
                username=session["username"],
                amount=amount_float,
                payment_method=payment_method,
                reference_number=reference_number,
                screenshot=screenshot_filename,
                status='pending'
            )
            db.session.add(topup_request)
            db.session.commit()
            flash("Top-up request submitted successfully! Please wait for admin approval.", "success")
            return redirect(url_for("customer"))
        except Exception as e:
            db.session.rollback()
            flash("Error submitting top-up request.", "error")
            return render_template("topup.html", user_balance=user.balance, amount=request.form.get("amount"), payment_method=request.form.get("payment_method"), reference_number=request.form.get("reference_number"))

    return render_template("topup.html", user_balance=user.balance)

@app.route("/admin_settings", methods=["GET", "POST"])
def admin_settings():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    try:
        pending_count = GameSuggestion.query.filter_by(status='pending').count()
    except Exception as e:
        pending_count = 0

    if request.method == "POST" and "current_password" in request.form:
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        user = User.query.filter_by(username=session["username"]).first()
        if not user or not user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("admin_settings.html", pending_count=pending_count)

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("admin_settings.html", pending_count=pending_count)

        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, "error")
            return render_template("admin_settings.html", pending_count=pending_count)

        try:
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating password.", "error")

    return render_template("admin_settings.html", pending_count=pending_count)

@app.route("/update_system_settings", methods=["POST"])
def update_system_settings():
    if "username" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    site_title = request.form.get("site_title", "").strip()
    max_topup = request.form.get("max_topup", "").strip()
    maintenance_mode = request.form.get("maintenance_mode") == "1"

    if not site_title:
        flash("Site title cannot be empty.", "error")
        return redirect(url_for("admin_settings"))

    try:
        max_topup_int = int(max_topup)
        if max_topup_int < 1000 or max_topup_int > 100000:
            flash("Maximum top-up must be between ₱1,000 and ₱100,000.", "error")
            return redirect(url_for("admin_settings"))
    except ValueError:
        flash("Invalid maximum top-up amount.", "error")
        return redirect(url_for("admin_settings"))

    flash("System settings updated successfully.", "success")
    return redirect(url_for("admin_settings"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0
    except Exception as e:
        user_balance = 0.0

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        user = User.query.filter_by(username=session["username"]).first()
        if not user or not user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("settings.html", user_balance=user_balance)

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("settings.html", user_balance=user_balance)

        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, "error")
            return render_template("settings.html", user_balance=user_balance)

        try:
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating password.", "error")

    return render_template("settings.html", user_balance=user_balance)

@app.route("/library")
def library():
    if "username" not in session:
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    if len(search) > 100:
        search = search[:100]

    user_balance = 0.0
    try:
        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0

        # Get purchased games with pagination and search
        purchased_query = UserGame.query.filter_by(username=session["username"]).filter(UserGame.game_id.isnot(None)).join(Game)

        if search:
            purchased_query = purchased_query.filter(Game.title.ilike(f"%{search}%"))

        total_purchased_count = purchased_query.count()
        total_pages = (total_purchased_count + per_page - 1) // per_page

        purchased_games = purchased_query.order_by(UserGame.purchase_date.desc()).offset(offset).limit(per_page).all()

        created_games = UserGame.query.filter_by(username=session["username"]).filter(UserGame.game_id.is_(None)).order_by(UserGame.purchase_date.desc()).all()

        for user_game in created_games:
            user_game.suggestion = GameSuggestion.query.filter_by(
                title=user_game.title,
                platform=user_game.platform,
                suggested_by=session["username"]
            ).first()

        # Filter out user_games without suggestions to prevent errors
        created_games = [ug for ug in created_games if ug.suggestion is not None]
    except Exception as e:
        purchased_games = []
        created_games = []
        user_balance = 0.0
        total_pages = 0
        page = 1
        search = ''

    return render_template("library.html", purchased_games=purchased_games, created_games=created_games, user_balance=user_balance, page=page, total_pages=total_pages, search=search)

@app.route("/edit_user_suggestion/<int:suggestion_id>", methods=["GET", "POST"])
def edit_user_suggestion(suggestion_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        suggestion = GameSuggestion.query.get(suggestion_id)
        if not suggestion or suggestion.suggested_by != session["username"]:
            flash("Suggestion not found or you don't have permission to edit it.", "error")
            return redirect(url_for("library"))
    except Exception as e:
        flash("Error loading suggestion.", "error")
        return redirect(url_for("library"))

    if request.method == "POST":
        title = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["title"].strip())
        if len(title) > 100:
            title = title[:100]
        platform = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["platform"].strip())
        if len(platform) > 50:
            platform = platform[:50]
        genre = request.form.get("genre", "Action").strip()
        price = request.form.get("price", "").strip()
        description = re.sub(r'[^\w\s\-\.\(\)\,\!\?\:\;\'\"\n\r]', '', request.form.get("description", "").strip())
        if len(description) > 1000:
            description = description[:1000]
        installation_instructions = request.form.get("installation_instructions", "").strip()

        if not title:
            flash("Game title cannot be empty.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)
        if len(title) > 100:
            flash("Game title must be 100 characters or less.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)
        if not platform:
            flash("Platform cannot be empty.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)
        if len(platform) > 50:
            flash("Platform must be 50 characters or less.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)
        if not genre:
            flash("Genre cannot be empty.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)
        if not installation_instructions:
            flash("Installation instructions are required.", "error")
            return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

        if suggestion.status == 'pending' and (title != suggestion.title or platform != suggestion.platform):
            existing_suggestion = GameSuggestion.query.filter_by(title=title, platform=platform).first()
            if existing_suggestion and existing_suggestion.id != suggestion_id:
                flash("A suggestion for this game already exists.", "error")
                return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            if image_file:

                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                    image_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image_file.save(image_path)
                    suggestion.image = filename
                else:
                    flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, or WebP.", "error")
                    return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

        if 'installation_file' in request.files and request.files['installation_file'].filename != '':
            installation_file = request.files['installation_file']
            if installation_file:

                allowed_extensions = {'txt', 'exe', 'msi', 'zip', 'rar', '7z', 'bat', 'cmd'}
                if '.' in installation_file.filename and installation_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + installation_file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    installation_file.save(file_path)
                    suggestion.installation_file = filename
                else:
                    flash("Invalid installation file type. Please upload TXT, EXE, MSI, ZIP, RAR, 7Z, BAT, or CMD files.", "error")
                    return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

        try:

            # Store old values to find user_game
            old_title = suggestion.title
            old_platform = suggestion.platform

            # Find user_game using old values
            user_game = UserGame.query.filter_by(
                username=session["username"],
                game_id=None,
                title=old_title,
                platform=old_platform
            ).first()

            if not user_game:
                flash("Associated user game not found. Please contact support.", "error")
                return redirect(url_for("library"))

            # Update user_game to new values
            user_game.title = title
            user_game.platform = platform
            user_game.genre = genre

            # Update suggestion to new values
            suggestion.title = title
            suggestion.platform = platform
            suggestion.genre = genre
            suggestion.description = description
            suggestion.installation_instructions = installation_instructions

            changes_made = (old_title != title or old_platform != platform or suggestion.genre != genre or suggestion.description != description or suggestion.installation_instructions != installation_instructions)

            if suggestion.status == 'approved':
                sale_price = request.form.get("sale_price", "").strip()
                if sale_price:
                    try:
                        price_float = float(sale_price)
                        if price_float > 0:
                            if suggestion.price != price_float:
                                changes_made = True
                            suggestion.price = price_float
                        else:
                            if suggestion.price != 0.0:
                                changes_made = True
                            suggestion.price = 0.0
                    except ValueError:
                        if suggestion.price != 0.0:
                            changes_made = True
                        suggestion.price = 0.0
                else:
                    if suggestion.price != 0.0:
                        changes_made = True
                    suggestion.price = 0.0

            if changes_made:
                suggestion.last_updated = datetime.utcnow()
                suggestion.updated_by = session["username"]

            db.session.commit()

            flash("Suggestion updated successfully!", "success")
            return redirect(url_for("library"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating suggestion: {re.escape(str(e))}", "error")

    return render_template("edit_user_suggestion.html", suggestion=suggestion, platforms=PLATFORMS)

@app.route("/marketplace")
def marketplace():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    if len(search) > 100:
        search = search[:100]
    platform_filter = request.args.get('platform', '')
    if len(platform_filter) > 50:
        platform_filter = platform_filter[:50]
    genre_filter = request.args.get('genre', '')
    if len(genre_filter) > 50:
        genre_filter = genre_filter[:50]

    try:

        query = UserGame.query.filter_by(listed_for_sale=True).join(Game)

        if search:
            query = query.filter(Game.title.ilike(f"%{search}%"))

        if platform_filter:
            query = query.filter(Game.platform == platform_filter)

        if genre_filter:
            query = query.filter(Game.genre == genre_filter)

        total_games_count = query.count()
        total_pages = (total_games_count + per_page - 1) // per_page

        user_games = query.order_by(UserGame.purchase_date).offset(offset).limit(per_page).all()

        approved_query = GameSuggestion.query.filter_by(status='approved')

        if search:
            approved_query = approved_query.filter(GameSuggestion.title.ilike(f"%{search}%"))

        if platform_filter:
            approved_query = approved_query.filter_by(platform=platform_filter)

        if genre_filter:
            approved_query = approved_query.filter_by(genre=genre_filter)

        approved_suggestions = approved_query.order_by(GameSuggestion.date_suggested.desc()).all()

        platforms = [p[0] for p in db.session.query(Game.platform).distinct().all()]
    except Exception as e:
        flash("Error loading marketplace.", "error")
        user_games = []
        approved_suggestions = []
        platforms = []
        total_pages = 0
        page = 1

    return render_template("marketplace.html", user_games=user_games, approved_suggestions=approved_suggestions, platforms=platforms, search=search, platform_filter=platform_filter, genre_filter=genre_filter, page=page, total_pages=total_pages)

@app.route("/sale/<int:user_game_id>", methods=["GET", "POST"])
def sale(user_game_id):
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

            return redirect(url_for('confirm_purchase', game_id=user_game.game_id, condition='used'))
        except Exception as e:
            flash("Error loading game.", "error")
    return redirect(url_for("marketplace"))

@app.route("/suggest_game", methods=["GET", "POST"])
def suggest_game():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["title"].strip())
        if len(title) > 100:
            title = title[:100]
        platform = re.sub(r'[^\w\s\-\.\(\)]', '', request.form["platform"].strip())
        if len(platform) > 50:
            platform = platform[:50]
        genre = request.form.get("genre", "Action").strip()
        price = request.form.get("price", "").strip()
        description = re.sub(r'[^\w\s\-\.\(\)\,\!\?\:\;\'\"\n\r]', '', request.form.get("description", "").strip())
        if len(description) > 1000:
            description = description[:1000]
        installation_instructions = request.form.get("installation_instructions", "").strip()

        price_float = 0.0
        if price:
            try:
                price_float = float(price)
                if price_float < 0:
                    price_float = 0.0
            except ValueError:
                price_float = 0.0

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
        if not installation_instructions:
            flash("Installation instructions are required.", "error")
            return render_template("suggest_game.html")

        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':

                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                    image_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image_file.save(image_path)
                    image_filename = filename
                else:
                    flash("Invalid image file type. Please upload PNG, JPG, JPEG, GIF, or WebP.", "error")
                    return render_template("suggest_game.html")

        installation_filename = None
        if 'installation_file' in request.files:
            installation_file = request.files['installation_file']
            if installation_file and installation_file.filename != '':

                allowed_extensions = {'txt', 'exe', 'msi', 'zip', 'rar', '7z', 'bat', 'cmd'}
                if '.' in installation_file.filename and installation_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

                    import uuid
                    filename = str(uuid.uuid4()) + '.' + installation_file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join('static', 'uploads', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    installation_file.save(file_path)
                    installation_filename = filename
                else:
                    flash("Invalid installation file type. Please upload TXT, EXE, MSI, ZIP, RAR, 7Z, BAT, or CMD files.", "error")
                    return render_template("suggest_game.html")

        existing_suggestion = GameSuggestion.query.filter_by(title=title, platform=platform).first()
        if existing_suggestion:
            flash("A suggestion for this game already exists.", "error")
            return render_template("suggest_game.html")

        try:
            suggestion = GameSuggestion(
                title=title,
                platform=platform,
                genre=genre,
                price=price_float,
                description=description,
                installation_instructions=installation_instructions,
                installation_file=installation_filename,
                suggested_by=session["username"],
                status='pending'
            )
            db.session.add(suggestion)
            db.session.commit()

            if image_filename:
                suggestion.image = image_filename
                db.session.commit()

            user_game = UserGame(username=session["username"], game_id=None, condition='suggested',
                               title=suggestion.title, platform=suggestion.platform, genre=suggestion.genre)
            db.session.add(user_game)
            db.session.commit()

            flash("Game suggestion submitted successfully!", "success")
            return redirect(url_for("customer"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting suggestion: {re.escape(str(e))}", "error")

    return render_template("suggest_game.html")

@app.route("/rate_game/<int:game_id>", methods=["GET", "POST"])
def rate_game(game_id):
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    try:
        game = Game.query.get(game_id)
        if not game:
            flash("Game not found.", "error")
            return redirect(url_for("customer"))

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

            existing = Rating.query.filter_by(username=session["username"], game_id=game_id).first()

            if existing:

                existing.rating = int(rating)
                existing.review = review
                existing.date = datetime.utcnow()
            else:

                new_rating = Rating(username=session["username"], game_id=game_id, rating=int(rating), review=review)
                db.session.add(new_rating)

            db.session.commit()
            flash("Rating submitted successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            db.session.rollback()
            flash("Error submitting rating.", "error")

    return render_template("rate_game.html", game=game)

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

        return render_template("forgot_password.html", username=username, show_reset=True)

    if request.method == "POST" and "new_password" in request.form:
        username = request.form["username"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("forgot_password.html", username=username, show_reset=True)

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

@app.route("/api/search")
def api_search():
    query = request.args.get('q', '').strip()
    if not query or len(query) > 100:
        return jsonify({'success': False, 'results': []})
    if len(query) < 2:
        return jsonify({'success': False, 'results': []})
    try:
        games = Game.query.filter(Game.title.ilike(f"%{query}%")).limit(10).all()
        results = []
        for game in games:
            results.append({
                'id': game.id,
                'title': game.title,
                'platform': game.platform,
                'genre': game.genre,
                'price': float(game.price),
                'image': f'/static/uploads/{game.image}' if game.image else '/static/logo.png'
            })
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/game_ratings/<int:game_id>")
def api_game_ratings(game_id):
    try:
        ratings = Rating.query.filter_by(game_id=game_id).order_by(Rating.date.desc()).all()
        if ratings:
            total_rating = sum(r.rating for r in ratings)
            average_rating = total_rating / len(ratings)
            total_ratings = len(ratings)
        else:
            average_rating = 0.0
            total_ratings = 0
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                'username': rating.username,
                'rating': rating.rating,
                'review': rating.review,
                'date': rating.date.isoformat()
            })
        return jsonify({
            'success': True,
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'ratings': ratings_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/cart/add", methods=["POST"])
def api_add_to_cart():
    if "username" not in session or session["role"] != "customer":
        return jsonify({'success': False, 'message': 'Not logged in'})
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        if not game_id:
            return jsonify({'success': False, 'message': 'Game ID required'})
        game = Game.query.get(game_id)
        if not game:
            return jsonify({'success': False, 'message': 'Game not available'})
        return jsonify({'success': True, 'message': 'Added to cart'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/cart/count")
def api_cart_count():
    if "username" not in session or session["role"] != "customer":
        return jsonify({'count': 0})
    return jsonify({'count': 0})

@app.route("/api/notifications")
def api_notifications():
    if "username" not in session or session["role"] != "customer":
        return jsonify({'success': False, 'message': 'Not logged in'})

    try:
        notifications = Notification.query.filter_by(username=session["username"], is_read=False).order_by(Notification.date_created.desc()).all()
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'date_created': notification.date_created.isoformat()
            })
        return jsonify({'success': True, 'notifications': notifications_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/notifications")
def notifications():
    if "username" not in session or session["role"] != "customer":
        return redirect(url_for("login"))

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    try:
        total_notifications = Notification.query.filter_by(username=session["username"]).count()
        total_pages = (total_notifications + per_page - 1) // per_page

        notifications = Notification.query.filter_by(username=session["username"]).order_by(Notification.date_created.desc()).offset(offset).limit(per_page).all()

        user = User.query.filter_by(username=session["username"]).first()
        user_balance = user.balance if user else 0.0
    except Exception as e:
        notifications = []
        total_pages = 0
        user_balance = 0.0

    return render_template("notifications.html", notifications=notifications, page=page, total_pages=total_pages, user_balance=user_balance)

@app.route("/api/notifications/mark_read/<int:notification_id>", methods=["POST"])
def api_mark_notification_read(notification_id):
    if "username" not in session or session["role"] != "customer":
        return jsonify({'success': False, 'message': 'Not logged in'})

    try:
        notification = Notification.query.get(notification_id)
        if notification and notification.username == session["username"]:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Notification not found'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route("/health")
def health_check():

    try:

        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.after_request
def add_header(response):

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'

    if request.endpoint in ['static']:

        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:

        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))