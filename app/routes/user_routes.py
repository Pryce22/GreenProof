from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.controllers import user_controller, company_controller, notifications_controller
from app.routes.auth_routes import get_user_info

bp = Blueprint('user', __name__)

@bp.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    user_id, user, is_admin, is_company_admin, notifications, pending_companies_count = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin, notifications = notifications, pending_companies_count=pending_companies_count)
    
    return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies, notifications = notifications, pending_companies_count=pending_companies_count)


@bp.route('/notifications', methods=['GET'])
def notifications():
    user_id, user, is_admin, is_company_admin, notifications, pending_companies_count = get_user_info()
    if not user_id:
        return redirect(url_for('auth.login'))
    
    notifications_info = notifications_controller.get_notifications_by_email(user['email'])
 

    return render_template('notifications.html',
                         user_id=user_id,
                         user=user,
                         is_admin=is_admin,
                         is_company_admin=is_company_admin,
                         notifications=notifications,
                         notifications_info=notifications_info)


@bp.route('/update_user', methods=['POST'])
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

@bp.route('/handle_invitation/<notification_id>/<action>', methods=['POST'])
def accept_invitation(notification_id, action):
    user_id, user, is_admin, is_company_admin, notifications, pending_companies_count = get_user_info()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get notification details
        notification = notifications_controller.get_notification_by_id(notification_id)
        if not notification:
            return jsonify({'success': False, 'error': 'Invitation not found'})
        
        sender_email = notification['receiver_email']
        receiver_email = notification['sender_email']
        company_id = notification['company_id']
        
        # Handle different actions
        if action == 'accept':
            success = user_controller.accept_invitation(sender_email, receiver_email, company_id)
        elif action == 'reject':
            success = user_controller.reject_invitation(sender_email, receiver_email, company_id)
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        # If action was successful, delete the notification
        if success:
            notifications_controller.delete_notification(notification_id)
            
        return jsonify({'success': success})
        
    except Exception as e:
        print(f"Error handling invitation: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'})


@bp.route('/manage_employee', methods=['GET', 'POST'])
def manage_employee():
    user_id, user, is_admin, is_company_admin, notifications, pending_companies_count = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('manage_employee.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin, pending_companies_count=pending_companies_count)
    
    return render_template('manage_employee.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies, pending_companies_count=pending_companies_count)

