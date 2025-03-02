from supabase import create_client, Client
from flask import Flask
from app.config import Config
from app.utils.date_format import format_date
import dotenv
import os


dotenv.load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create Flask app
app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

app.jinja_env.filters['format_date'] = format_date


# Import routes after app is created to avoid circular imports
from app.routes import auth_routes, user_routes, company_routes, main_routes, admin_routes, log_user_action



# Register blueprints
app.register_blueprint(auth_routes.bp)
app.register_blueprint(user_routes.bp)
app.register_blueprint(company_routes.bp)
app.register_blueprint(main_routes.bp)
app.register_blueprint(admin_routes.bp, url_prefix='/admin') 
app.register_blueprint(log_user_action.bp)









