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

@app.route('/')
def home():
    user_id = session.get('id')
    user = None
    if user_id:
        user = user_controller.get_user_by_id(user_id)
    return render_template('index.html', user_id=user_id, user=user)

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
    
    return render_template('login.html')

@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
     user_id = session.get('id')
     user = user_controller.get_user_by_id(user_id) if user_id else None
     return render_template('user_profile.html', user_id=user_id, user=user)

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
        
    return render_template('MFA.html')

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
    
    return render_template('register.html')

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

@app.route('/search_companies', methods=['GET', 'POST'])
def seach_companies():
    user_id = session.get('id')
    user = user_controller.get_user_by_id(user_id) if user_id else None
    return render_template('search_companies.html', user_id=user_id, user=user)

@app.route('/information_company', methods=['GET', 'POST'])
def information_company():
    user_id = session.get('id')
    user = user_controller.get_user_by_id(user_id) if user_id else None
    return render_template('information_company.html', user_id=user_id, user=user) 


@app.route('/password_recover', methods=['GET', 'POST'])
def password_recover():
    return render_template('password_recover.html')

@app.route('/company_register', methods=['GET', 'POST'])
def company_register():
    user_id = session.get('id')
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

    user = user_controller.get_user_by_id(user_id) if user_id else None
    return render_template('company_register.html', user_id=user_id, user=user)

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

if __name__ == '__main__':
    app.run(debug=True)