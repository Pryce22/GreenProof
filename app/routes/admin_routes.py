from flask import Blueprint, render_template, redirect, url_for, jsonify, g
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller

bp = Blueprint('admin', __name__)

@bp.route('/notifications', methods=['GET'])
def notifications():
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
    if not is_admin:
        return redirect(url_for('home'))
        
    pending_companies = company_controller.get_pending_companies()
    
    return render_template('admin_notifications.html', 
                         user_id=user_id, 
                         user=user, 
                         is_admin=is_admin, 
                         is_company_admin=is_company_admin,
                         pending_companies=pending_companies,
                         pending_companies_count=pending_companies_count)

@bp.route('/approve_company/<int:company_id>', methods=['POST'])
def approve_company(company_id):
    user_id, user, is_admin, is_company_admin = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    success = company_controller.approve_company(company_id)

    return jsonify({'success': success, 'error': None if success else 'Failed to approve company'})

@bp.route('/reject_company/<int:company_id>', methods=['POST'])
def reject_company(company_id):
    user_id, user, is_admin, is_company_admin = get_user_info()
    if not is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    if company_controller.reject_company(company_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to reject company'})
