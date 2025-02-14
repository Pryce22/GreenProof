from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.controllers import user_controller, company_controller, notifications_controller
from app.routes.auth_routes import get_user_info
import re
from datetime import datetime, date

bp = Blueprint('user', __name__)

# Add validation functions
def validate_email(email):
    pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return bool(pattern.match(email))

def validate_name(name):
    pattern = re.compile(r'^[A-Za-z]{2,50}$')
    return bool(pattern.match(name))

def validate_phone_number(phone):
    pattern = re.compile(r'^\+?\d{10,15}$')
    return bool(pattern.match(phone))

def validate_birthday(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = date.today()
        age = (today - birth_date).days / 365
        return birth_date <= today and age >= 16
    except ValueError:
        return False

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
                    'company_id': notification[6]
                }
            else:
                notification_dict = notification

            # Add company name
            if notification_dict.get('company_id'):
                company = company_controller.get_company_by_id(notification_dict['company_id'])
                notification_dict['company_name'] = company['company_name'] if company else 'Unknown Company'
                notification_dict['company'] = company  # Add the entire company object
            
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

@bp.route('/handle_invitation/<notification_id>/<action>', methods=['POST'])
def handle_invitation(notification_id, action):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
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

@bp.route('/manage_employee', methods=['GET', 'POST'])
def manage_employee():
    # Ottieni informazioni sull'utente
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()

    # Verifica se l'utente è autenticato
    if not user_id:
        return redirect(url_for('login'))

    # Ottieni le company_id per l'utente
    companies = user_controller.get_companies_by_user_id(user_id)
    info_company = user_controller.get_companies_information_by_user_id(user_id)
    
    search_query = request.args.get('search_query', '').strip()
    
    # Se l'utente è un amministratore di una compagnia
    if is_company_admin:
        unique_company_admin = user_controller.is_unique_company_admin(user_id)
        unique_admin = user_controller.get_company_ids_where_user_is_unique_admin(user_id)

        # Ottieni i dettagli degli employee per le compagnie dell'utente
        if search_query:
            employees_by_name_or_surname = user_controller.get_users_by_name_or_surname(search_query)
            
            all_employees=user_controller.get_employees_by_companies(user_id)
           
            # Filtra solo i dipendenti che appartengono a una delle aziende dell'utente
            employees = [employee for employee in all_employees
                        if any(emp['id'] == employee['id'] for emp in employees_by_name_or_surname)]
            
        else:
            employees = user_controller.get_employees_by_companies(user_id)

        email = user_controller.get_all_user_emails()
        
        # Passa tutte le informazioni alla template
        return render_template('manage_employee.html',
                               user_id=user_id,
                               user=user,
                               is_admin=is_admin,
                               is_company_admin=is_company_admin,
                               unique_company_admin=unique_company_admin,
                               companies=companies,
                               unique_admin=unique_admin,
                               employees=employees,
                               info_company=info_company,
                               email=email,
                               notifications=notifications)

    # Se non è amministratore di una compagnia, solo le informazioni di base
    return render_template('manage_employee.html',
                           user_id=user_id,
                           user=user,
                           is_admin=is_admin,
                           is_company_admin=is_company_admin,
                           companies=companies,
                           info_company=info_company,
                           email=email,
                           notifications=notifications)



@bp.route('/send_company_invitation', methods=['POST'])
def send_company_invitation():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not user_id or not is_company_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    company_id = data.get('company_id')
    receiver_email = data.get('email')
    
    if not company_id or not receiver_email:
        return jsonify({'success': False, 'error': 'Missing data'})
    
    # Verify if the email exists in the database
    if not user_controller.check_email_exists(receiver_email):
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
    

@bp.route('/mark_notification_read/<notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    try:
        success = notifications_controller.mark_as_read(notification_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error in mark_notification_read: {e}")
        return jsonify({'success': False, 'error': str(e)})
    

@bp.route('/delete_employee', methods=['POST'])
def delete_employee_route():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        company_id = data.get('company_id')

        response = user_controller.delete_employee(user_id, company_id)
        
        # Se la risposta della funzione di eliminazione è positiva, ritorniamo success
        if response:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete employee'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})