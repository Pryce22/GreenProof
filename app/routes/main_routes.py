from flask import Blueprint, render_template, request, jsonify
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller
import re
from app.utils.email_service import EmailService
from time import time

bp = Blueprint('main', __name__)
# Dizionario per il rate limiting (chiave: IP, valore: timestamp dell'ultimo messaggio)
contact_rate_limit = {}

RATE_LIMIT_SECONDS = 300  # l'utente può inviare un messaggio ogni 300 secondi

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


@bp.route('/contact', methods=['POST'])
def contact():
    user_ip = request.remote_addr
    now = time()

    # Controlla se l'IP ha già inviato un messaggio di recente
    if user_ip in contact_rate_limit and now - contact_rate_limit[user_ip] < RATE_LIMIT_SECONDS:
        return jsonify({'success': False, 'error': 'Messaggi inviati troppo frequentemente. Attendere qualche secondo.'}), 429

    # Se tutto ok, registra l'invio
    contact_rate_limit[user_ip] = now

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()

    errors = {}

    if not (2 <= len(name) <= 50):
        errors['name'] = "Il nome deve essere compreso tra 2 e 50 caratteri."
    
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_pattern, email):
        errors['email'] = "Inserisci una email valida."
    
    if len(message) > 500:
        errors['message'] = "Il messaggio non deve superare 500 caratteri."
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    try:
        email_service = EmailService()
        if email_service.send_contact_email(name, email, message):
            return jsonify({'success': True, 'message': 'Il tuo messaggio è stato inviato correttamente.'})
        else:
            return jsonify({'success': False, 'error': 'Errore durante l\'invio della mail.'}), 500
    except Exception as e:
        print(f"Errore in /contact: {e}")
        return jsonify({'success': False, 'error': 'Si è verificato un errore.'}), 500