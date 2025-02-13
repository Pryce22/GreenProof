from flask import Blueprint, render_template, redirect, url_for, jsonify, g, request
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller, user_controller
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
    
@bp.route('/admin_manage_company', methods=['GET'])
def admin_manage_company():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    search_query = request.args.get('query', '').strip()

    try:
        companies = []
        if search_query != "":
            companies = company_controller.search_companies(search_query)
        else:
            companies = company_controller.get_all_companies_sorted()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'companies': companies})
        
        return render_template('manage_companies.html', 
                             companies=companies, 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin, 
                             is_company_admin=is_company_admin,
                             notifications=notifications,
                             search_query=search_query)
    except Exception as e:
        print(f"Errore durante la ricerca delle compagnie: {e}")
        return render_template('manage_companies.html', 
                             companies=[], 
                             user_id=user_id, 
                             user=user, 
                             is_admin=is_admin,
                             notifications=notifications,
                             search_query=search_query, 
                             is_company_admin=is_company_admin)
    


@bp.route('/admin_manage_user', methods=['GET', 'POST'])
def admin_manage_user():
    # Ottieni informazioni sull'utente
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    unique_admin=user_controller.get_unique_company_admins()

    # Verifica se l'utente è autenticato
    if not user_id:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')

    # Se è presente una query di ricerca, filtra gli utenti
    if search_query:
        # Passa il search_query alla funzione get_all_users per filtrare i risultati
        users_info = user_controller.get_users_by_name_or_surname(search_query)
    else:
        # Se non c'è ricerca, restituisci tutti gli utenti
        users_info = user_controller.get_all_users()

    # Se non è amministratore di una compagnia, solo le informazioni di base
    return render_template('manage_user.html', 
                           user_id=user_id, 
                           user=user, 
                           is_admin=is_admin, 
                           is_company_admin=is_company_admin,
                           users_info=users_info,
                           search_query=search_query,
                           unique_admins=unique_admin,
                           notifications=notifications)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        # Esegui l'eliminazione dell'utente dal database (assumendo che tu stia usando un database con supabase)
        response = user_controller.delete_user(user_id)
        if response:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete user'}), 500

    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500
