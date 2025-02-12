from flask import Blueprint, render_template
from app.routes.auth_routes import get_user_info

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    user_id, user, is_admin, is_company_admin, notifications, pending_companies_count = get_user_info()
    return render_template('index.html', 
                         user_id=user_id, 
                         user=user, 
                         is_admin=is_admin, 
                         is_company_admin=is_company_admin,
                         notifications=notifications)
