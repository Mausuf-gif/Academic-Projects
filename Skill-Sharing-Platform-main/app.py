import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, EmailField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_mail import Mail, Message

import secrets
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask_socketio import SocketIO, join_room, leave_room, emit
import logging
logging.basicConfig(level=logging.DEBUG)

# meco laya pyqa hljx
# App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/skill_sharing_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'farhanishrak5@gmail.com'
# app.config['MAIL_PASSWORD'] = 'ozfl pepx qtpk fuae'  # Use app password for Gmail
# app.config['MAIL_DEFAULT_SENDER'] = 'farhanishrak5@gmail.com'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'farhanishrak5@gmail.com'
app.config['MAIL_PASSWORD'] = 'hpku oqbe zqsz kiyv'  # Use Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'farhanishrak5@gmail.com'


# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)  # Initialize SocketIO

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_no = db.Column(db.String(11))
    address = db.Column(db.String(255))
    password = db.Column(db.String(128), nullable=False)  # Store passwords in plain text
    user_type = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password = password  # Store the password directly

    def check_password(self, password):
        return self.password == password  # Compare the plain text password


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')# Forms


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone_no = StringField('Phone Number')
    address = StringField('Address')
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('User Type', choices=[('skill_provider', 'Skill Provider'), ('client', 'Client')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class Skills(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    experience_level = db.Column(db.String(50))
    description = db.Column(db.Text)
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(50), nullable=False)  # e.g., "2 hours", "3 days"
    skill_level = db.Column(db.String(50), nullable=False)  # e.g., "Beginner", "Advanced"

    provider = db.relationship('User', backref='courses')
    def average_rating(self):
        if not self.reviews:
            return None
        return round(sum([review.rating for review in self.reviews]) / len(self.reviews), 1)

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)

    # Relationship to access the course details
    course = db.relationship('Course', backref='wishlisted_by')

class PurchasedCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)

    # Relationship to access course details
    course = db.relationship('Course', backref='purchased_by')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating from 1 to 5
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('User', backref='reviews')
    course = db.relationship('Course', backref='reviews')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class CourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    duration = StringField('Duration', validators=[DataRequired()])
    skill_level = SelectField('Skill Level', choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], validators=[DataRequired()])
    submit = SubmitField('Create Course')

class ReportForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Generate Report')




# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
def home():
    # Fetch all courses from the database
    courses = Course.query.all()
    return render_template('home.html', courses=courses)
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()  # Create an instance of the form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if email == "read.al.rashid@g.bracu.ac.bd" and password == "read.al.rashid@g.bracu.ac.bd":
            login_user(user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin'))
        elif user and user.check_password(password):
            login_user(user)
            logging.debug(f"User logged in: {user.name}, User type: {user.user_type}")
            flash('Login successful!', 'success')
            if user.user_type == 'skill_provider':
                return redirect(url_for('skill_provider_dashboard'))
            elif user.user_type == 'client':
                return redirect(url_for('client_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)



@app.route('/admin')
def admin():
    return render_template('admin.html')
from flask_mail import Message

# # Forgot Password Route
# @app.route('/forgot_password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         user = User.query.filter_by(email=email).first()
#         if user:
#             token = secrets.token_urlsafe(16)  # Generate a secure token
#             reset_url = url_for('reset_password', token=token, _external=True)
#             try:
#                 # Send the email
#                 msg = Message('Password Reset Request', recipients=[email])
#                 msg.body = f"""
#                 Hi {user.name},

#                 You requested to reset your password. Click the link below to reset your password:
#                 {reset_url}

#                 If you didn't request this, please ignore this email.

#                 Thanks,
#                 Skill Sharing Platform Team
#                 """
#                 mail.send(msg)
#                 flash('Password reset email sent. Please check your inbox.', 'success')
#             except Exception as e:
#                 flash(f'Error sending email: {str(e)}', 'danger')
#         else:
#             flash('No account found with that email.', 'danger')

#     return render_template('forgot_password.html')
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(16)  # Generate a secure token
            reset_url = url_for('reset_password', token=token, _external=True)
            logging.debug(f"Generated Reset URL: {reset_url}")
            
            try:
                # Create and configure the email message
                msg = Message()
                msg.subject = 'Password Reset Request'
                msg.sender = app.config['MAIL_USERNAME']
                msg.recipients = [email]
                msg.body = f"""
                Hi {user.name},

                You requested to reset your password. Click the link below to reset your password:
                {reset_url}

                If you didn't request this, please ignore this email.

                Thanks,
                Skill Sharing Platform Team
                """
                mail.send(msg)
                logging.info(f"Password reset email sent to: {email}")
                flash('Password reset email sent. Please check your inbox.', 'success')
            except Exception as e:
                logging.error(f"Error sending email: {e}")
                flash('There was an error sending the email. Please try again later.', 'danger')
        else:
            flash('No account found with that email.', 'danger')

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if new_password == confirm_password:
            # Verify token and update password (add token validation logic here)
            email = request.form.get('email')  # Get email for validation
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(new_password)
                db.session.commit()
                flash('Your password has been reset. You can now log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Invalid token or user not found.', 'danger')
        else:
            flash('Passwords do not match.', 'danger')

    return render_template('reset_password.html', token=token)






@app.route('/dashboard')
@login_required
def dashboard():
    # Check the user type and redirect accordingly
    if current_user.user_type == 'skill_provider':
        return redirect(url_for('skill_provider_dashboard'))
    elif current_user.user_type == 'client':
        return redirect(url_for('client_dashboard'))
    else:
        flash('Invalid user type.', 'danger')
        return redirect(url_for('logout'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone_no=form.phone_no.data,
            address=form.address.data,
            password=form.password.data,  # Store the plain text password
            user_type=form.user_type.data
        )
        db.session.add(user)
        try:
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed. Error: {str(e)}')
    return render_template('register.html', form=form)


@app.route('/dashboard/skill_provider', methods=['GET', 'POST'])
@login_required
def skill_provider_dashboard():
    if current_user.user_type != 'skill_provider':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Handle profile update
    if request.method == 'POST' and 'update_profile' in request.form:
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        current_user.phone_no = request.form.get('phone_no')
        current_user.address = request.form.get('address')
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    # Handle reply to a client message
    if request.method == 'POST' and 'reply_message' in request.form:
        recipient_id = int(request.form.get('recipient_id'))
        reply_message = request.form.get('reply_message')
        if reply_message:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=recipient_id,
                message=reply_message
            )
            try:
                db.session.add(new_message)
                db.session.commit()
                flash('Reply sent successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error sending reply: {str(e)}', 'danger')

    # Retrieve all messages involving the skill provider
    raw_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp).all()

    # Group messages by client
    messages_by_user = {}
    for message in raw_messages:
        # Determine the other user in the conversation
        other_user_id = message.sender_id if message.recipient_id == current_user.id else message.recipient_id
        other_user = User.query.get(other_user_id)

        if other_user_id not in messages_by_user:
            messages_by_user[other_user_id] = {
                "user_name": other_user.name,
                "user_email": other_user.email,
                "messages": []
            }

        # Add the message to the conversation
        messages_by_user[other_user_id]["messages"].append({
            "message": message.message,
            "timestamp": message.timestamp,
            "is_sent": message.sender_id == current_user.id  # Indicate if the message was sent by the provider
        })

    # Retrieve courses created by the skill provider
    courses = Course.query.filter_by(provider_id=current_user.id).all()

    return render_template(
        'skill_provider_dashboard.html',
        user=current_user,
        courses=courses,
        messages_by_user=messages_by_user
    )

@app.route('/dashboard/skill_provider/add_course', methods=['POST'])
@login_required
def add_course():
    if current_user.user_type != 'skill_provider':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    course_name = request.form.get('course_name')
    description = request.form.get('description')
    duration = request.form.get('duration')
    skill_level = request.form.get('skill_level')
    new_course = Course(
        provider_id=current_user.id,
        course_name=course_name,
        description=description,
        duration=duration,
        skill_level=skill_level
    )
    try:
        db.session.add(new_course)
        db.session.commit()
        flash('Course added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding course: {str(e)}', 'danger')

    return redirect(url_for('skill_provider_dashboard'))

# Route to delete a course
@app.route('/dashboard/skill_provider/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.user_type != 'skill_provider':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get(course_id)
    if course and course.provider_id == current_user.id:
        try:
            db.session.delete(course)
            db.session.commit()
            flash('Course deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting course: {str(e)}', 'danger')
    else:
        flash('Course not found or access denied.', 'danger')
    
    return redirect(url_for('skill_provider_dashboard'))


@app.route('/dashboard/client', methods=['GET'])
@login_required
def client_dashboard():
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    search_query = request.args.get('search', '').lower()
    skill_level_filter = request.args.get('skill_level', '')

    # Fetch all courses with optional filters
    courses_query = Course.query
    if search_query:
        courses_query = courses_query.filter(Course.course_name.ilike(f"%{search_query}%"))
    if skill_level_filter:
        courses_query = courses_query.filter_by(skill_level=skill_level_filter)

    courses = courses_query.all()

    return render_template('client_dashboard.html', user=current_user, courses=courses)




@app.route('/dashboard/client/add_to_wishlist/<int:course_id>', methods=['POST'])
@login_required
def add_to_wishlist(course_id):
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get(course_id)
    if course:
        existing_entry = Wishlist.query.filter_by(client_id=current_user.id, course_id=course_id).first()
        if not existing_entry:
            wishlist_entry = Wishlist(client_id=current_user.id, course_id=course_id)
            db.session.add(wishlist_entry)
            try:
                db.session.commit()
                flash(f'Course "{course.course_name}" added to wishlist!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding to wishlist: {str(e)}', 'danger')
        else:
            flash('Course is already in your wishlist.', 'info')
    else:
        flash('Course not found.', 'danger')

    return redirect(url_for('client_dashboard'))


@app.route('/dashboard/client/wishlist', methods=['GET'])
@login_required
def view_wishlist():
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Retrieve wishlist items with associated course details
    wishlist = Wishlist.query.filter_by(client_id=current_user.id).all()
    return render_template('wishlist.html', wishlist=wishlist)

@app.route('/course/<int:course_id>')
@login_required
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    can_review = PurchasedCourse.query.filter_by(client_id=current_user.id, course_id=course_id).first() is not None
    return render_template('course_details.html', course=course, can_review=can_review)

@app.route('/dashboard/client/buy_course/<int:course_id>', methods=['POST'])
@login_required
def buy_course(course_id):
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if the course exists and hasn't already been purchased
    course = Course.query.get(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('client_dashboard'))

    existing_purchase = PurchasedCourse.query.filter_by(client_id=current_user.id, course_id=course_id).first()
    if existing_purchase:
        flash('You have already purchased this course.', 'info')
        return redirect(url_for('client_dashboard'))

    # Add the course to the purchased list
    purchased_course = PurchasedCourse(client_id=current_user.id, course_id=course_id)
    db.session.add(purchased_course)
    try:
        db.session.commit()

        # Send Email Notification
        msg = Message(
            subject=f'Course Purchased: {course.course_name}',
            recipients=[current_user.email]  # Send email to the current user
        )
        msg.body = f"""
        Hello {current_user.name},

        Thank you for purchasing the course: {course.course_name}!

        Course Details:
        - Provider: {course.provider.name if course.provider else "N/A"}
        - Description: {course.description}
        - Duration: {course.duration}
        - Level: {course.skill_level}

        If you have any questions, feel free to reach out to the provider.

        Best regards,
        Skill Sharing Platform Team
        """
        mail.send(msg)

        flash(f'You have successfully bought the course: {course.course_name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error purchasing course: {str(e)}', 'danger')

    return redirect(url_for('client_dashboard'))


@app.route('/dashboard/client/your_courses', methods=['GET'])
@login_required
def your_courses():
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Retrieve all purchased courses for the current user
    purchased_courses = PurchasedCourse.query.filter_by(client_id=current_user.id).all()
    return render_template('your_courses.html', purchased_courses=purchased_courses)

@app.route('/dashboard/client/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_purchased_course(course_id):
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    purchased_course = PurchasedCourse.query.filter_by(client_id=current_user.id, course_id=course_id).first()
    if not purchased_course:
        flash('Course not found in your purchased list.', 'danger')
        return redirect(url_for('your_courses'))

    try:
        db.session.delete(purchased_course)
        db.session.commit()
        flash('Course removed from your list.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'danger')

    return redirect(url_for('your_courses'))

@app.route('/course/<int:course_id>/review', methods=['GET', 'POST'])
@login_required
def submit_review(course_id):
    if current_user.user_type != 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Check if the client has purchased this course
    purchased_course = PurchasedCourse.query.filter_by(client_id=current_user.id, course_id=course_id).first()
    if not purchased_course:
        flash('You can only review courses you have purchased.', 'danger')
        return redirect(url_for('client_dashboard'))

    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        review = request.form.get('review')

        # Check if the client has already reviewed this course
        existing_review = Review.query.filter_by(client_id=current_user.id, course_id=course_id).first()
        if existing_review:
            flash('You have already reviewed this course.', 'info')
            return redirect(url_for('your_courses'))

        new_review = Review(course_id=course_id, client_id=current_user.id, rating=rating, review=review)
        db.session.add(new_review)
        try:
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting review: {str(e)}', 'danger')

        return redirect(url_for('your_courses'))

    # If GET, render the review form
    course = Course.query.get_or_404(course_id)
    return render_template('submit_review.html', course=course)
4
@app.route('/messages/<int:provider_id>', methods=['GET'])
@login_required
def get_messages(provider_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == provider_id)) |
        ((Message.sender_id == provider_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()

    return {
        "messages": [{"sender": "You" if msg.sender_id == current_user.id else "Provider", "message": msg.message} for msg in messages]
    }

# Real-Time Events with SocketIO
@socketio.on('join')
def handle_join(data):
    room = f"{data['sender_id']}_{data['recipient_id']}"
    join_room(room)
    emit('status', {'msg': f"{data['username']} has joined the chat."}, room=room)

@socketio.on('message')
def handle_message(data):
    room = f"{data['sender_id']}_{data['recipient_id']}"
    try:
        # Ensure sender and recipient exist
        sender = User.query.get(data['sender_id'])
        recipient = User.query.get(data['recipient_id'])
        if not sender or not recipient:
            emit('error', {'msg': 'Invalid sender or recipient.'}, room=room)
            return
        
        # Save message
        new_message = Message(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            message=data['message']
        )
        db.session.add(new_message)
        db.session.commit()
        
        # Broadcast the message
        emit('message', {
            'sender': data['username'],
            'message': data['message'],
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }, room=room)
    except Exception as e:
        emit('error', {'msg': f"Error saving message: {str(e)}"}, room=room)


@socketio.on('leave')
def handle_leave(data):
    room = f"{data['sender_id']}_{data['recipient_id']}"
    leave_room(room)
    emit('status', {'msg': f"{data['username']} has left the chat."}, room=room)

@app.route('/admin/users')
@login_required
def view_users():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('view_users.html', users=users)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        try:
            db.session.commit()
            flash('User deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting user: {str(e)}', 'danger')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('view_users'))
@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone_no=form.phone_no.data,
            address=form.address.data,
            password=form.password.data,  # Store the plain text password
            user_type=form.user_type.data
        )
        db.session.add(user)
        try:
            db.session.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('view_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    return render_template('create_user.html', form=form)

@app.route('/admin/courses')
@login_required
def view_courses():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    courses = Course.query.all()
    return render_template('view_courses.html', courses=courses)


@app.route('/admin/delete_course/<int:course_id>', methods=['POST'], endpoint='admin_delete_course')
@login_required
def delete_course(course_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    print(f"Attempting to delete course with ID: {course_id}")
    course = Course.query.get(course_id)
    if course:
        print(f"Course found: {course.course_name}")
        db.session.delete(course)
        try:
            db.session.commit()
            flash('Course deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting course: {str(e)}', 'danger')
    else:
        flash('Course not found.', 'danger')

    return redirect(url_for('view_courses'))
@app.route('/admin/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            provider_id=current_user.id,  # Assuming admin acts as the provider
            course_name=form.course_name.data,
            description=form.description.data,
            duration=form.duration.data,
            skill_level=form.skill_level.data
        )
        db.session.add(course)
        try:
            db.session.commit()
            flash('Course created successfully!', 'success')
            return redirect(url_for('view_courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating course: {str(e)}', 'danger')
    return render_template('create_course.html', form=form)
@app.route('/admin/reports')
@login_required
def view_reports():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Fetch user count over time
    users = User.query.all()
    dates = [user.created_at for user in users]
    dates.sort()

    # Generate cumulative user count over time
    user_counts = range(1, len(dates) + 1)

    # Plot the graph
    plt.figure(figsize=(10, 5))
    plt.plot(dates, user_counts, marker='o')
    plt.title('Total Users Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Users')
    plt.grid(True)

    # Save the graph to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()

    return render_template('view_reports.html', graph_url=graph_url)


@app.route('/admin/generate_report', methods=['GET', 'POST'])
@login_required
def generate_report():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    form = ReportForm()
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        # Query users created within the specified date range
        users = User.query.filter(User.created_at >= start_date, User.created_at <= end_date).all()

        # Build report data
        report_data = [{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone_no': user.phone_no,
            'address': user.address,
            'user_type': user.user_type,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        } for user in users]

        return render_template('generated_report.html', report_data=report_data)
    return render_template('generate_report.html', form=form)


@app.route('/test_email')
def test_email():
    try:
        msg = Message(
            subject='Test Email',
            recipients=['your_email@gmail.com'],  # Replace with your email
            body='This is a test email from Flask-Mail.'
        )
        mail.send(msg)
        return 'Test email sent successfully!'
    except Exception as e:
        return f'Error: {str(e)}'


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    socketio.run(app, debug=True)  
