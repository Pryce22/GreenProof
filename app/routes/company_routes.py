from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from app.controllers import company_controller, user_controller, notifications_controller, eth_account_controller
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
    if company is None:
        return "Company not found", 404

    # Get real-time token balance from blockchain
    token_balance = 0
    if company.get('eth_address'):
        token_balance = eth_account_controller.get_token_balance(company['eth_address'])
    
    info_of_admin = company_controller.get_admin_info_by_company(company_id)
        
    # Permetti la visualizzazione solo se la company è approvata o l'utente è admin
    if not company['status'] and not is_admin:
        return "Unauthorized", 403

    # Get token balance if ETH address exists
    token_balance = 0
    if company.get('eth_address'):
        token_balance = eth_account_controller.get_token_balance(company['eth_address'])
        
    return render_template('information_company.html', 
                         company=company,
                         token_balance=token_balance,
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
            # Get existing company data
            existing_company = company_controller.get_company_by_id(company_id)
            
            # Merge form data with existing data (keep existing values if not in form)
            company_data = {
                'company_name': request.form.get('company_name', existing_company['company_name']),
                'company_phone_number': request.form.get('company_phone_number', existing_company['company_phone_number']),
                'company_email': request.form.get('company_email', existing_company['company_email']),
                'company_industry': request.form.get('company_industry', existing_company['company_industry']),
                'company_website': request.form.get('company_website', existing_company['company_website']),
                'company_description': request.form.get('company_description', existing_company['company_description'])
            }

            # Only validate fields that are actually being updated
            if company_data['company_name'] != existing_company['company_name']:
                if len(company_data['company_name']) < 2:
                    return jsonify({"success": False, "error": "Company name must be at least 2 characters long"})

            if company_data['company_email'] != existing_company['company_email']:
                if not validate_email(company_data['company_email']):
                    return jsonify({"success": False, "error": "Please enter a valid email address"})

            if company_data['company_phone_number'] != existing_company['company_phone_number']:
                if not validate_phone(company_data['company_phone_number']):
                    return jsonify({"success": False, "error": "Please enter a valid phone number (+XX followed by 10-15 digits)"})

            if company_data['company_website'] != existing_company['company_website']:
                if company_data['company_website'] and not validate_website(company_data['company_website']):
                    return jsonify({"success": False, "error": "Website URL must start with https://"})

            if company_data['company_description'] != existing_company['company_description']:
                if len(company_data['company_description']) > 1500:
                    return jsonify({"success": False, "error": "Description must not exceed 1500 characters"})

            # Handle image upload separately
            if 'company_logo' in request.files and request.files['company_logo'].filename:
                file = request.files['company_logo']
                if not allowed_file(file.filename):
                    return jsonify({"success": False, "error": "Invalid file type"})
                if not validate_file_size(file):
                    return jsonify({"success": False, "error": "File size must not exceed 3MB"})
                try:
                    company_image_url = company_controller.upload_company_image(company_id, file)
                    if company_image_url:
                        company_data['company_image'] = company_image_url
                    else:
                        return jsonify({"success": False, "error": "Failed to upload image"})
                except Exception as e:
                    print(f"Error uploading image: {e}")
                    return jsonify({"success": False, "error": "Failed to upload image"})
            else:
                # Keep existing image
                company_data['company_image'] = existing_company.get('company_image')

            # Update company with merged data
            result = company_controller.update_company(company_id, **company_data)
            if result.get('success'):
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": result.get('message', "Failed to update company")})

        except Exception as e:
            print(f"Error in modify_company: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return render_template('modify_company.html', 
                         company=company,
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         is_company_admin=is_company_admin,
                         notifications=notifications)

@bp.route('/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    success = company_controller.delete_company_notification(user["email"],company_id)
    return jsonify({'success': success, 'error': None if success else 'Failed to delete company'})

@bp.route('/check_eth_address', methods=['GET'])
def check_eth_address():
    eth_address = request.args.get('address')
    company_id = request.args.get('company_id')
    
    if not eth_address:
        return jsonify({'available': False, 'error': 'No address provided'})
        
    # Validate format
    if not re.match(r'^0x[a-fA-F0-9]{40}$', eth_address):
        return jsonify({'available': False, 'error': 'Invalid address format'})
        
    # Check uniqueness
    is_unique = company_controller.check_eth_address_unique(eth_address, company_id)
    return jsonify({'available': is_unique})

@bp.route('/manage_tokens', methods=['GET', 'POST'])
def manage_tokens():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    
    # Recupera gli ID delle aziende di cui l'utente è admin
    company_ids = company_controller.get_companyID_by_owner(user_id)
    companies = []
    for cid in company_ids:
        comp = company_controller.get_company_by_id(cid['company_id'])
        if comp['eth_address'] != 'no address' and comp['eth_address'] != None:
            companies.append(comp)

    if len(companies) == 1:
        return redirect(url_for('company.manage_tokens_detail', company_id=companies[0]['company_id']))
    
    if request.method == 'POST':
        # Quando l'utente seleziona un'azienda dal form
        selected_company_id = request.form.get('company_id')
        return redirect(url_for('company.manage_tokens_detail', company_id=selected_company_id))
    
    return render_template('select_company_to_manage_tokens.html',
                           companies=companies,
                           user_id=user_id,
                           user=user,
                           is_admin=is_admin,
                           is_company_admin=is_company_admin,
                           notifications=notifications)

@bp.route('/manage_tokens_details/<int:company_id>', methods=['GET', 'POST'])
def manage_tokens_detail(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    
    company = company_controller.get_company_by_id(company_id)
    if company is None:
        return "Company not found", 404

    # Controlla autorizzazioni
    if not company['status'] and not is_admin:
        return "Unauthorized", 403

    current_page = request.args.get("page", default=1, type=int)
    token_balance = 0
    transactions = []
    total_pages = 1  # Default value
    
    if company.get('eth_address'):
        token_balance = eth_account_controller.get_token_balance(company['eth_address'])
        # Use get_paginated_transactions instead of get_transactions_for_company
        transactions, total_pages = eth_account_controller.get_paginated_transactions(
            company['eth_address'], 
            page=current_page
        )

    # Create a sliding window of page numbers (show max 4 pages)
    if total_pages <= 4:
        page_numbers = list(range(1, total_pages + 1))
    else:
        if current_page <= 2:
            page_numbers = list(range(1, 5))
        elif current_page >= total_pages - 1:
            page_numbers = list(range(total_pages - 3, total_pages + 1))
        else:
            page_numbers = list(range(current_page - 1, current_page + 3))

    return render_template('manage_token.html', 
                         company=company,
                         token_balance=token_balance,
                         transactions=transactions,
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         is_company_admin=is_company_admin,
                         notifications=notifications,
                         current_page=current_page,
                         total_pages=total_pages,
                         page_numbers=page_numbers)

@bp.route('/check_available_companies/<int:company_id>')
def check_available_companies(company_id):
    amount = request.args.get('amount', type=float)
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400
        
    companies = eth_account_controller.find_companies_with_sufficient_tokens(amount)
    companies = [c for c in companies if c['company_id'] != company_id]
    
    return jsonify({'companies': companies})

@bp.route('/submit_token_request', methods=['POST'])
def submit_token_request():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})

    data = request.get_json()
    amount = data.get('amount')
    receiver_address = data.get('receiver_address')
    sender_company_id = data.get('company_id')
    sender_id = data.get('user_id')

    try:
        # Get receiver company details
        receiver_company = company_controller.get_company_by_eth_address(receiver_address)
        if not receiver_company:
            return jsonify({'success': False, 'error': 'Receiver company not found'})

        # Get sender company details for notification
        sender_company = company_controller.get_company_by_id(sender_company_id)
        if not sender_company:
            return jsonify({'success': False, 'error': 'Sender company not found'})
        
        sender_email = user_controller.get_user_by_id(sender_id)['email']
        same_request = uuid.uuid4().int & (1<<32)-1

        # Create notification for receiver company admins
        success = company_controller.create_token_request_notification(
            sender_email = sender_email,
            sender_company_id=sender_company_id,
            receiver_company_id=receiver_company['company_id'],
            amount=amount,
            same_request=same_request
        )

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to create token request'})

    except Exception as e:
        print(f"Error submitting token request: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/approve_token_request/<notification_id>', methods=['POST'])
def approve_token_request(notification_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})

    try:
        # Get notification details
        notification = notifications_controller.get_notification_by_id(notification_id)
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'})

        # Get sender and receiver company details
        

        sender_company = company_controller.get_company_by_id(notification['sender_company_id'])
        receiver_company = company_controller.get_company_by_id(notification['company_id'])
        
        if not sender_company or not receiver_company:
            return jsonify({'success': False, 'error': 'Company information not found'})

        # Verify sender's ETH address exists
        if not sender_company.get('eth_address'):
            return jsonify({'success': False, 'error': 'Sender company has no ETH address'})

        # Verify receiver's ETH address exists and matches connected MetaMask account
        if not receiver_company.get('eth_address'):
            return jsonify({'success': False, 'error': 'Your company has no ETH address'})

        # Prepare transaction data
        transfer_data = eth_account_controller.initiate_token_transfer(
            receiver_company['eth_address'],
            sender_company['eth_address'],
            notification['requested_token']
        )
        
        if not transfer_data['success']:
            return jsonify({'success': False, 'error': transfer_data.get('error', 'Failed to prepare transaction')})

        # Return transaction data for MetaMask to sign
        return jsonify({
            'success': True,
            'transaction': transfer_data['tx_data'],
            'notification_id': notification_id
        })

    except Exception as e:
        print(f"Error in approve_token_request: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/complete_token_transfer/<notification_id>', methods=['POST'])
def complete_token_transfer(notification_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})

    try:
        data = request.get_json()
        tx_hash = data.get('transactionHash')
        
        if not tx_hash:
            return jsonify({'success': False, 'error': 'No transaction hash provided'}) 

        # Delete notification for all admins
        success = notifications_controller.delete_notification_for_all_admin_company(notification_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update notification status'})

    except Exception as e:
        print(f"Error completing token transfer: {e}")
        return jsonify({'success': False, 'error': str(e)})