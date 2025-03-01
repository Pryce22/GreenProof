from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.controllers import user_controller, notifications_controller
import re
import uuid
import time
from datetime import datetime, date


bp = Blueprint('auth', __name__)

def get_user_info():
    user_id = session.get('id')
    user = None
    is_admin = False
    is_company_admin = False
    notifications = []
    
    if user_id:
        user = user_controller.get_user_by_id(user_id)
        is_admin = user_controller.is_admin(user_id)
        is_company_admin = user_controller.is_company_admin(user_id)
        notifications = notifications_controller.get_unread_notifications_count(user['email'])
    return user_id, user, is_admin, is_company_admin, notifications, 

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        result = user_controller.verify_login(email, password)
        
        # Check if result contains error message (timeout)
        if isinstance(result, dict) and 'error' in result:
            return jsonify({
                'success': False, 
                'error': result['error']
            })
            
        if result:
            # Store login info in session for MFA verification
            session['pending_login'] = {
                'email': email,
                'user_id': result['id']
            }
            # Send verification email
            if user_controller.send_verification_email(email):
                return jsonify({'success': True, 'redirect': url_for('auth.mfa')})
            return jsonify({'success': False, 'error': 'Failed to send verification email.'})
            
        return jsonify({
            'success': False, 
            'error': 'Invalid email or password'
        })
    
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    return render_template('login.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, notifications=notifications)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        

        email = request.form['email']
        first_name = request.form['firstName']
        surname = request.form['surname']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        phone_number = request.form['phone']
        birth_date = request.form['birthDate']
        id_company = uuid.uuid4().int & (1<<32)-1
        
        # Check if passwords match and pattern
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'})
        
        password_pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")
        if not password_pattern.match(password):
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character'})
        
        # Check phone number validity: controlla che il numero abbia solo cifre e il segno +
        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone_number):
            return jsonify({'success': False, 'error': 'Invalid phone number format'})
        
        # Check birth_date validity
        try:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid birth date format. Use YYYY-MM-DD'})
        
        # La data di nascita non deve essere nel futuro
        if birth_date_obj > date.today():
            return jsonify({'success': False, 'error': 'Birth date cannot be in the future'})
        
        # Verifica che l'utente abbia almeno 18 anni (puoi modificare questa soglia a piacere)
        age = (date.today() - birth_date_obj).days // 365
        if age < 16:
            return jsonify({'success': False, 'error': 'You must be at least 16 years old'})
        
        # Store registration data in session
        session['pending_registration'] = {
            'id': id_company,
            'email': email,
            'name': first_name,
            'surname': surname,
            'password': password,
            'phone_number': phone_number,
            'birth_date': birth_date
        }
        
        # Send verification email
        if user_controller.send_verification_email(email):
            return jsonify({'success': True, 'redirect': url_for('auth.mfa')})
        return jsonify({'success': False, 'error': 'Failed to send verification email'})
    
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    return render_template('register.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, notifications=notifications)

@bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    # Controlla sia login che registrazione
    pending_login = session.get('pending_login')
    pending_registration = session.get('pending_registration')
    
    if pending_login:
        email = pending_login['email']
    elif pending_registration:
        email = pending_registration['email']
    else:
        return jsonify({'success': False, 'error': 'Session expired. Please try again.'})
    
    # Reset dei tentativi quando si richiede un nuovo codice
    session.pop('verification_attempts', None)
    
    if user_controller.send_verification_email(email):
        # Salva il timestamp del nuovo codice
        session['verification_start_time'] = time.time()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to send verification email'})

@bp.route('/mfa', methods=['GET', 'POST'])
def mfa():
    if request.method == 'GET':
        # Resetta il timer ad ogni caricamento della pagina MFA
        session['verification_start_time'] = time.time()
        # (Opzionalmente, resetta anche i tentativi)
        session.pop('verification_attempts', None)
    
    if request.method == 'POST':
        token = request.form.get('verificationCode')
        if not token:
            return jsonify({'success': False, 'error': 'Verification code is required'})
            
        pending_login = session.get('pending_login')
        pending_registration = session.get('pending_registration')
        attempts = session.get('verification_attempts', 0)
        
        if pending_login:
            if user_controller.verify_token(token, pending_login['email']):
                session.pop('pending_login', None)
                session['id'] = pending_login['user_id']
                session.pop('verification_attempts', None)
                return jsonify({'success': True, 'redirect': url_for('main.home')})
            else:
                attempts += 1
                session['verification_attempts'] = attempts
                if attempts >= 3:
                    # Raggiunto il limite di tentativi: rinvia un nuovo codice
                    user_controller.send_verification_email(pending_login['email'])
                    session['verification_start_time'] = time.time()
                    session.pop('verification_attempts', None)
                    return jsonify({
                        'success': False,
                        'error': 'Too many invalid attempts. A new verification code has been sent to your email.'
                    })
                return jsonify({'success': False, 'error': 'Invalid verification code'})
                
        elif pending_registration:
            if user_controller.verify_token(token, pending_registration['email']):
                if user_controller.create_user(
                    id=pending_registration['id'],
                    email=pending_registration['email'],
                    name=pending_registration['name'],
                    surname=pending_registration['surname'],
                    password=pending_registration['password'],
                    phone_number=pending_registration['phone_number'],
                    birthday=pending_registration['birth_date']
                ):
                    session.pop('pending_registration', None)
                    user = user_controller.get_user_by_email(pending_registration['email'])
                    if user:
                        session['id'] = user['id']
                        session.pop('verification_attempts', None)
                        return jsonify({'success': True, 'redirect': url_for('main.home')})
                return jsonify({'success': False, 'error': 'Failed to create account'})
            else:
                attempts += 1
                session['verification_attempts'] = attempts
                if attempts >= 3:
                    user_controller.send_verification_email(pending_registration['email'])
                    session['verification_start_time'] = time.time()
                    session.pop('verification_attempts', None)
                    return jsonify({
                        'success': False,
                        'error': 'Too many invalid attempts. A new verification code has been sent to your email.'
                    })
                return jsonify({'success': False, 'error': 'Invalid verification code'})
        
        return jsonify({'success': False, 'error': 'Session expired. Please try again.'})
    
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    return render_template('MFA.html', user_id=user_id, user=user, is_admin=is_admin,
                           is_company_admin=is_company_admin, notifications=notifications)

@bp.route('/password_recover', methods=['GET', 'POST'])
def password_recover():
    if request.method == 'GET':
        # Clean expired attempts on page load
        client_ip = request.remote_addr
        user_controller.get_password_reset_attempts(client_ip)
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required.'
            })
            
        client_ip = request.remote_addr
        
        # Check attempt limits (this will also clean expired attempts)
        attempts = user_controller.get_password_reset_attempts(client_ip)
        if attempts >= 3:
            remaining_time = 600  # 10 minutes in seconds
            return jsonify({
                'success': False,
                'error': f'Too many attempts. Please try again in {remaining_time//60} minutes.'
            })
        
        # Verify email exists
        user = user_controller.get_user_by_email(email)
        if not user:
            user_controller.update_password_reset_attempts(client_ip)
            return jsonify({
                'success': False,
                'error': 'No account found with this email address.'
            })
        
        try:
            # Generate reset token
            reset_token = user_controller.generate_password_reset_token()
            
            # Store token in session
            user_controller.store_reset_token(email, reset_token)
            
            # Verifica che il token sia stato salvato correttamente
            stored_tokens = session.get('reset_tokens', {})
            #print(f"Tokens after storing: {stored_tokens}")  # Debug print
            
            # Send reset email
            if user_controller.send_password_reset_email(email, reset_token):
                return jsonify({
                    'success': True,
                    'message': 'Password reset instructions have been sent to your email.'
                })
            
            return jsonify({
                'success': False,
                'error': 'Failed to send reset email.'
            })
            
        except Exception as e:
            print(f"Error in password reset: {e}")  # Debug print
            return jsonify({
                'success': False,
                'error': 'An error occurred during password reset.'
            })
    
    return render_template('password_recover.html')

@bp.route('/password_recover_2/<token>', methods=['GET', 'POST'])
def password_recover_2(token):
    #print(f"Accessing password_recover_2 with token: {token}")  # Debug print
    email = user_controller.validate_reset_token(token)
    #print(email)
    
    if not email:
        return render_template('error.html', 
                             error="Invalid or expired reset link. Please request a new password reset."), 400
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        
        if not password or not confirm_password:
            return jsonify({
                'success': False,
                'error': 'Password is required'
            })
            
        if password != confirm_password:
            return jsonify({
                'success': False,
                'error': 'Passwords do not match'
            })
        
        # Aggiorna la password
        if user_controller.update_user_password(email, password):
            # Rimuovi il token usato
            reset_tokens = session.get('reset_tokens', {})
            if token in reset_tokens:
                del reset_tokens[token]
                session['reset_tokens'] = reset_tokens
                
            return jsonify({
                'success': True,
                'redirect': url_for('auth.login')
            })
            
        return jsonify({
            'success': False,
            'error': 'Failed to update password'
        })
    
    return render_template('password_recover_2.html', token=token, email=email)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))
