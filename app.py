# app.py
import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade as migrate_upgrade
from models import db, User

app = Flask(
    __name__,
    instance_relative_config=True,
    template_folder='templates',
    static_folder='static'
)

app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.instance_path, exist_ok=True)

ENV = os.getenv('FLASK_ENV', 'development')
DATABASE_URL = os.getenv('DATABASE_URL')

if ENV == 'production':
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL saknas i produktion!")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    sqlite_path = os.path.join(app.instance_path, 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f'sqlite:///{sqlite_path}'

print("→ FLASK_ENV:", ENV)
print("→ Using DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)
migrate = Migrate(app, db)

# ── AUTOMATISK MIGRERING VID START ────────────────────────────────────
if ENV == 'production':
    with app.app_context():
        migrate_upgrade()

login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def require_login():
    exempt = {'auth.login', 'auth.register', 'public.public_profile', 'static'}
    if not current_user.is_authenticated and request.endpoint not in exempt:
        return redirect(url_for('auth.login'))

from views.auth_routes      import auth
from views.dashboard_routes import dashboard
from views.themes_routes    import themes
from views.public_routes    import public

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(themes)
app.register_blueprint(public)

with app.app_context():
    from sqlalchemy import inspect
    insp = inspect(db.engine)
    if not insp.has_table('user') or not insp.has_table('link'):
        db.create_all()

if __name__ == '__main__':
    app.run(debug=(ENV != 'production'))
