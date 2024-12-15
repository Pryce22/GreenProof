from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurazione SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Database in app.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
