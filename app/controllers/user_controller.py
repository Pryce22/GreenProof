from werkzeug.security import generate_password_hash, check_password_hash
from app.models import user as user_model
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from app import supabase
import random
import time
from flask import session


def create_user(id, email, name, surname, password, phone_number, birthday):
    if check_email_exists(email):
        return False
    
    try:
        password_hash = generate_password_hash(password)
        user_data = {
            'id': id,
            'email': email,
            'name': name,
            'surname': surname,
            'password': password_hash,
            'phone_number': phone_number,
            'birthday': birthday,
        }
        
        response = supabase.table('user').insert(user_data).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
        
def login_user(email, password):
    try:
        response = supabase.table('user').select('email', 'password').eq('email', email).execute()
        if len(response.data) == 0:
            return None
        user = response.data[0]
        if check_password(user['password'], password):
            return user
        return None
    except Exception as e:
        print(f"Error logging in user: {e}")
        return None

def check_email_exists(email):
    try:
        response = supabase.table('user').select('email').eq('email', email).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking email: {e}")
        return False

def check_password(password_hash, password):
    return check_password_hash(password_hash, password)

def generate_verification_token():
    return random.randint(10000, 99999)

def send_verification_email(to_email):
    from_email = "ssb2024.2025@gmail.com"
    from_password = "vpon ryms zupv owmt"
    subject = "Email Verification"
    
    # Generate a new token
    token = generate_verification_token()
    body = f"Your new verification code is: {token}"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        # Update stored token
        session['verification_token'] = {
            'token': str(token),
            'email': to_email,
            'timestamp': time.time()
        }
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def verify_token(token, email):
    stored_data = session.get('verification_token')
    attempts = session.get('verification_attempts', 0)
    
    if not stored_data:
        return False
    
    if attempts >= 2:
        # Reset token and attempts after 3 failed tries
        session.pop('verification_token', None)
        session.pop('verification_attempts', None)
        # Generate and send new token
        send_verification_email(email)
        return 'max_attempts'
        
    # Increment attempts
    session['verification_attempts'] = attempts + 1
        
    # Check if token is valid and not expired (2 minutes)
    if (stored_data['token'] == str(token) and 
        stored_data['email'] == email and 
        (time.time() - stored_data['timestamp']) < 120):
        session.pop('verification_token', None)
        session.pop('verification_attempts', None)
        return True
    return False

def get_user_by_email(email):
    try:
        response = supabase.table('user').select('*').eq('email', email).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def get_user_by_id(user_id):
    try:
        response = supabase.table('user').select('*').eq('id', user_id).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None

def verify_login(email, password):
    try:
        response = supabase.table('user').select('*').eq('email', email).execute()
        if len(response.data) == 0:
            return None
        user = response.data[0]
        if check_password_hash(user['password'], password):
            return user
        return None
    except Exception as e:
        print(f"Error verifying login: {e}")
        return None

'''
def login_user(email, password):
    users = load_users_from_file()
    user = next((user for user in users if user['email'] == email), None)
    if user is None:
        return None
    if check_password(user['password_hash'], password):
        return user
    return None

def get_user_tokens(user_id):
    users = load_users_from_file()
    user = next((user for user in users if user['id'] == user_id), None)
    if user:
        return user.get('tokens', [])
    return []

def add_token_to_user(user_id, token):
    users = load_users_from_file()
    for user in users:
        if user['id'] == user_id):
            if 'tokens' not in user:
                user['tokens'] = []
            user['tokens'].append(token)
            save_users_to_file(users)
            return True
    return False
'''