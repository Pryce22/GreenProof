from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import geonamescache
import re
from app.config import Config
from app.controllers import user_controller
from app.controllers import company_controller
import uuid
from werkzeug.utils import secure_filename
import os

app = Flask(__name__,
            static_folder='app/static',
            template_folder='app/templates')
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

def get_user_info():
    user_id = session.get('id')
    user = None
    is_admin = False
    is_company_admin= False
    if user_id:
        user = user_controller.get_user_by_id(user_id)
        is_admin = user_controller.is_admin(user_id)
        is_company_admin = user_controller.is_company_admin(user_id)
    return user_id, user, is_admin, is_company_admin

@app.route('/')
def home():
    user_id, user, is_admin, is_company_admin = get_user_info()
    return render_template('index.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin)

@app.route('/login', methods=['GET', 'POST'])
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
                return jsonify({'success': True, 'redirect': url_for('MFA')})
            return jsonify({'success': False, 'error': 'Failed to send verification email'})
            
        return jsonify({
            'success': False, 
            'error': 'Invalid email or password'
        })
    
    user_id, user, is_admin, is_company_admin = get_user_info()
    return render_template('login.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin)

@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    user_id, user, is_admin, is_company_admin = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin)
    
    return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies)

@app.route('/MFA', methods=['GET', 'POST'])
def MFA():
    if request.method == 'POST':
        token = request.form.get('verificationCode')
        if not token:
            return jsonify({'success': False, 'error': 'Verification code is required'})
            
        pending_login = session.get('pending_login')
        pending_registration = session.get('pending_registration')
        
        if pending_login:
            # Handle login MFA
            if user_controller.verify_token(token, pending_login['email']):
                session.pop('pending_login', None)
                session['id'] = pending_login['user_id']
                return jsonify({'success': True, 'redirect': url_for('home')})
            return jsonify({'success': False, 'error': 'Invalid verification code'})
            
        elif pending_registration:
            # Handle registration MFA
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
                        return jsonify({'success': True, 'redirect': url_for('home')})
                return jsonify({'success': False, 'error': 'Failed to create account'})
        
        return jsonify({'success': False, 'error': 'Session expired. Please try again.'})
        
    user_id, user, is_admin, is_company_admin = get_user_info()
    return render_template('MFA.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstName']
        surname = request.form['surname']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        phone_number = request.form['phone']
        birth_date = request.form['birthDate']
        id = uuid.uuid4().int & (1<<32)-1
        
        # Check if passwords match and pattern
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'})
        
        password_pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")
        if not password_pattern.match(password):
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character'})

        # Store registration data in session
        session['pending_registration'] = {
            'id': id,
            'email': email,
            'name': first_name,
            'surname': surname,
            'password': password,
            'phone_number': phone_number,
            'birth_date': birth_date
        }
        
        # Send verification email
        if user_controller.send_verification_email(email):
            return jsonify({'success': True, 'redirect': url_for('MFA')})
        return jsonify({'success': False, 'error': 'Failed to send verification email'})
    
    user_id, user, is_admin, is_company_admin = get_user_info()
    return render_template('register.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    pending_registration = session.get('pending_registration')
    if not pending_registration:
        return jsonify({'success': False, 'error': 'Session expired. Please register again.'})
    
    if user_controller.send_verification_email(pending_registration['email']):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to send verification email'})

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    tokens = user_controller.get_user_tokens(user_id)
    return render_template('dashboard.html', tokens=tokens, user_id=user_id)

@app.route('/add_token/<user_id>', methods=['POST'])
def add_token(user_id):
    token = request.form['token']
    user_controller.add_token_to_user(user_id, token)
    return redirect(url_for('dashboard', user_id=user_id))

@app.route('/search_companies', methods=['GET'])
def search_companies():
    user_id, user, is_admin, is_company_admin = get_user_info()
    search_query = request.args.get('query', '').strip()
    
    try:
        if search_query != "":
            companies = company_controller.search_companies(search_query)
            print(companies[0])
        else:
            companies = company_controller.get_all_companies_sorted()
            print(companies[1])
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'companies': companies})
        
        return render_template('search_companies.html', 
                             companies=companies, 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             search_query=search_query)
    except Exception as e:
        print(f"Error in search: {e}")
        return render_template('search_companies.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin)

@app.route('/information_company/<int:company_id>')
def information_company(company_id):
    user_id, user, is_admin, is_company_admin = get_user_info()
    try:
        company = company_controller.get_company_by_id(company_id)
        if company:
            return render_template('information_company.html',user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, company=company)
        return "Company not found", 404
    except Exception as e:
        print(f"Error fetching company details: {e}")
        return "Error loading company details", 500



@app.route('/password_recover', methods=['GET', 'POST'])
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
            print(f"Tokens after storing: {stored_tokens}")  # Debug print
            
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

@app.route('/password_recover_2/<token>', methods=['GET', 'POST'])
def password_recover_2(token):
    print(f"Accessing password_recover_2 with token: {token}")  # Debug print
    email = user_controller.validate_reset_token(token)
    print(email)
    
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
                'redirect': url_for('login')
            })
            
        return jsonify({
            'success': False,
            'error': 'Failed to update password'
        })
    
    return render_template('password_recover_2.html', token=token, email=email)

@app.route('/company_register', methods=['GET', 'POST'])
def company_register():
    user_id, user, is_admin, is_company_admin = get_user_info()
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Extract form data
            company_data = {
                'company_name': request.form['companyName'],
                'company_phone_number': request.form['phone'],
                'company_email': request.form['email'],
                'company_industry': request.form['industry'],
                'company_country': request.form['country'],
                'company_city': request.form['city'],
                'company_address': request.form['address'],
                'company_description': request.form['description'],
                'company_website': request.form.get('website'),
                'company_image': request.files.get('logo') if 'logo' in request.files else None
            }

            # Validate company name
            if company_controller.check_company_exists(company_data['company_name']):
                return jsonify({
                    'success': False,
                    'error': 'A company with this name already exists'
                })

            # Create company
            result = company_controller.create_company(**company_data)

            if result['success']:
                # Get user info for notification
                user = user_controller.get_user_by_id(user_id)
                if user:
                    company_controller.send_admin_notification(user, company_data)
                return jsonify({
                    'success': True,
                    'redirect': url_for('home')
                })
                
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create company')
            })

        except Exception as e:
            print(f"Error in company registration: {e}")
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred'
            })

    return render_template('company_register.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB in bytes
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE

# Inizializza geonamescache
gc = geonamescache.GeonamesCache()

@app.route('/get_countries', methods=['GET'])
def get_countries():
    # Prendi il termine di ricerca dalla query
    query = request.args.get('query', '')
    
    # Ottieni la lista di paesi
    countries = gc.get_countries()
    
    # Filtra i paesi che corrispondono al termine di ricerca
    filtered_countries = [
        {"id": country_code, "text": country_info['name']}
        for country_code, country_info in countries.items()
        if query.lower() in country_info['name'].lower()  # Controlla se il nome del paese contiene il termine
    ]
    
    return jsonify(filtered_countries)

@app.route('/get_cities', methods=['GET'])
def get_cities():
    country_code = request.args.get('country_code')  # Ottieni il codice del paese dalla query string
    if not country_code:
        return jsonify({'error': 'Country code is required'}), 400

    # Ottieni tutte le città dalla cache
    cities = gc.get_cities()

    # Aggiungi un controllo per verificare che i dati siano nel formato corretto
    if isinstance(cities, dict):
        cities_in_country = []
        for city_key, city in cities.items():
            if city['countrycode'] == country_code:
                cities_in_country.append(city['name'])
    else:
        return jsonify({'error': 'Data format is incorrect'}), 500

    return jsonify(cities_in_country)


@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = user_controller.get_user_by_id(user_id)
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/update_user', methods=['POST'])
def update_user():
    if not session.get('id'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
        
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    if not field or not value:
        return jsonify({'success': False, 'error': 'Missing data'})
        
    if user_controller.update_user_info(session['id'], field, value):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Update failed'})

if __name__ == '__main__':
    app.run(debug=True)