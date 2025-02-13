from flask import Blueprint, render_template, redirect, url_for, jsonify, g
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller
from app.controllers import notifications_controller

bp = Blueprint('admin', __name__)


@bp.route('/company/approve/<int:company_id>', methods=['POST'])
def approve_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    success = company_controller.approve_company(company_id)
    return jsonify({'success': success, 'error': None if success else 'Failed to approve company'})

@bp.route('/company/reject/<int:company_id>', methods=['POST'])
def reject_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    success = company_controller.reject_company(company_id)
    return jsonify({'success': success, 'error': None if success else 'Failed to reject company'})

@bp.route('/company/eliminate/<int:company_id>', methods=['POST'])
def eliminate_company(company_id):
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    success = company_controller.eliminate_company(company_id)
    return jsonify({'success': success, 'error': None if success else 'Failed to eliminate company'})

@bp.route('/notification/<notification_id>/process', methods=['POST'])
def process_notification(notification_id):
    """Process a notification (approve/reject/eliminate) and delete it"""
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    try:
        # Get notification details
        notif = notifications_controller.get_notification_by_id(notification_id)
        if not notif:
            return jsonify({'success': False, 'error': 'Notification not found'})
        company_id = notif['company_id']
        
        # Process based on notification type
        success = False
        if notif['type'] == 'company_registration':
            success = company_controller.approve_company(company_id)
        elif notif['type'] == 'company_elimination':
            success = company_controller.eliminate_company(company_id)
            
        # If company operation was successful, delete the notification
        if success:
            notifications_controller.delete_notification(notification_id)
            return jsonify({'success': True})
            
        return jsonify({'success': False, 'error': 'Failed to process request'})
        
    except Exception as e:
        print(f"Error processing notification: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'})