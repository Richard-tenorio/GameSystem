from flask import Flask, render_template, request, redirect

app = Flask(__name__)

books = []  # temporary storage

@app.route('/')
def home():
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        books.append({'title': title, 'author': author})
        return redirect('/')
    return render_template('add_book.html')

if __name__ == '__main__':
    app.run(debug=True)
