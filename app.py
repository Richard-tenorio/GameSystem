from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'library_secret_key'

# Simple in-memory data
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "student": {"password": "student123", "role": "student"}
}

books = [
    {"title": "Python Basics", "author": "John Doe", "copies": 3},
    {"title": "Flask Guide", "author": "Jane Smith", "copies": 2}
]

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = users.get(username)
    if user and user["password"] == password:
        session["user"] = username
        session["role"] = user["role"]
        if user["role"] == "admin":
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('student_page'))
    return render_template('login.html', error="Invalid credentials")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_page():
    if session.get("role") != "admin":
        return redirect(url_for('login'))
    return render_template('admin.html', books=books)

@app.route('/student')
def student_page():
    if session.get("role") != "student":
        return redirect(url_for('login'))
    return render_template('student.html', books=books)

# ----- Admin Features -----
@app.route('/add_book', methods=['POST'])
def add_book():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"})
    title = request.form.get('title')
    author = request.form.get('author')
    copies = int(request.form.get('copies', 1))
    books.append({"title": title, "author": author, "copies": copies})
    return jsonify({"success": True})

@app.route('/remove_book', methods=['POST'])
def remove_book():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"})
    title = request.form.get('title')
    global books
    books = [b for b in books if b["title"] != title]
    return jsonify({"success": True})

# ----- Student Features -----
@app.route('/borrow_book', methods=['POST'])
def borrow_book():
    title = request.form.get('title')
    for b in books:
        if b["title"] == title and b["copies"] > 0:
            b["copies"] -= 1
            return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/return_book', methods=['POST'])
def return_book():
    title = request.form.get('title')
    for b in books:
        if b["title"] == title:
            b["copies"] += 1
            return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/get_books')
def get_books():
    return jsonify(books)

if __name__ == '__main__':
    app.run(debug=True)
