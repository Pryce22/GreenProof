from werkzeug.security import generate_password_hash, check_password_hash
from app.models import user as user_model
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

USER_FILE = os.path.join(os.path.dirname(__file__), '../data/user.json')

def create_user(email, username, password):
    id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    users = load_users_from_file()
    if any(user['email'] == email for user in users):
        return False
    else:
        user = user_model.User(id, email=email, username=username, password_hash=password_hash)
        user.save()
        users.append({
            'id': id,
            'email': email,
            'username': username,
            'password_hash': password_hash,
            'verified': False,
            'verification_token': None
        })
        save_users_to_file(users)
        send_verification_email(email)
        return True

def check_email(email):
    users = load_users_from_file()
    return any(user['email'] == email for user in users)

def check_password(password_hash, password):
    return check_password_hash(password_hash, password)

import uuid

def send_verification_email(to_email):
    from_email = "your_email@example.com"
    from_password = "your_password"
    subject = "Email Verification"
    token = str(uuid.uuid4())
    verification_link = f"http://yourdomain.com/verify?token={token}&email={to_email}"
    body = f"Please verify your email by clicking on the following link: {verification_link}"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.example.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        # Save the token to the user's data
        users = load_users_from_file()
        for user in users:
            if user['email'] == to_email:
                user['verification_token'] = token
                save_users_to_file(users)
                break
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def verify_email(token, email):
    users = load_users_from_file()
    for user in users:
        if user['email'] == email and user.get('verification_token') == token:
            user['verified'] = True
            user.pop('verification_token', None)  # Remove the token after verification
            save_users_to_file(users)
            return True
    return False

def login_user(email, password):
    users = load_users_from_file()
    user = next((user for user in users if user['email'] == email), None)
    if user is None:
        return None
    if check_password(user['password_hash'], password):
        return user
    return None

def save_users_to_file(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file)

def load_users_from_file():
    try:
        with open(USER_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def get_user_tokens(user_id):
    users = load_users_from_file()
    user = next((user for user in users if user['id'] == user_id), None)
    if user:
        return user.get('tokens', [])
    return []

def add_token_to_user(user_id, token):
    users = load_users_from_file()
    for user in users:
        if user['id'] == user_id:
            if 'tokens' not in user:
                user['tokens'] = []
            user['tokens'].append(token)
            save_users_to_file(users)
            return True
    return False