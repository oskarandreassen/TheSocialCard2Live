# app.py
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from models import db, User
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
migrate = Migrate(app, db)

# ↑ Här sätter vi upp Flask-Login
login_manager = LoginManager(app)
# Vart flask-login ska skicka icke-inloggade användare:
login_manager.login_view = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── FAILSAFE: innan varje request ─────────────────────────────────────
@app.before_request
def require_login():
    # endpoints vi INTE vill tvinga inloggning för
    exempt_endpoints = (
        'auth.login', 'auth.register',      # inloggningssidor
        'public.public_profile',            # den publika profilen
        'static'                            # statiska filer
    )
    # Om användaren inte är inloggad OCH försöker nå något annat än exempt_endpoints
    if not current_user.is_authenticated and request.endpoint not in exempt_endpoints:
        return redirect(url_for('auth.login'))

# ── Registrera dina blueprints ────────────────────────────────────────
from views.auth_routes import auth
from views.dashboard_routes import dashboard
from views.themes_routes import themes
from views.public_routes import public

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(themes)
app.register_blueprint(public)

if __name__ == '__main__':
    app.run(debug=True)
