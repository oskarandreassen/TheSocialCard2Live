# app.py
import os
import logging
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade as migrate_upgrade
from sqlalchemy import create_engine, inspect as sa_inspect
from models import db, User

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# ── Val av databas-URI med fallback och debug-loggning ─────────────────
DATABASE_URL = os.getenv('DATABASE_URL')
logger.debug(f"Environment DATABASE_URL: {DATABASE_URL}")

candidates = []
if DATABASE_URL:
    candidates.append(DATABASE_URL)
candidates.append('sqlite:////user/data/users.db')
sqlite_local = os.path.join(app.instance_path, 'users.db')
candidates.append(f'sqlite:///{sqlite_local}')
candidates.append('sqlite:///backup/users_backup.db')
logger.debug(f"DB candidates: {candidates}")

chosen_uri = None
for uri in candidates:
    try:
        engine = create_engine(uri)
        insp = sa_inspect(engine)
        logger.debug(f"Inspecting URI {uri}: tables={insp.get_table_names()}")
        if insp.has_table('user') or uri.startswith('sqlite:///'):
            chosen_uri = uri
            logger.info(f"Chosen DB URI: {chosen_uri}")
            break
    except Exception as e:
        logger.warning(f"Failed to connect/test URI {uri}: {e}")

if not chosen_uri:
    logger.error('Ingen giltig databas-URI kunde hittas')
    raise RuntimeError('Ingen giltig databas-URI kunde hittas')

app.config['SQLALCHEMY_DATABASE_URI'] = chosen_uri
logger.debug(f"→ Using DB URI: {chosen_uri}")

# ── Initiera DB och migrations ─────────────────────────────────────────
db.init_app(app)
migrate = Migrate(app, db)

# ── Automatisk migrering vid start med felhantering ────────────────────
if chosen_uri != f'sqlite:///{sqlite_local}':  # migrera för extern eller render
    try:
        with app.app_context():
            logger.info("Running migrations...")
            migrate_upgrade()
            logger.info("Migrations applied successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # pdb.set_trace()  # Uncomment for interactive debugging

# ── Flask-Login setup ─────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user with ID: {user_id}")
    return User.query.get(int(user_id))

# ── Tvinga inloggning för alla endpoints utom undantag ────────────────
@app.before_request
def require_login():
    exempt = {'auth.login', 'auth.register', 'public.public_profile', 'static'}
    if not current_user.is_authenticated and request.endpoint not in exempt:
        logger.debug(f"Unauthorized access attempt to {request.endpoint}")
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
    insp_main = sa_inspect(db.engine)
    existing = insp_main.get_table_names()
    logger.debug(f"Existing tables before fallback: {existing}")
    if 'user' not in existing or 'link' not in existing:
        logger.info("Creating missing tables via db.create_all()")
        db.create_all()

# ── Starta server ──────────────────────────────────────────────────────
if __name__ == '__main__':
    debug_mode = chosen_uri.startswith('sqlite:///') and not DATABASE_URL
    app.run(debug=debug_mode)