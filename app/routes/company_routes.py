from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.controllers import company_controller, user_controller
from app.routes.auth_routes import get_user_info
from werkzeug.utils import secure_filename
import os
import geonamescache

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

@bp.route('/company_register', methods=['GET', 'POST'])
def company_register():
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
    if not user_id:
        return redirect(url_for('auth.login'))
    
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

    return render_template('company_register.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, pending_companies_count=pending_companies_count)

@bp.route('/search_companies', methods=['GET'])
def search_companies():
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
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
                             pending_companies_count=pending_companies_count)
    except Exception as e:
        print(f"Error in search: {e}")
        return render_template('search_companies.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin)

@bp.route('/information_company/<int:company_id>')
def information_company(company_id):
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
    
    company = company_controller.get_company_by_id(company_id)
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
                         is_company_admin=is_company_admin,
                         pending_companies_count=pending_companies_count)

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
