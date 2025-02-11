from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.controllers import user_controller
from app.routes.auth_routes import get_user_info

bp = Blueprint('user', __name__)

@bp.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin, pending_companies_count=pending_companies_count)
    
    return render_template('user_profile.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies, pending_companies_count=pending_companies_count)


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


@bp.route('/manage_employee', methods=['GET', 'POST'])
def manage_employee():
    user_id, user, is_admin, is_company_admin, pending_companies_count = get_user_info()
    companies= user_controller.get_companies_by_user_id(user_id)

    if not user_id:
        return redirect(url_for('login'))
    if is_company_admin:
        unique_company_admin=user_controller.is_unique_company_admin(user_id)
        unique_admin=user_controller.get_company_ids_where_user_is_unique_admin(user_id)
        
        return render_template('manage_employee.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, unique_company_admin=unique_company_admin, companies=companies, unique_admin=unique_admin, pending_companies_count=pending_companies_count)
    
    return render_template('manage_employee.html', user_id=user_id, user=user, is_admin=is_admin, is_company_admin=is_company_admin, companies=companies, pending_companies_count=pending_companies_count)

