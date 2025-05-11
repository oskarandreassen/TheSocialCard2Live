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

# ── Hemlig nyckel ───────────────────────────────────────────────────────
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'

# ── Se till att instance-mappen finns (för lokal fallback) ─────────────
os.makedirs(app.instance_path, exist_ok=True)

# ── Dynamisk databas-URI ───────────────────────────────────────────────
database_url = os.getenv('DATABASE_URL')
if database_url:
    # På Render: monterad disk under /user/data
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Lokalt: vi sparar i instance/users.db
    sqlite_path = os.path.join(app.instance_path, 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'

# ── Debug: skriv ut var databasen pekas och vad som finns lokalt ───────
print("🗄️  Using database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
# Lista innehåll i två platser för felsökning:
#  - Render-disk: /user/data (om env DATABASE_URL används)
#  - Lokalt: instance/
try:
    render_disk = os.listdir('/user/data')
except FileNotFoundError:
    render_disk = None
print("📂 Contents of /user/data:", render_disk)
print("📂 Contents of instance/ :", os.listdir(app.instance_path))

# ── Resten av din konfig ───────────────────────────────────────────────
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
        'auth.login', 'auth.register',
        'public.public_profile',
        'static'
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


# ── Säkerställ schema ────────────────────────────────────────────────
with app.app_context():
    from sqlalchemy import inspect
    insp = inspect(db.engine)
    if not insp.has_table('user') or not insp.has_table('link'):
        db.create_all()
        print("✅ Skapade tabeller:", ", ".join(db.metadata.tables.keys()))
    else:
        print("🔍 Tabellerna finns redan, hoppar över create_all()")

# ── Kör app ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
