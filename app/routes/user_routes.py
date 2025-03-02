from flask import Blueprint, json, render_template, request, redirect, url_for, session, jsonify
from app.controllers import user_controller, company_controller, notifications_controller
from app.routes.auth_routes import get_user_info
import re
from datetime import datetime, date

bp = Blueprint('user', __name__)

# Add validation functions
def validate_email(email):
    pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return bool(pattern.match(email))

# validation function for name and surname
def validate_name(name):
    pattern = re.compile(r'^[A-Za-z]{2,50}$')
    return bool(pattern.match(name))

# validation function for phone number
def validate_phone_number(phone):
    pattern = re.compile(r'^\+?\d{10,15}$')
    return bool(pattern.match(phone))

# validation function for birthday
def validate_birthday(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = date.today()
        age = (today - birth_date).days / 365
        return birth_date <= today and age >= 16
    except ValueError:
        return False

# validation function for all fields
def validate_field(field, value):
    validators = {
        'email': (validate_email, 'Invalid email format'),
        'name': (validate_name, 'Name must be between 2 and 50 characters and contain only letters'),
        'surname': (validate_name, 'Surname must be between 2 and 50 characters and contain only letters'),
        'phone_number': (validate_phone_number, 'Invalid phone number format'),
        'birthday': (validate_birthday, 'Invalid birthday or user must be at least 16 years old')
    }

    if field not in validators:
        return True, None

    validator_func, error_message = validators[field]
    is_valid = validator_func(value)
    return is_valid, error_message if not is_valid else None

# Route for user profile
@bp.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin, notifications = notifications)
    
    return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies, notifications = notifications)

# Route for notifications
@bp.route('/notifications', methods=['GET'])
def notifications():
    user_id, user, is_admin, is_company_admin, notifications= get_user_info()
    if not user_id:
        return redirect(url_for('auth.login'))
    
    notifications_info = notifications_controller.get_notifications_by_email(user['email'])
    if notifications_info:
        processed_notifications = []
        for notification in notifications_info:
            # Convert to dictionary if it's a tuple
            if isinstance(notification, tuple):
                notification_dict = {
                    'id_notification': notification[0],
                    'created_at': notification[1],
                    'type': notification[2],
                    'sender_email': notification[3],
                    'receiver_email': notification[4],
                    'status': notification[5],
                    'company_id': notification[6],
                    'product_request_id' : notification[7]
                }
            else:
                notification_dict = notification

            # Add company name
            if notification_dict.get('company_id'):
                company = company_controller.get_company_by_id(notification_dict['company_id'])
                notification_dict['company_name'] = company['company_name'] if company else 'Unknown Company'
                notification_dict['company'] = company  # Add the entire company object

            if notification_dict.get('product_request_id'):
                product_request = company_controller.get_product_request_by_id(notification_dict['product_request_id'])
                if product_request:
                    notification_dict['product_request_quantity'] = product_request['quantity_of_raw_material'] # Aggiungi le informazioni sulla product_request
                    notification_dict['product_request_km'] = product_request['distance_to_travel']
                    notification_dict['product_request_date'] = product_request['transport_date']
                    notification_dict['product_supplier_approve'] = product_request['supplier_approve']
                    notification_dict['product_transporter_approve'] = product_request['transporter_approve']
                    notification_dict['request_id']= product_request['id']

                    id_buyer= product_request['id_buyer']
                    id_supplier= product_request['id_supplier']
                    buyer=company_controller.get_company_by_id(id_buyer)
                    supplier= company_controller.get_company_by_id(id_supplier)
                    notification_dict['buyer']=buyer['company_name']
                    notification_dict['supplier']=supplier['company_name']


                    product_id = product_request['id_raw_material']
                    product_info = company_controller.get_products_by_id(product_id)
                    if product_info:
                        notification_dict['product_name']=product_info['name']
                        
                    else:
                        notification_dict['product'] = None
                else:
                    notification_dict['product_request'] = None

            processed_notifications.append(notification_dict)
    else:
        processed_notifications = []
   
    
    return render_template('notifications.html',
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         is_company_admin=is_company_admin,
                         notifications=notifications,
                         notifications_info=processed_notifications)

# Route for approving supplier
@bp.route("/approve_supplier/<int:product_request_id>", methods=["POST"])
def approve_supplier_route(product_request_id):
    try:
        response = company_controller.approve_supplier(product_request_id)
        company_controller.update_product_quantity_after_approval(product_request_id)
       
        if company_controller.check_approval_status(product_request_id):
            company_controller.add_transport_record_from_product_request(product_request_id)
            notifications_controller.create_notifications_for_product_request(product_request_id)
            company_controller.update_total_quantity_co2_emission_processor(product_request_id)

            if company_controller.check_equal_status_of_request_product(product_request_id):
                company_controller.update_or_insert_chain_product_for_seller(product_request_id)
                company_controller.insert_product_seller(product_request_id)
            else:
                company_controller.update_quantity_of_processed_product(product_request_id)
                company_controller.update_or_insert_chain_product(product_request_id)
                
        
        if response:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Update failed"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Route for approving transporter 
@bp.route("/approve_transporter/<int:transport_request_id>", methods=["POST"])
def approve_transporter_route(transport_request_id):
    try:
        response = company_controller.approve_transporter(transport_request_id)

        if company_controller.check_approval_status(transport_request_id):
            company_controller.add_transport_record_from_product_request(transport_request_id)
            notifications_controller.create_notifications_for_product_request(transport_request_id)
            company_controller.update_total_quantity_co2_emission_processor(transport_request_id)
        
            if company_controller.check_equal_status_of_request_product(transport_request_id):
                company_controller.update_or_insert_chain_product_for_seller(transport_request_id)
                company_controller.insert_product_seller(transport_request_id)
            else:
                company_controller.update_quantity_of_processed_product(transport_request_id)
                company_controller.update_or_insert_chain_product(transport_request_id)
   

        if response:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Update failed"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Route for rejecting supplier
@bp.route('/reject_supplier/<int:request_id>', methods=['POST'])
def reject_supplier(request_id):
    try:
        success = company_controller.reject_supplier(request_id)
        notifications_controller.create_notifications_for_reject_request(request_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Route for rejecting transporter
@bp.route('/reject_transporter/<int:request_id>', methods=['POST'])
def reject_transporter(request_id):
    try:

        success = company_controller.reject_transporter(request_id)
        notifications_controller.create_notifications_for_reject_request(request_id)
        check= company_controller.check_supplier_approve(request_id)
        check= check.data[0]['quantity_of_raw_material']
        if check or check == 0:
            id_product=company_controller.id_product_from_request(request_id)
            id_product=id_product.data[0]['id_product']
            company_controller.update_quantity_after_reject(id_product, check)
            
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Route for updating user information 
@bp.route('/update_user', methods=['POST'])
def update_user():
    if not session.get('id'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
        
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    if not field or value is None:
        return jsonify({'success': False, 'error': 'Missing data'})

    # Validate the field
    is_valid, error_message = validate_field(field, value)
    if not is_valid:
        return jsonify({'success': False, 'error': error_message})

    # Additional email-specific checks
    if field == 'email':
        # Check if email already exists
        if user_controller.check_email_exists(value):
            return jsonify({'success': False, 'error': 'Email already in use'})
            
        # Update the email
        if user_controller.update_user_info(session['id'], field, value):
            # Clear the session to force logout
            session.clear()
            return jsonify({'success': True, 'requireLogout': True})
            
    # For all other fields
    if user_controller.update_user_info(session['id'], field, value):
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'error': 'Update failed'})

# Route for handling company invitations
@bp.route('/handle_invitation/<notification_id>/<action>', methods=['POST'])
def handle_invitation(notification_id, action):
    user_id, _, _, _, _ = get_user_info()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get notification details
        notification = notifications_controller.get_notification_by_id(notification_id)
        if not notification:
            return jsonify({'success': False, 'error': 'Invitation not found'})

        
        if action == 'accept':
            # Create company-user relationship
            success = user_controller.accept_invitation(notification['receiver_email'], notification['sender_email'], notification['company_id'])
        
        elif action == 'reject':
            # Create rejection notification for company admin
            success = user_controller.reject_invitation(notification['receiver_email'], notification['sender_email'], notification['company_id'])
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        # If action was successful, delete the invitation notification
        if success:
            notifications_controller.delete_notification(notification_id)
            return jsonify({'success': True})
            
        return jsonify({'success': False, 'error': 'Failed to process invitation'})
        
    except Exception as e:
        print(f"Error handling invitation: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'})

# Route for managing employees
@bp.route('/manage_employee', methods=['GET', 'POST'])
def manage_employee():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()

    if not user_id:
        return redirect(url_for('login'))

    companies = user_controller.get_companies_by_user_id(user_id)
    
    info_company = user_controller.get_companies_information_by_user_id(user_id)
    
    search_query = request.args.get('search_query', '').strip()

    email = user_controller.get_all_user_emails()
    
    if is_company_admin:
        unique_company_admin = user_controller.is_unique_company_admin(user_id)
        unique_admin = user_controller.get_company_ids_where_user_is_unique_admin(user_id)

        if search_query:
            employees_by_name_or_surname = user_controller.get_users_by_name_or_surname(search_query)
            
            all_employees=user_controller.get_employees_by_companies(user_id)
           
            employees = [employee for employee in all_employees
                        if any(emp['id'] == employee['id'] for emp in employees_by_name_or_surname)]
            
        else:
            employees = user_controller.get_employees_by_companies(user_id)

        employees_json=json.dumps(employees)

        return render_template('manage_employee.html',
                               user_id=user_id,
                               user=user,
                               is_admin=is_admin,
                               is_company_admin=is_company_admin,
                               unique_company_admin=unique_company_admin,
                               companies=companies,
                               unique_admin=unique_admin,
                               employees=employees,
                               employees_json=employees_json,
                               info_company=info_company,
                               email=email,
                               notifications=notifications)

    return render_template('manage_employee.html',
                           user_id=user_id,
                           user=user,
                           is_admin=is_admin,
                           is_company_admin=is_company_admin,
                           companies=companies,
                           info_company=info_company,
                           email=email,
                           notifications=notifications)


# Route for sending company invitation
@bp.route('/send_company_invitation', methods=['POST'])
def send_company_invitation():
    user_id, user, _, is_company_admin, _ = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    company_id = data.get('company_id')
    receiver_email = data.get('email')
    
    is_him = user['email'] == receiver_email
    if is_him:
        return jsonify({'success': False, 'error': 'You cannot invite yourself'})
    
    if not company_id or not receiver_email:
        return jsonify({'success': False, 'error': 'Missing data'})
    
    # Verify if the email exists in the database
    if not user_controller.check_email_exists(receiver_email) or user_controller.check_user_by_email_if_is_admin(receiver_email):
        return jsonify({'success': False, 'error': 'User email not found'})
    
    # Create a company invitation notification
    success = notifications_controller.create_notification(
        type='company_invitation',
        sender=user['email'],
        receiver=receiver_email,
        company_id=company_id
    )
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to create invitation'})
    
# Route for marking notification as read
@bp.route('/mark_notification_read/<notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    try:
        success = notifications_controller.mark_as_read(notification_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error in mark_notification_read: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
# Route for deleting employee
@bp.route('/delete_employee', methods=['POST'])
def delete_employee_route():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        company_id = data.get('company_id')

        response = user_controller.delete_employee(user_id, company_id)
        
        if response:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete employee'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Route for promoting employee to admin
@bp.route('/promote_to_admin', methods=['POST'])
def promote_to_admin():
    try:
        # Get data from the request
        data = request.get_json()
        employee_id = data.get('employee_id')
        company_id = data.get('company_id')

        # Verify that the data is provided
        if not employee_id or not company_id:
            return jsonify({"error": "employee_id and company_id are required"}), 400

        # Call the function to promote the user to admin
        success = user_controller.set_company_admin(company_id, employee_id)
        # Return a response based on the success of the operation
        if success:
            return jsonify({"message": "Employee successfully promoted to admin."}), 200
        else:
            return jsonify({"error": "An error occurred during promotion."}), 500

    except Exception as e:
        print(f"Error in route: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Route for submitting Ethereum address
@bp.route('/submit_eth_address', methods=['POST'])
def submit_eth_address():
    user_id, _, _, is_company_admin, _ = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        data = request.get_json()
        eth_address = data.get('eth_address')
        company_id = data.get('company_id')
        
        if not eth_address or not company_id:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Validate ETH address format
        if not re.match(r'^0x[a-fA-F0-9]{40}$', eth_address):
            return jsonify({'success': False, 'error': 'Invalid Ethereum address format'})
        
        # Check uniqueness
        if not company_controller.check_eth_address_unique(eth_address, company_id):
            return jsonify({'success': False, 'error': 'ETH address already in use'})
        
        # Update company ETH address
        success = company_controller.update_company_eth_address(company_id, eth_address)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update ETH address'})
            
    except Exception as e:
        print(f"Error submitting ETH address: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'})
    
# Route for searching products
@bp.route('/search_product', methods=['GET'])
def search_product():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    search_query = request.args.get('query', '').strip()
    
    try:
        
        companies = company_controller.get_sellers_with_products()
        
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'companies': companies})
        
        return render_template('products_views.html', 
                             companies=companies, 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             search_query=search_query,
                             notifications = notifications,)
    except Exception as e:
        print(f"Error in search: {e}")
        return render_template('products_views.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             notifications = notifications)

# Route for viewing products of a seller    
@bp.route('/product_of_seller/<int:company_id>', methods=['GET'])
def product_of_seller(company_id):
    # Retrieve user and company details
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
   
    info_company = company_controller.get_company_by_id(company_id)
    products = company_controller.get_products_by_seller(company_id)

    
    grouped_products = {}

    for product in products.data:
        info_product = company_controller.get_information_by_id_product(product['id_product'])
        companies_of_production = company_controller.get_companies_of_chain_product(product['id_product'], company_id)

        product_name = info_product.data[0]['name'].lower()


        
        if product_name not in grouped_products:
            grouped_products[product_name] = {
                'company_id': info_company['company_id'],
                'company_name': info_company['company_name'],
                'company_email': info_company['company_email'],
                'company_phone_number': info_company['company_phone_number'],
                'company_country': info_company['company_country'],
                'company_city': info_company['company_city'],
                'company_address': info_company['company_address'],
                'company_image': info_company['company_image'],
                'product_id': product['id_product'],
                'product_quantity': product['quantity'],
                'product_name': info_product.data[0]['name'],
                'product_description': info_product.data[0]['description'],
                'farmer_names': set(),
                'transformer_names': set(),
                'transporter1_names': set(),
                'transporter2_names': set(),
                'serial_ids': set(),
                'co2_emission': 0,
                'company_emissions': {}
            }
        
        for comp in companies_of_production.data:
            if comp['farmer']:
                farmer_id = comp['farmer']
                farmer_name = company_controller.get_company_by_id(farmer_id)['company_name']
                grouped_products[product_name]['farmer_names'].add(farmer_name)
                
                farmer_emission = company_controller.get_company_co2_contribution(farmer_id, product['id_product'])
                grouped_products[product_name]['company_emissions'][farmer_name] = farmer_emission
                
            if comp['transformer']:
                transformer_id = comp['transformer']
                transformer_name = company_controller.get_company_by_id(transformer_id)['company_name']
                grouped_products[product_name]['transformer_names'].add(transformer_name)
                
                transformer_emission = company_controller.get_company_co2_contribution(transformer_id, product['id_product'])
                grouped_products[product_name]['company_emissions'][transformer_name] = transformer_emission

            if comp['transporter1']:
                transporter1_id = comp['transporter1']
                transporter1_name = company_controller.get_company_by_id(transporter1_id)['company_name']
                grouped_products[product_name]['transporter1_names'].add(transporter1_name)
                
                transporter1_emission = company_controller.get_company_co2_contribution(transporter1_id, product['id_product'])
                grouped_products[product_name]['company_emissions'][transporter1_name] = transporter1_emission
                
            if comp['transporter2']:
                transporter2_id = comp['transporter2']
                transporter2_name = company_controller.get_company_by_id(transporter2_id)['company_name']
                grouped_products[product_name]['transporter2_names'].add(transporter2_name)
                
                transporter2_emission = company_controller.get_company_co2_contribution(transporter2_id, product['id_product'])
                grouped_products[product_name]['company_emissions'][transporter2_name] = transporter2_emission
            
            seller_emission = company_controller.get_company_co2_contribution(company_id, product['id_product'])
            grouped_products[product_name]['company_emissions'][info_company['company_name']] = seller_emission
            
            grouped_products[product_name]['serial_ids'].add(comp['serial_id'])

    for product in grouped_products.values():
        total_co2 = sum(product['company_emissions'].values())
        product['co2_emission'] = total_co2

        product['farmer_names'] = list(product['farmer_names'])
        product['transformer_names'] = list(product['transformer_names'])
        product['transporter1_names'] = list(product['transporter1_names'])
        product['transporter2_names'] = list(product['transporter2_names'])
        product['serial_ids'] = list(product['serial_ids'])
    
    return render_template('product_of_seller.html', 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin,
                             product_info_list=list(grouped_products.values()), 
                             company_id=company_id,
                             is_company_admin=is_company_admin,
                             notifications=notifications)
