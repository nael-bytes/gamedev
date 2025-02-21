from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from db import app, mysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password=None):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        return User(user[0], user[1], user[2]) if user else None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies")
    movies = cur.fetchall()
    cur.close()
    return render_template('index.html', movies=movies)

@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        director = request.form['director']
        year = request.form['year'][:4]  # Extract the year from the date (YYYY-MM-DD)
        rating = request.form['rating']  # Get the rating value

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO movies (title, director, year, rating) VALUES (%s, %s, %s, %s)", (title, director, year, rating))
        mysql.connection.commit()
        cur.close()

        flash('Movie added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_movie.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('account'))  # Redirect to account page if already logged in
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.check_password_hash(user[2], password):
            login_user(User(user[0], user[1]))
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        # Check if new passwords match
        if new_password != confirm_new_password:
            flash('New passwords do not match!', 'danger')
            return redirect('/account')

        # Verify the current password
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (current_user.username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[2], current_password):  # user[2] is password column
            # Hash the new password and update it in the database
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_password, current_user.username))
            mysql.connection.commit()
            flash('Password updated successfully!', 'success')
        else:
            flash('Invalid current password!', 'danger')

        cursor.close()

    return render_template('account.html')



@app.route('/movies', methods=['GET'])
def get_movies():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies")
    movies = cur.fetchall()
    cur.close()

    movies = [
        {"id": movie[0], "title": movie[1], "director": movie[2], "year": movie[3]}
        for movie in movies
    ]
    return jsonify(movies)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
