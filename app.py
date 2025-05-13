# app.py
import os
import logging
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade as migrate_upgrade
from sqlalchemy import inspect as sa_inspect
from models import db, User
from datetime import timedelta

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ── Flask app initialization ──────────────────────────────────────────
app = Flask(
    __name__,
    instance_relative_config=True,
    template_folder='templates',
    static_folder='static'
)


# … efter app = Flask(…)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=5)



# ── Configuration ─────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'din-superhemliga-nyckel')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ── Ensure instance folder exists ─────────────────────────────────────
os.makedirs(app.instance_path, exist_ok=True)

# ── Determine database URI ─────────────────────────────────────────────
# If DATABASE_URL env var is set, use it (production/Render), else local SQLite
database_url = os.getenv('DATABASE_URL')
if database_url:
    db_uri = database_url
    run_migrations = True
else:
    sqlite_path = os.path.join(app.instance_path, 'users.db')
    db_uri = f'sqlite:///{sqlite_path}'
    run_migrations = False

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
logger.info(f"Using DB URI: {db_uri}")

# ── Initialize DB and migrations ───────────────────────────────────────
db.init_app(app)
migrate = Migrate(app, db)

# ── Apply Alembic migrations if running against external DB ────────────
if run_migrations:
    try:
        with app.app_context():
            logger.info("Applying pending migrations...")
            migrate_upgrade()
            logger.info("Migrations applied successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # For debugging, uncomment:
        # import pdb; pdb.set_trace()

# ── Flask-Login setup ─────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user id {user_id}")
    return User.query.get(int(user_id))

# ── Require login for protected routes ─────────────────────────────────
@app.before_request
def require_login():
    exempt = {'auth.login', 'auth.register', 'public.public_profile', 'static'}
    if not current_user.is_authenticated and request.endpoint not in exempt:
        logger.debug(f"Blocked access to {request.endpoint}")
        return redirect(url_for('auth.login'))

# ── Register blueprints ───────────────────────────────────────────────
from views.auth_routes      import auth
from views.dashboard_routes import dashboard
from views.themes_routes    import themes
from views.public_routes    import public
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(themes)
app.register_blueprint(public)

# ── Create missing tables locally if not using migrations ─────────────
if not run_migrations:
    with app.app_context():
        insp = sa_inspect(db.engine)
        existing = insp.get_table_names()
        logger.debug(f"Existing tables locally: {existing}")
        if 'user' not in existing or 'link' not in existing:
            logger.info("Creating tables via db.create_all() (local)")
            db.create_all()

# ── Run server ────────────────────────────────────────────────────────
if __name__ == '__main__':
    debug_mode = not run_migrations
    app.run(debug=debug_mode)