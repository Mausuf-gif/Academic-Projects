from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from tutor_finder.app import app, db
from tutor_finder.models import User, Message, Feedback
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'tutor':
                return redirect(url_for('tutor_dashboard'))
        else:
            flash('Login failed. Check email/password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/tutor_dashboard')
@login_required
def tutor_dashboard():
    return render_template('tutor_dashboard.html')

@app.route('/admin_panel')
@login_required
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        content = request.form['content']
        feedback = Feedback(user_id=current_user.id, content=content)
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted!', 'success')
        return redirect(url_for('home'))
    return render_template('feedback.html')

@app.route('/message', methods=['GET', 'POST'])
@login_required
def message():
    if request.method == 'POST':
        receiver_id = request.form['receiver_id']
        content = request.form['content']
        message = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('home'))
    return render_template('message.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404