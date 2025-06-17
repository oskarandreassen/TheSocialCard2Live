# app.py
import os
import logging

import stripe
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade as migrate_upgrade
from sqlalchemy import inspect as sa_inspect
from models import db, User
from datetime import timedelta, datetime
from flask_mail import Mail, Message

from flask import Flask
from flask_mail import Mail



from billing import billing



from dotenv import load_dotenv
load_dotenv()      # läser in .env i miljön

from flask import Blueprint, send_from_directory, current_app



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

mail = Mail(app)

# app.py (viktigast: längst ner eller där du registrerar andra blueprints)
from billing import billing
app.register_blueprint(billing)  # prefix är redan satt i billing.py som '/billing'


# … efter app = Flask(…)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

app.config.update(
  MAIL_SERVER        = 'smtp.strato.com',
  MAIL_PORT          = 587,
  MAIL_USE_TLS       = True,
  MAIL_USERNAME      = os.getenv('STRATO_SMTP_USER'),
  MAIL_PASSWORD      = os.getenv('STRATO_SMTP_PASS'),
  MAIL_DEFAULT_SENDER= ('SocialCard', 'noreply@socialcard.se'),
)
mail = Mail(app)

exempt = {'auth.login', 'auth.register', 'auth.confirm_email',
          'auth.resend_confirm', 'auth.setup_email', 'public.public_profile', 'static',
          'uploaded_file'
          }

from admin import admin_bp
app.register_blueprint(admin_bp)


# ── Configuration ─────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'din-superhemliga-nyckel')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ⮕ Lägg till just denna rad, så att konfigen från .env hamnar i app.config:
app.config['STRIPE_SECRET_KEY']    = os.getenv('STRIPE_SECRET_KEY')
app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY')
app.config['STRIPE_PRICE_ID']       = os.getenv('STRIPE_PRICE_ID')

import os

if os.environ.get("RENDER") == "1":
    UPLOAD_FOLDER = '/user/data/uploads'
else:
    UPLOAD_FOLDER = os.path.join('static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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



# ── Flask-Login setup ─────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Du måste logga in för att se den här sidan."


from flask import send_from_directory

from flask_apscheduler import APScheduler
from tasks import purge_unconfirmed

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)
# Kör första gången direkt, därefter var 10:e dag
scheduler.add_job(
    id='purge_unconfirmed',
    func=purge_unconfirmed,
    trigger='interval',
    days=10,
    next_run_time=datetime.utcnow()
)
scheduler.start()


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user id {user_id}")
    return User.query.get(int(user_id))

@app.before_request
def require_login():
    # 1. Tillåt Stripe webhook POST
    if request.path == '/billing/webhook':
        return

    # 2. Övriga undantag – endpoints som ska vara publika
    exempt = {
        'auth.login', 'auth.register', 'auth.confirm_email',
        'auth.setup_email', 'public.public_profile', 'static',
        'uploaded_file'
    }
    if not current_user.is_authenticated and request.endpoint not in exempt:
        # Logga gärna för felsökning:
        # print(f"Blocked access to {request.endpoint} from {request.path}")
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
            #db.create_all()



from flask import request, abort

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload    = request.data
    sig_header = request.headers.get('Stripe-Signature')
    secret     = os.environ['STRIPE_WEBHOOK_SECRET']
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except stripe.error.SignatureVerificationError:
        abort(400)

    if event['type'] == 'checkout.session.completed':
        sess = event['data']['object']
        user = User.query.filter_by(stripe_customer_id=sess['customer']).first()
        if user:
            user.is_premium             = True
            user.stripe_subscription_id = sess.get('subscription')
            db.session.commit()
    return '', 200


# ── Run server ────────────────────────────────────────────────────────
if __name__ == '__main__':
    debug_mode = not run_migrations
    app.run(debug=debug_mode)