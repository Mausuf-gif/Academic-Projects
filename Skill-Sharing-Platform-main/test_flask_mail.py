from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_gmail_app_password'  # Use Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

@app.route('/test_email')
def test_email():
    try:
        msg = Message(
            subject='Test Email',
            recipients=['mostafijur.bd786@gmail.com'],  # Replace with your test email
            body='This is a test email from Flask-Mail.'
        )
        mail.send(msg)
        return 'Test email sent successfully!'
    except Exception as e:
        return f'Error: {str(e)}'

if __name__ == '__main__':
    app.run(debug=True)
