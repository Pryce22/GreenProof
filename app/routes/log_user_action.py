from flask import Blueprint,request, g, session
from datetime import datetime, timezone
from app.controllers.log_action_controller import log_user_action

bp = Blueprint('log_user', __name__)

# Middleware to log user actions
@bp.before_app_request
def log_request():
    g.start_time = datetime.now(timezone.utc)

# Middleware to log user actions
@bp.after_app_request
def log_response(response):
    if hasattr(g, 'start_time'):
        # Get user info from session if available
        user_id = session.get('id', 'anonymous')
        
        # Create log entry
        current_time = datetime.now(timezone.utc)
        log_data = {
            'user_id': user_id,
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'timestamp': current_time.isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'response_time': (current_time - g.start_time).total_seconds()
        }

        log_user_action(log_data)

    return response