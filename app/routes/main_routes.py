from flask import Blueprint, render_template, request, jsonify
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller
import re
from app.utils.email_service import EmailService
from time import time

bp = Blueprint('main', __name__)

contact_rate_limit = {}

RATE_LIMIT_SECONDS = 300

# Route for home page
@bp.route('/')
def home():
    user_id, user, is_admin, is_company_admin, notifications = get_user_info()
    top_companies = company_controller.get_top_companies()

    return render_template('index.html', 
                         user_id=user_id, 
                         user=user, 
                         is_admin=is_admin, 
                         is_company_admin=is_company_admin,
                         notifications=notifications,
                         top_companies=top_companies)

# Route for contact form submission
@bp.route('/contact', methods=['POST'])
def contact():
    user_ip = request.remote_addr
    now = time()

    if user_ip in contact_rate_limit and now - contact_rate_limit[user_ip] < RATE_LIMIT_SECONDS:
        return jsonify({'success': False, 'error': 'Messages sent too frequently. Please wait a few seconds.'}), 429

    contact_rate_limit[user_ip] = now

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()

    errors = {}

    if not (2 <= len(name) <= 50):
        errors['name'] = "Name must be between 2 and 50 characters."
    
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_pattern, email):
        errors['email'] = "Enter a valid email address."
    
    if len(message) > 500:
        errors['message'] = "Message must not exceed 500 characters."
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    try:
        email_service = EmailService()
        if email_service.send_contact_email(name, email, message):
            return jsonify({'success': True, 'message': 'Your message has been sent successfully.'})
        else:
            return jsonify({'success': False, 'error': 'Error sending the email.'}), 500
    except Exception as e:
        print(f"Error in /contact: {e}")
        return jsonify({'success': False, 'error': 'An error occurred.'}), 500