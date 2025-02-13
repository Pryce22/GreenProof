from flask import Blueprint, render_template
from app.routes.auth_routes import get_user_info
from app.controllers import company_controller

bp = Blueprint('main', __name__)

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
