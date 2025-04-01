from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from .app import mail
from werkzeug.utils import secure_filename
from PIL import Image
import os

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except Exception:
        return False
    return email

def send_verification_email(user):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps({'user_id': user.id})
    link = url_for('auth.verify_email', token=token, _external=True)

    msg = Message('Verify Your Email', recipients=[user.email])
    msg.body = f'Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{link}\n\nIf you did not register, please ignore this email.'
    mail.send(msg)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def resize_and_save_avatar(file, user_id):
    filename = secure_filename(f"user_{user_id}.png")
    filepath = os.path.join('static', 'uploads', filename)

    image = Image.open(file)
    image = image.convert("RGB")
    image.thumbnail((300, 300))
    image.save(filepath, format='PNG')

    return filename
