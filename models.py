from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    display_name = db.Column(db.String(150), nullable=True)  # ← NYTT
    password = db.Column(db.String(150))
    profile_image = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.String(300), nullable=True)
    font_family = db.Column(db.String(100), default='Inter')
    theme_color = db.Column(db.String(20), default='blue')
    template = db.Column(db.String(50), default='default')
    links = db.relationship('Link', backref='user')
    show_links = db.Column(db.Boolean, default=True)
    is_visible = db.Column(db.Boolean, default=True)
    email         = db.Column(db.String(120), nullable=True)
    show_email    = db.Column(db.Boolean, default=False)
    phone_number  = db.Column(db.String(20),  nullable=True)
    show_phone    = db.Column(db.Boolean, default=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_token     = db.Column(db.String(36), nullable=True)
    email_sent_at   = db.Column(db.DateTime, nullable=True)

    def generate_email_token(self):
        self.email_token = str(uuid.uuid4())
        self.email_sent_at = datetime.utcnow()
        return self.email_token


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    url = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    position = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)  # 🆕 Lägg till detta!

