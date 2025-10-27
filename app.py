from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

books = []  # temporary book storage

@app.route('/')
def home():
    return render_template('add_book.html')  # <-- your HTML file here

@app.route('/get_books')
def get_books():
    return jsonify(books)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    if title and author:
        books.append({'title': title, 'author': author})
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Missing fields'})

@app.route('/remove_book', methods=['POST'])
def remove_book():
    title = request.form.get('title')
    global books
    books = [b for b in books if b['title'] != title]
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
