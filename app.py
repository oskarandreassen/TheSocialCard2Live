# app.py
import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from models import db, User

# ── Skapa app och tala om att vi vill ha en “instance”-mapp ──────────────
app = Flask(
    __name__,
    instance_relative_config=True,  # __file__/../instance blir app.instance_path
    template_folder='templates',
    static_folder='static'
)

print("🗄️  Using database:", app.config['SQLALCHEMY_DATABASE_URI'])


# ── Hemlig nyckel ───────────────────────────────────────────────────────
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'

# ── Se till att instance-mappen finns ──────────────────────────────────
os.makedirs(app.instance_path, exist_ok=True)

# ── Dynamisk databas-URI ───────────────────────────────────────────────
# Om vi har env-variabel DATABASE_URL (Render), använd den.
# Annars lokalt: absolut sökväg till instance/users.db
database_url = os.getenv('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    sqlite_path = os.path.join(app.instance_path, 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ── Initiera SQLAlchemy och migrations ─────────────────────────────────
db.init_app(app)
migrate = Migrate(app, db)

# ── Flask-Login ────────────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Tvinga inloggning för alla endpoints utom undantag ────────────────
@app.before_request
def require_login():
    exempt = {
        'auth.login', 'auth.register',    # inloggningssidor
        'public.public_profile',          # publika profilen
        'static'                          # statiska filer
    }
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


# ── Kör app ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
