# app.py
import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from models import db, User

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'

# ─── Läs in DATABASE_URL från miljön, annars lokalen för dev ───────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///instance/users.db'      # lokal fallback
)

app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
migrate = Migrate(app, db)

# ── Flask-Login setup ──────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── FAILSAFE: tvinga inloggning ────────────────────────────────────────
@app.before_request
def require_login():
    exempt = (
        'auth.login', 'auth.register',
        'public.public_profile',
        'static'
    )
    if not current_user.is_authenticated and request.endpoint not in exempt:
        return redirect(url_for('auth.login'))

# ── Registrera blueprints ──────────────────────────────────────────────
from views.auth_routes      import auth
from views.dashboard_routes import dashboard
from views.themes_routes    import themes
from views.public_routes    import public

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(themes)
app.register_blueprint(public)

if __name__ == '__main__':
    app.run(debug=True)
