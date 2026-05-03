from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import or_

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    author = db.Column(db.String(200))
    issued = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    fine_per_day = db.Column(db.Integer, default=5)

    def is_overdue(self):
        return self.due_date and datetime.now() > self.due_date

    def calculate_fine(self):
        if self.is_overdue():
            days_late = (datetime.now() - self.due_date).days
            return days_late * self.fine_per_day
        return 0

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('search', '')

    query = Book.query

    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f"%{search_query}%"),
                Book.author.ilike(f"%{search_query}%")
            )
        )

    if filter_type == 'issued':
        query = query.filter_by(issued=True)
    elif filter_type == 'available':
        query = query.filter_by(issued=False)

    books = query.all()

    total = Book.query.count()
    issued = Book.query.filter_by(issued=True).count()
    available = Book.query.filter_by(issued=False).count()
    overdue = sum(1 for b in Book.query.all() if b.is_overdue())

    return render_template(
        'index.html',
        books=books,
        current_filter=filter_type,
        search_query=search_query,
        total=total,
        issued=issued,
        available=available,
        overdue=overdue
    )

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book = Book(
            title=request.form['title'],
            author=request.form['author']
        )
        db.session.add(book)
        db.session.commit()
        return redirect('/')
    return render_template('add.html')

@app.route('/issue/<int:id>', methods=['POST'])
def issue_book(id):
    book = Book.query.get(id)

    days = int(request.form['days'])
    fine = int(request.form['fine'])

    book.issued = True
    book.due_date = datetime.now() + timedelta(days=days)
    book.fine_per_day = fine

    db.session.commit()
    return redirect('/')

@app.route('/reissue/<int:id>')
def reissue_book(id):
    book = Book.query.get(id)
    if book.due_date:
        book.due_date += timedelta(days=7)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_book(id):
    book = Book.query.get(id)
    db.session.delete(book)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)