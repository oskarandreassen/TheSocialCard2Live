from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'din-superhemliga-nyckel'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
