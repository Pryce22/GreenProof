from supabase import create_client, Client
from flask import Flask
from app.config import Config
from app.utils.date_format import format_date

SUPABASE_URL = "https://cjoykzgrtvlghogxzdjq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqb3lremdydHZsZ2hvZ3h6ZGpxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDMwMDY4NiwiZXhwIjoyMDQ5ODc2Njg2fQ.JkShNd00ZSc7QmsthH49aS8fQPqmHuM-Xj3WuSgEsPc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

app.jinja_env.filters['format_date'] = format_date

# Import routes after app is created to avoid circular imports
from app.routes import auth_routes, user_routes, company_routes, main_routes, admin_routes

# Register blueprints
app.register_blueprint(auth_routes.bp)
app.register_blueprint(user_routes.bp)
app.register_blueprint(company_routes.bp)
app.register_blueprint(main_routes.bp)
app.register_blueprint(admin_routes.bp, url_prefix='/admin') 








