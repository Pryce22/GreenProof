from werkzeug.security import generate_password_hash, check_password_hash
from app.models import user as user_model
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import supabase
import random
import time
from flask import session, request
import uuid
from datetime import datetime, timezone, timedelta
from app.utils.email_service import EmailService
from app.controllers import notifications_controller

email_service = EmailService()

def create_user(id, email, name, surname, password, phone_number, birthday):
    if check_email_exists(email):
        return False
    
    try:
        # Inizia una transazione
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
        
        # Inserisci l'utente
        user_response = supabase.table('user').insert(user_data).execute()
        
        if not user_response.data:
            return False
            
        # Crea il ruolo per l'utente
        role_data = {
            'user_id': id,
            'admin': False
        }
        
        # Inserisci il ruolo
        role_response = supabase.table('roles').insert(role_data).execute()
        
        if not role_response.data:
            # Se l'inserimento del ruolo fallisce, dovresti gestire il rollback
            # Elimina l'utente creato
            supabase.table('user').delete().eq('id', id).execute()
            return False
            
        return True
        
    except Exception as e:
        print(f"Error creating user: {e}")
        # In caso di errore, prova a fare rollback eliminando l'utente se esiste
        try:
            supabase.table('user').delete().eq('id', id).execute()
        except:
            pass
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
    token = generate_verification_token()
    if email_service.send_verification_code(to_email, token):
        session['verification_token'] = {
            'token': str(token),
            'email': to_email,
            'timestamp': time.time()
        }
        return True
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

def get_companies_by_user_id(user_id):
    try:
        # Primo passo: ottenere i 'company_id' dalla tabella 'company_employe' per il dato 'user_id'
        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).execute()
        
        if len(response.data) > 0:
            company_ids = [item['company_id'] for item in response.data]  # Lista di 'company_id' associati all'utente
            
            # Secondo passo: usare i 'company_id' per ottenere i dettagli di tutte le compagnie dalla tabella 'companies'
            company_response = supabase.table('companies').select('*').in_('company_id', company_ids).execute()
            
            if len(company_response.data) > 0:
                return company_response.data  # Restituisce una lista di compagnie
            
        # Se non trovi nulla, restituisci None
        return None
    except Exception as e:
        print(f"Error getting companies by user id: {e}")
        return None




def get_user_role(user_id):
    """Get the role of a user"""
    try:
        response = supabase.table('roles').select('admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None

def is_admin(user_id):
    """Check if user is admin"""
    try:
        response = supabase.table('roles').select('admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]['admin']
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def is_company_admin(user_id):
    """Check if user is admin"""
    try:
        response = supabase.table('company_employe').select('company_admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]['company_admin']
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def is_unique_company_admin(user_id):
    """Check if the user is the only company admin in their company"""
    try:
        # Ottieni l'azienda dell'utente
        response = supabase.table('company_employe').select('company_id', 'company_admin').eq('user_id', user_id).execute()
        
        if not response.data or not response.data[0]['company_admin']:
            return False  # L'utente non è un admin o non esiste

        company_id = response.data[0]['company_id']

        # Conta il numero di admin in questa azienda
        admin_count = supabase.table('company_employe').select('count', count='exact')\
            .eq('company_id', company_id).eq('company_admin', True).execute()

        if admin_count.count == 1:
            return True  # È l'unico admin dell'azienda
        return False  # Ci sono altri admin nella stessa azienda

    except Exception as e:
        print(f"Error checking unique admin status: {e}")
        return False
    
def get_company_ids_where_user_is_unique_admin(user_id):
    """Return the company_ids where the user is the only admin of the company"""
    try:
        # Ottieni tutte le compagnie in cui l'utente è un admin
        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).eq('company_admin', True).execute()
        
        if not response.data:
            return []  # Se l'utente non è amministratore in nessuna azienda, restituisci una lista vuota

        # Lista per raccogliere i company_id in cui l'utente è l'unico admin
        unique_admin_company_ids = []

        # Verifica per ogni compagnia
        for company in response.data:
            company_id = company['company_id']

            # Conta il numero di admin per questa compagnia
            admin_count = supabase.table('company_employe').select('count', count='exact')\
                .eq('company_id', company_id).eq('company_admin', True).execute()

            if admin_count.count == 1:  # Se l'utente è l'unico admin
                unique_admin_company_ids.append(company_id)

        return unique_admin_company_ids

    except Exception as e:
        print(f"Error getting unique admin company IDs: {e}")
        return []



def _get_ip_blocklist():
    """Get the IP blocklist from session"""
    return session.get('ip_blocklist', {})

def _update_ip_attempts(ip):
    
    """Update the IP attempts counter"""
    current_time = time.time()
    ip_blocklist = _get_ip_blocklist()
    
    # Clean up expired blocks
    ip_blocklist = {k: v for k, v in ip_blocklist.items() 
                   if current_time - v['timestamp'] < 30}
    
    if ip in ip_blocklist:
        ip_blocklist[ip]['attempts'] += 1
        ip_blocklist[ip]['timestamp'] = current_time
    else:
        ip_blocklist[ip] = {
            'attempts': 1,
            'timestamp': current_time
        }
    
    session['ip_blocklist'] = ip_blocklist
    return ip_blocklist[ip]['attempts']

def verify_login(email, password):
    try:
        # Check for IP-based blocking
        client_ip = request.remote_addr
        ip_blocklist = _get_ip_blocklist()
        current_time = time.time()
        
        if client_ip in ip_blocklist:
            block_info = ip_blocklist[client_ip]
            if block_info['attempts'] >= 3:
                # Check if 30 seconds have passed
                if current_time - block_info['timestamp'] < 60:
                    remaining_time = int(60 - (current_time - block_info['timestamp']))
                    return {'error': f'Too many failed attempts. Please wait {remaining_time} seconds.'}
                else:
                    # Reset attempts after timeout
                    del ip_blocklist[client_ip]
                    session['ip_blocklist'] = ip_blocklist

        # Verify credentials
        response = supabase.table('user').select('*').eq('email', email).execute()
        if len(response.data) == 0:
            attempts = _update_ip_attempts(client_ip)
            return None
            
        user = response.data[0]
        if check_password_hash(user['password'], password):
            # Reset IP attempts on successful login
            if client_ip in ip_blocklist:
                del ip_blocklist[client_ip]
                session['ip_blocklist'] = ip_blocklist
            return user
            
        # Update IP attempts
        attempts = _update_ip_attempts(client_ip)
        return None
        
    except Exception as e:
        print(f"Error verifying login: {e}")
        return None

def _update_failed_attempts(email):
    """Update the failed login attempts counter"""
    last_attempt = session.get('last_failed_login', {})
    current_time = time.time()
    
    if last_attempt.get('email') == email:
        session['last_failed_login'] = {
            'email': email,
            'attempts': last_attempt.get('attempts', 0) + 1,
            'timestamp': current_time
        }
    else:
        session['last_failed_login'] = {
            'email': email,
            'attempts': 1,
            'timestamp': current_time
        }

def update_user_info(user_id, field, value):
    try:
        response = supabase.table('user') \
            .update({field: value}) \
            .eq('id', user_id) \
            .execute()
        return response.data is not None
    except Exception as e:
        print(f"Error updating user info: {e}")
        return False

def generate_password_reset_token():
    """Generate a secure token for password reset"""
    return str(uuid.uuid4())  # Rimuovi il parametro email poiché non è necessario per generare il token

def send_password_reset_email(email, reset_token):
    reset_link = f"http://localhost:5000/password_recover_2/{reset_token}"
    return email_service.send_password_reset(email, reset_link)

def get_password_reset_attempts(ip):
    """Get the number of password reset attempts for an IP and clean expired attempts"""
    reset_attempts = session.get('password_reset_attempts', {})
    current_time = time.time()
    
    # Clean all expired attempts (older than 10 minutes)
    expired_ips = [ip_addr for ip_addr, data in reset_attempts.items() 
                  if current_time - data['timestamp'] > 600]
    
    # Remove expired attempts
    for expired_ip in expired_ips:
        del reset_attempts[expired_ip]
    
    if expired_ips:
        session['password_reset_attempts'] = reset_attempts
        session.modified = True
    
    # Return current attempts for the IP, or 0 if expired or not found
    if ip in reset_attempts:
        if current_time - reset_attempts[ip]['timestamp'] > 600:
            del reset_attempts[ip]
            session['password_reset_attempts'] = reset_attempts
            session.modified = True
            return 0
        return reset_attempts[ip]['attempts']
    return 0

def update_password_reset_attempts(ip):
    """Update password reset attempts for an IP"""
    reset_attempts = session.get('password_reset_attempts', {})
    current_time = time.time()
    
    # Clean expired attempts first
    expired_ips = [ip_addr for ip_addr, data in reset_attempts.items() 
                  if current_time - data['timestamp'] > 600]
    
    for expired_ip in expired_ips:
        del reset_attempts[expired_ip]
    
    # Update attempts for current IP
    if ip in reset_attempts and current_time - reset_attempts[ip]['timestamp'] <= 600:
        reset_attempts[ip]['attempts'] += 1
    else:
        reset_attempts[ip] = {
            'attempts': 1,
            'timestamp': current_time
        }
    
    session['password_reset_attempts'] = reset_attempts
    session.modified = True
    
    return reset_attempts[ip]['attempts']

def store_reset_token(email, token):
    """Store the reset token in the database"""
    try:
        # Prima elimina eventuali token esistenti per questa email
        supabase.table('recover_password_token') \
            .delete() \
            .eq('email', email) \
            .execute()
            
        # Inserisci il nuovo token
        response = supabase.table('recover_password_token') \
            .insert({
                'email': email,
                'token': token, 
                'is_used': False
            }) \
            .execute()
            
        print(f"Token stored in DB: {token} for email: {email}")
        return True
    except Exception as e:
        print(f"Error storing reset token: {e}")
        return False

def validate_reset_token(token):
    """Validate the reset token and return associated email if valid"""
    try:
        print(f"Validating token: {token}")
        ten_minutes_ago = time.time() - (10 * 60) 
        ten_minutes_ago = datetime.fromtimestamp(ten_minutes_ago, tz=timezone.utc)
        # Recupera il token dal database e verifica che non sia scaduto e non sia già stato usato
        '''
        response = supabase.table('recover_password_token') \
            .select('*') \
            .eq('token', token) \
            .eq('is_used', False) \
            .lt('created_at', ten_minutes_ago) \
            .execute()
        '''
        response = supabase.table('recover_password_token') \
            .select('*') \
            .eq('token', token) \
            .eq('is_used', False) \
            .execute()
        
        print(f"Token validation response: {response.data}")
        if response.data and len(response.data) > 0:
            token_data = response.data[0]  # Supponiamo che ci sia solo un token valido
            created_at = datetime.fromisoformat(token_data['created_at'])  # Converti la stringa in datetime
            #created_at = created_at.replace(tzinfo=None)
            expiration_time = created_at + timedelta(minutes=1)
            print(expiration_time)

        # Controlla se il token è ancora valido
            if datetime.now(timezone.utc) < expiration_time:
                token_data = response.data[0]
                print("sono QUi")
                return token_data['email']
            else:
                # Elimina i token scaduti
                response = supabase.table('recover_password_token') \
                .delete() \
                .eq('token', token) \
                .eq('is_used', False) \
                .execute()
                print(f"Token not found or expired: {token}")
                return None
    except Exception as e:
        print(f"Error validating reset token: {e}")
        return None

def update_user_password(email, new_password):
    """Update user's password and handle used token"""
    try:
        # Aggiorna la password
        password_hash = generate_password_hash(new_password)
        user_response = supabase.table('user') \
            .update({'password': password_hash}) \
            .eq('email', email) \
            .execute()
        
        if user_response.data:
            # Prima marca il token come usato
            supabase.table('recover_password_token') \
                .update({'is_used': True}) \
                .eq('email', email) \
                .execute()
            
            # Poi elimina tutti i token usati
            supabase.table('recover_password_token') \
                .delete() \
                .eq('is_used', True) \
                .execute()
                
            return True
            
        return False
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    
def accept_invitation(sender_email, receiver_email, company_id):
    try:
        notifications_controller.create_notification('invitation_accepted', sender_email, receiver_email , company_id)
        
        user_id = get_user_by_email(sender_email)['id']
        # Add user to company
        supabase.table('company_employe').insert({
            'user_id': user_id,
            'company_id': company_id,
        }).execute()
        return True
    except Exception as e:
        print(f"Error accepting invitation: {e}")
        return False

def reject_invitation(sender_email, receiver_email, company_id):
    try:

        notifications_controller.create_notification('invitation_rejected', sender_email, receiver_email , company_id)

        return True
    except Exception as e:
        print(f"Error rejecting invitation: {e}")
        return False

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
    user = next((user in users if user['id'] == user_id), None)
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

def get_companies_id_by_user_id(user_id):
    try:
        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).execute()
        if len(response.data) > 0:
            # Restituisce una lista di company_id
            return [company['company_id'] for company in response.data]
        return []
    except Exception as e:
        print(f"Error getting companies by user_id: {e}")
        return []

def get_employees_by_companies(excluded_user_id):
    try:
        # Ottieni tutte le company_id per il tuo user_id
        company_ids = get_companies_id_by_user_id(excluded_user_id)
        if not company_ids:
            print('Nessuna compagnia trovata per l\'utente.')
            return []

        # Ottieni tutti gli user_id delle persone associate alle compagnie (escludendo te stesso)
        response = supabase.table('company_employe').select('user_id', 'company_id').in_('company_id', company_ids).neq('user_id', excluded_user_id).execute()

        if len(response.data) > 0:
            employees = []
            for record in response.data:
                user_id = record['user_id']
                company_id = record['company_id']

                # Recupera i dettagli dell'utente dalla tabella 'user'
                user_response = supabase.table('user').select('name', 'surname', 'phone_number', 'email').eq('id', user_id).execute()
                if user_response.data:
                    user_details = user_response.data[0]  # Dettagli utente
                    user_details['id'] = user_id  # Aggiungi user_id ai dettagli

                    # Recupera il nome della compagnia dalla tabella 'companies'
                    company_response = supabase.table('companies').select('company_name').eq('company_id', company_id).execute()
                    if company_response.data:
                        company_name = company_response.data[0]['company_name']
                        user_details['company_name'] = company_name  # Aggiungi il nome della compagnia

                        employees.append(user_details)

            return employees

        return []
    except Exception as e:
        print(f"Error getting employees by companies: {e}")
        return []

def get_companies_information_by_user_id(user_id):
    try:
        # Ottieni tutti gli ID delle aziende a cui l'utente è associato
        company_ids = get_companies_by_user_id(user_id)
        
        if not company_ids:
            return []

        # Recupera le informazioni complete delle aziende usando gli ID
        response = supabase.table('companies').select('*').in_('company_id', company_ids).execute()
        
        if response.data:
            return response.data  # Restituisce una lista di dizionari con le informazioni delle aziende
        
        return []
    
    except Exception as e:
        print(f"Error getting company information by user_id: {e}")
        return []

def get_all_user_emails():
    try:
        response = supabase.table('user').select('email').execute()
        if response.data:
            return [user['email'] for user in response.data]  # Restituisce una lista di email
        return []
    except Exception as e:
        print(f"Error getting all user emails: {e}")
        return []
