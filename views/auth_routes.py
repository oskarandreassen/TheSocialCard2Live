# views/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms import RegisterForm, LoginForm
from flask import session


auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Kontrollera att användarnamnet inte finns
        if User.query.filter_by(username=username).first():
            flash("Användarnamnet finns redan.", "warning")
            return redirect(url_for('auth.register'))

        # Skapa användare
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Konto skapat! Logga in nedan.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            session.permanent = True
            return redirect(url_for('dashboard.dashboard_view'))

        flash("Fel användarnamn eller lösenord.", "danger")

    return render_template('login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
