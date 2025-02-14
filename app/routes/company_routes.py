from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from app.controllers import company_controller, user_controller, notifications_controller
from app.routes.auth_routes import get_user_info
from werkzeug.utils import secure_filename
import os
import geonamescache
import uuid
import re

bp = Blueprint('company', __name__)
gc = geonamescache.GeonamesCache()

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

import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?\d{10,15}$'
    return re.match(pattern, phone) is not None

def validate_website(website):
    if not website:
        return True
    if not website.startswith('https://'):
        website = 'https://' + website
    return website.startswith('https://')

@bp.route('/company_register', methods=['GET', 'POST'])
def company_register():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not user_id:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            if 'id' not in session:
                return jsonify({'success': False, 'error': 'User not authenticated'})

            # Get user email for notification
            user = user_controller.get_user_by_id(session['id'])
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})
            
            company_id = uuid.uuid4().int & (1<<32)-1
            company_phone_number = request.form.get('phone')

            company_phone_pattern = re.compile(r'^\+?\d{10,15}$')
            if not company_phone_pattern.match(company_phone_number):
                return jsonify({'success': False, 'error': 'Invalid phone number format'})


            # Extract form data
            company_data = {
                'company_id': company_id,
                'company_name': request.form['companyName'],
                'company_phone_number': request.form['phone'],
                'company_email': request.form['email'],
                'company_industry': request.form['industry'],
                'company_country': request.form['country'],
                'company_city': request.form['city'],
                'company_address': request.form['address'],
                'company_description': request.form['description'],
                'company_website': request.form.get('website'),
                'company_image': request.files.get('logo') if 'logo' in request.files else None,
                'sender_email': user['email']  # Add sender email
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
                    notifications_controller.send_notification_to_admin('company registration', user['email'], company_id)
                return jsonify({
                    'success': True,
                    'redirect': url_for('main.home')
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

    return render_template('company_register.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, notifications = notifications)

@bp.route('/search_companies', methods=['GET'])
def search_companies():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    search_query = request.args.get('query', '').strip()
    
    try:
        if search_query != "":
            companies = company_controller.search_companies(search_query)
        else:
            companies = company_controller.get_all_companies_sorted()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'companies': companies})
        
        return render_template('search_companies.html', 
                             companies=companies, 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             search_query=search_query,
                             notifications = notifications,)
    except Exception as e:
        print(f"Error in search: {e}")
        return render_template('search_companies.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             notifications = notifications)

@bp.route('/information_company/<int:company_id>')
def information_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications= get_user_info()
    
    company = company_controller.get_company_by_id(company_id)
    info_of_admin = []
    info_of_admin=company_controller.get_admin_info_by_company(company_id)

    if company is None:
        return "Company not found", 404
        
    # Permetti la visualizzazione solo se la company è approvata o l'utente è admin
    if not company['status'] and not is_admin:
        return "Unauthorized", 403
        
    return render_template('information_company.html', 
                         company=company,
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         info_of_admin=info_of_admin,
                         is_company_admin=is_company_admin,
                         notifications = notifications)

@bp.route('/get_countries', methods=['GET'])
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

@bp.route('/get_cities', methods=['GET'])
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

@bp.route('/companies_of_administrator', methods=['GET'])
def companies_administrator():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    
    try:
        # Verifica se l'utente è un amministratore di alcune compagnie
        company_ids = company_controller.get_companyID_by_owner(user_id)  # Otteniamo gli ID delle compagnie
        # Ora otteniamo le informazioni complete per ogni company_id
        companies = []
        for company_id in company_ids:
            company = company_controller.get_company_by_id(company_id['company_id'])  # Otteniamo i dettagli della compagnia
            if company:
                companies.append(company)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'companies': companies})
        
        return render_template('manage_companies.html', 
                             companies=companies, 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             notifications=notifications)
    except Exception as e:
        print(f"Errore durante la ricerca delle compagnie: {e}")
        return render_template('manage_companies.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             notifications=notifications,
                             is_company_admin=is_company_admin)

@bp.route('/modify_company/<int:company_id>', methods=['GET', 'POST'])
def modify_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    
    company = company_controller.get_company_by_id(company_id)
    if company is None:
        return jsonify({"success": False, "error": "Company not found"}), 404

    if not company['status'] and not is_admin:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if request.method == 'POST':
        try:
            # Extract form data
            company_name = request.form.get('company_name')
            company_phone_number = request.form.get('company_phone_number')
            company_email = request.form.get('company_email')
            company_industry = request.form.get('company_industry')
            company_website = request.form.get('company_website')
            company_description = request.form.get('company_description')

            # Validation checks with user-friendly messages
            if len(company_name) < 2:
                return jsonify({"success": False, "error": "Company name must be at least 2 characters long"})

            if not validate_email(company_email):
                return jsonify({"success": False, "error": "Please enter a valid email address"})

            if not validate_phone(company_phone_number):
                return jsonify({"success": False, "error": "Please enter a valid phone number (+XX followed by 10-15 digits)"})

            if company_website and not validate_website(company_website):
                return jsonify({"success": False, "error": "Website URL must start with https://"})

            if len(company_description) > 1500:
                return jsonify({"success": False, "error": "Description must not exceed 1500 characters"})

            # Handle image upload with user-friendly messages
            company_logo = request.files.get('company_logo')
            company_image_url = None
            
            if company_logo and company_logo.filename != '':
                if not allowed_file(company_logo.filename):
                    return jsonify({"success": False, "error": "Please upload only JPG, PNG or GIF files"})
                
                if not validate_file_size(company_logo):
                    return jsonify({"success": False, "error": "Image size must not exceed 3MB"})
                    
                company_image_url = company_controller.upload_company_image(company_id, company_logo)

            # Update company
            company_controller.update_company(
                company_id=company_id,
                company_name=company_name,
                company_phone_number=company_phone_number,
                company_email=company_email,
                company_industry=company_industry,
                company_website=company_website,
                company_description=company_description,
                company_image=company_image_url
            )
            
            return jsonify({"success": True})

        except Exception as e:
            return jsonify({"success": False, "error": "An unexpected error occurred. Please try again."}), 200  # Note: 200 status to allow toast to show

    return render_template('modify_company.html', 
                         company=company,
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         is_company_admin=is_company_admin,
                         notifications=notifications)


@bp.route('/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    
    success = company_controller.delete_company(company_id)
    return jsonify({'success': success, 'error': None if success else 'Failed to delete company'})
