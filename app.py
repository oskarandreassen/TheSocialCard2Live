# app.py
import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade as migrate_upgrade
from models import db, User

# ── Skapa app med instance-mapp ────────────────────────────────────────
app = Flask(
    __name__,
    instance_relative_config=True,
    template_folder='templates',
    static_folder='static'
)

# ── Grundläggande config ───────────────────────────────────────────────
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ── Se till att instance-mappen finns ─────────────────────────────────
os.makedirs(app.instance_path, exist_ok=True)

# ── Välj databas‐URI beroende på environment ─────────────────────────────
ENV = os.getenv('FLASK_ENV', 'development')
DATABASE_URL = os.getenv('DATABASE_URL')

if ENV == 'production':
    # I Render: kör alltid mot monterad disk
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL saknas i produktion!")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Lokalt: fallback till instance/users.db
    sqlite_path = os.path.join(app.instance_path, 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f'sqlite:///{sqlite_path}'

# ── Debug-print (syns i loggen) ────────────────────────────────────────
print("→ FLASK_ENV:", ENV)
print("→ Using DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])

# ── Initiera DB och migrations ─────────────────────────────────────────
db.init_app(app)
migrate = Migrate(app, db)

# ── Automatisk Alembic‐migrering i produktion ─────────────────────────
@app.before_first_request
def ensure_migrations():
    # Kör bara i produktion
    if ENV == 'production':
        migrate_upgrade()

# ── Flask-Login setup ─────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Tvinga inloggning för alla endpoints utom undantag ────────────────
@app.before_request
def require_login():
    exempt = {'auth.login', 'auth.register', 'public.public_profile', 'static'}
    if not current_user.is_authenticated and request.endpoint not in exempt:
        return redirect(url_for('auth.login'))

# ── Registrera blueprints ─────────────────────────────────────────────
from views.auth_routes      import auth
from views.dashboard_routes import dashboard
from views.themes_routes    import themes
from views.public_routes    import public

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(themes)
app.register_blueprint(public)

# ── Fallback: skapa tables om de inte finns (lokalt/test) ──────────────
with app.app_context():
    from sqlalchemy import inspect
    insp = inspect(db.engine)
    if not insp.has_table('user') or not insp.has_table('link'):
        db.create_all()

# ── Starta server ──────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=(ENV != 'production'))
