from werkzeug.security import generate_password_hash, check_password_hash
from app import supabase
import random
import time
from flask import session, request
import uuid
from datetime import datetime, timezone, timedelta
from app.utils.email_service import EmailService
from app.controllers import notifications_controller

email_service = EmailService()

# Function to create a new user
def create_user(id, email, name, surname, password, phone_number, birthday):
    email=email.lower()
    if check_email_exists(email):
        return False, "There are problems with your account data"
    
    if check_phone_exists(phone_number):
        return False, "There are problems with your account data"
    
    
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
        
        # Insert the user
        user_response = supabase.table('user').insert(user_data).execute()
        
        if not user_response.data:
            return False, "Failed to create user"
            
        role_data = {
            'user_id': id,
            'admin': False
        }
        
        role_response = supabase.table('roles').insert(role_data).execute()
        
        if not role_response.data:
            supabase.table('user').delete().eq('id', id).execute()
            return False, "Failed to assign role"
            
        return True,  "User created successfully"
        
    except Exception as e:
        print(f"Error creating user: {e}")

        try:
            supabase.table('user').delete().eq('id', id).execute()
        except Exception as e:
            print(f"Error rolling back user creation: {e}")
        return False, "An error occurred during registration"

# Function to login a user
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

# Function to check if a phone number exists
def check_phone_exists(phone_number):
    try:
        response = supabase.table('user').select('phone_number').eq('phone_number', phone_number).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return False

# Function to check if an email exists
def check_email_exists(email):
    try:
        response = supabase.table('user').select('email').eq('email', email).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking email: {e}")
        return False
    
# Function to check if a password is correct
def check_password(password_hash, password):
    return check_password_hash(password_hash, password)

# Function to generate a verification token
def generate_verification_token():
    return random.randint(10000, 99999)

# Function to send a verification email
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

# Function to verify the token
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
        return False
        
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

# Function to get user by email
def get_user_by_email(email):
    try:
        response = supabase.table('user').select('*').eq('email', email).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

# Function to get user by ID
def get_user_by_id(user_id):
    try:
        response = supabase.table('user').select('*').eq('id', user_id).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None
    

# Function to get user email by ID
def get_user_email(user_id):
    try:
        response = supabase.table('user').select('email').eq('id', user_id).execute()
        print(response.data[0])
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None

# Function to get companies by user ID
def get_companies_by_user_id(user_id):
    try:

        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).execute()
        
        if len(response.data) > 0:
            company_ids = [item['company_id'] for item in response.data]
            
            company_response = supabase.table('companies').select('*').in_('company_id', company_ids).execute()
            
            if len(company_response.data) > 0:
                return company_response.data
            
        return None
    except Exception as e:
        print(f"Error getting companies by user id: {e}")
        return None

# Function to get user role
def get_user_role(user_id):

    try:
        response = supabase.table('roles').select('admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None

# Function to check if user is admin
def is_admin(user_id):

    try:
        response = supabase.table('roles').select('admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]['admin']
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

# Function to get unique company admins
def get_unique_company_admins():

    try:

        response = supabase.table('company_employe').select('user_id', 'company_id', 'company_admin').eq('company_admin', True).execute()
        
        if not response.data:
            return []

        company_admins = {}

        for record in response.data:
            company_id = record['company_id']
            user_id = record['user_id']

            if company_id not in company_admins:
                company_admins[company_id] = []

            company_admins[company_id].append(user_id)

        unique_admins = []

        for company_id, admins in company_admins.items():
            if len(admins) == 1:
                unique_admins.append(admins[0])

        return unique_admins

    except Exception as e:
        print(f"Error fetching unique company admins: {e}")
        return []


# Function to check if user is company admin
def is_company_admin(user_id):

    try:
        response = supabase.table('company_employe').select('company_admin').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]['company_admin']
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

# Function to check if user is unique company admin
def is_unique_company_admin(user_id):

    try:

        response = supabase.table('company_employe').select('company_id', 'company_admin').eq('user_id', user_id).execute()
        
        if not response.data or not response.data[0]['company_admin']:
            return False

        company_id = response.data[0]['company_id']

        admin_count = supabase.table('company_employe').select('count', count='exact')\
            .eq('company_id', company_id).eq('company_admin', True).execute()

        if admin_count.count == 1:
            return True
        return False

    except Exception as e:
        print(f"Error checking unique admin status: {e}")
        return False

# Function to get company IDs where user is unique admin  
def get_company_ids_where_user_is_unique_admin(user_id):

    try:

        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).eq('company_admin', True).execute()
        
        if not response.data:
            return []

        unique_admin_company_ids = []

        for company in response.data:
            company_id = company['company_id']


            admin_count = supabase.table('company_employe').select('count', count='exact')\
                .eq('company_id', company_id).eq('company_admin', True).execute()

            if admin_count.count == 1:
                unique_admin_company_ids.append(company_id)

        return unique_admin_company_ids

    except Exception as e:
        print(f"Error getting unique admin company IDs: {e}")
        return []

# Function to get company IDs where user is admin
def _get_ip_blocklist():
    return session.get('ip_blocklist', {})

# Function to update IP attempts
def _update_ip_attempts(ip):
    
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

# Function to verify login
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

# Function to update user information
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

# Function to generate password reset token
def generate_password_reset_token():
    return str(uuid.uuid4())

# Function to send password reset email
def send_password_reset_email(email, reset_token):
    reset_link = f"http://localhost:5000/password_recover_2/{reset_token}"
    return email_service.send_password_reset(email, reset_link)

# Function to get password reset attempts
def get_password_reset_attempts(ip):
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

# Function to update password reset attempts
def update_password_reset_attempts(ip):

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

# Function to reset password
def store_reset_token(email, token):
    """Store the reset token in the database"""
    try:

        supabase.table('recover_password_token') \
            .delete() \
            .eq('email', email) \
            .execute()
            

        supabase.table('recover_password_token') \
            .insert({
                'email': email,
                'token': token, 
                'is_used': False
            }) \
            .execute()
            
        return True
    except Exception as e:
        print(f"Error storing reset token: {e}")
        return False

# Function to validate reset token
def validate_reset_token(token):

    try:

        ten_minutes_ago = time.time() - (10 * 60) 
        ten_minutes_ago = datetime.fromtimestamp(ten_minutes_ago, tz=timezone.utc)
       
        response = supabase.table('recover_password_token') \
            .select('*') \
            .eq('token', token) \
            .eq('is_used', False) \
            .execute()
        
        if response.data and len(response.data) > 0:
            token_data = response.data[0]
            created_at = datetime.fromisoformat(token_data['created_at'])
            
            expiration_time = created_at + timedelta(minutes=1)


            if datetime.now(timezone.utc) < expiration_time:
                token_data = response.data[0]
                return token_data['email']
            else:
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

# Function to update user password
def update_user_password(email, new_password):

    try:
        password_hash = generate_password_hash(new_password)
        user_response = supabase.table('user') \
            .update({'password': password_hash}) \
            .eq('email', email) \
            .execute()
        
        if user_response.data:

            supabase.table('recover_password_token') \
                .update({'is_used': True}) \
                .eq('email', email) \
                .execute()
            
            supabase.table('recover_password_token') \
                .delete() \
                .eq('is_used', True) \
                .execute()
                
            return True
            
        return False
    except Exception as e:
        print(f"Error updating password: {e}")
        return False

# Function to accept invitation  
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

# Function to reject invitation
def reject_invitation(sender_email, receiver_email, company_id):
    try:

        notifications_controller.create_notification('invitation_rejected', sender_email, receiver_email , company_id)

        return True
    except Exception as e:
        print(f"Error rejecting invitation: {e}")
        return False

# Function to get companies ID by user ID
def get_companies_id_by_user_id(user_id):
    try:
        response = supabase.table('company_employe').select('company_id').eq('user_id', user_id).execute()
        if len(response.data) > 0:
            return [company['company_id'] for company in response.data]
        return []
    except Exception as e:
        print(f"Error getting companies by user_id: {e}")
        return []

# Function to get employees by companies
def get_employees_by_companies(excluded_user_id):
    try:
        company_ids = get_companies_id_by_user_id(excluded_user_id)
        if not company_ids:
            print('Nessuna compagnia trovata per l\'utente.')
            return []

        response = supabase.table('company_employe').select('user_id', 'company_id', 'company_admin').in_('company_id', company_ids).neq('user_id', excluded_user_id).execute()

        if len(response.data) > 0:
            employees = []
            for record in response.data:
                user_id = record['user_id']
                company_id = record['company_id']
                company_admin= record['company_admin']

                user_response = supabase.table('user').select('name', 'surname', 'phone_number', 'email').eq('id', user_id).execute()
                if user_response.data:
                    user_details = user_response.data[0]
                    user_details['id'] = user_id

                    company_response = supabase.table('companies').select('company_name', 'company_id').eq('company_id', company_id).execute()
                    if company_response.data:
                        company_data = company_response.data[0]
                        user_details['company_name'] = company_data['company_name']
                        user_details['company_id'] = company_data['company_id']
                        user_details['company_admin'] = company_admin

                        employees.append(user_details)

            return employees

        return []
    except Exception as e:
        print(f"Error getting employees by companies: {e}")
        return []

# Function to get companies information by user ID
def get_companies_information_by_user_id(user_id):
    try:
        company_ids = get_companies_id_by_user_id(user_id)
        
        if not company_ids:
            return []

        response = supabase.table('companies').select('*').in_('company_id', company_ids).execute()
        
        if response.data:
            return response.data
        
        return []
    
    except Exception as e:
        print(f"Error getting company information by user_id: {e}")
        return []

# Function to get all user emails
def get_all_user_emails():
    try:
        response = supabase.table('user').select('email').execute()
        if response.data:
            return [user['email'] for user in response.data]
        return []
    except Exception as e:
        print(f"Error getting all user emails: {e}")
        return []

# Function to get all users  
def get_all_users():
    try:
        user_response = supabase.table('user').select('*').execute()

        if user_response.data:
            return user_response.data
        else:
            return []

    except Exception as e:
        print(f"Error fetching users: {e}")
        return []
    
# Function to get users by name or surname
def get_users_by_name_or_surname(search_term):
    try:
        name_response = supabase.table('user') \
            .select('*') \
            .ilike('name', f'%{search_term}%') \
            .execute()

        surname_response = supabase.table('user') \
            .select('*') \
            .ilike('surname', f'%{search_term}%') \
            .execute()

        users = name_response.data + surname_response.data

        unique_users = [dict(t) for t in {tuple(user.items()) for user in users}]

        return unique_users
    except Exception as e:
        print(f"Error searching users by name or surname: {e}")
        return []
    
# Function to delete user   
def delete_user(user_id):
    try:
        response=supabase.table('user').delete().eq('id', user_id).execute()
        return response
    except Exception as e:
        print(f"Error searching users by name or surname: {e}")
        return []

# Function to delete employee
def delete_employee(user_id, company_id):
    try:
        response=supabase.table('company_employe').delete().eq('user_id', user_id).eq('company_id', company_id).execute()
        return response
    except Exception as e:
        print(f"Error searching users by name or surname: {e}")
        return []

# Function to set company admin
def set_company_admin(company_id, user_id):
    
    try:

        response = supabase.table('company_employe') \
            .update({'company_admin': True}) \
            .eq('company_id', company_id) \
            .eq('user_id', user_id) \
            .execute()
        
        if response.data:
            return True
        else:
            print(f"Failed to promote user {user_id} to admin in company {company_id}")
            return False
    except Exception as e:
        print(f"Error setting company admin: {e}")
        return False
    
# Function to check if user is admin by email
def check_user_by_email_if_is_admin(email):
    try:
        response_user = supabase.table('user').select('id').eq('email', email).execute()
        
        if len(response_user.data) == 0:
            return False

        user_id = response_user.data[0]['id']

        response_roles = supabase.table('roles').select('user_id').eq('user_id', user_id).eq('admin', True).execute()
        
        if len(response_roles.data) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

# Function to view products
def view_products():
    try:
        response = supabase.table('products') \
            .select('*') \
            .execute()
        
        if response.data:
            return response
        else:
            print("Failed to view product")
            return False
    except Exception as e:
        print(f"Error setting to view product: {e}")
        return False