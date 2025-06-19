# views/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from app import mail, db, limiter        # ← Importera limiter här
from models import User
from forms import RegisterForm, LoginForm, SetupEmailForm
from flask_mail import Message


auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # max 5 försök per IP och timme
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # 1) Kolla både username och email
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email= User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Användarnamnet finns redan.", "warning")
            return redirect(url_for('auth.register'))
        if existing_email:
            flash("Den här e-postadressen är redan registrerad.", "warning")
            return redirect(url_for('auth.register'))

        # 2) Skapa användare + generera token, skicka mail …
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        # … om du vill göra email-confirmation:
        token = new_user.generate_email_token()
        new_user.email_token = token
        db.session.add(new_user)
        db.session.commit()

        # Skicka bekräftelsemail
        link = url_for('auth.confirm_email', token=token, _external=True)
        msg = Message("Bekräfta din e-post", recipients=[new_user.email])
        msg.body = f"Välkommen! Klicka här för att aktivera ditt konto:\n\n{link}"
        mail.send(msg)

        flash("En aktiveringslänk har skickats till din e-post.", "info")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth.route('/resend-confirm', methods=['POST'])
def resend_confirm():
    email = request.form.get('email')  # eller från ett dolt fält i inloggningsformuläret
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Vi hittar inget konto med den e-postadressen.", "warning")
        return redirect(url_for('auth.login'))

    if user.email_confirmed:
        flash("Din e-post är redan bekräftad. Logga in istället.", "info")
        return redirect(url_for('auth.login'))

    # Skapa ny token och skicka
    token = user.generate_email_token()
    db.session.commit()
    link = url_for('auth.confirm_email', token=token, _external=True)
    msg = Message("Bekräfta din e-post", recipients=[user.email])
    msg.body = f"Klicka här för att aktivera ditt konto:\n\n{link}"
    mail.send(msg)

    flash("Ny bekräftelselänk skickad till din e-post.", "success")
    return redirect(url_for('auth.login'))

@auth.route('/setup-email', methods=['GET', 'POST'])
def setup_email():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if current_user.email_confirmed:
        return redirect(url_for('dashboard.dashboard_view'))

    form = SetupEmailForm()
    if form.validate_on_submit():
        # Spara både e-post och token i samma commit
        current_user.email = form.email.data
        token = current_user.generate_email_token()
        db.session.commit()

        # Skicka bekräftelse-mail
        link = url_for('auth.confirm_email', token=token, _external=True)
        msg = Message("Bekräfta din e-post", recipients=[current_user.email])
        msg.body = f"Klicka här för att bekräfta ditt konto:\n\n{link}"
        mail.send(msg)

        flash("E-post sparad – kolla din inkorg för bekräftelselänk.", "success")
        return redirect(url_for('auth.login'))

    return render_template('setup_email.html', form=form)




@auth.route('/confirm/<token>')
def confirm_email(token):
    user = User.query.filter_by(email_token=token).first_or_404()
    user.email_confirmed = True
    user.email_token = None
    db.session.commit()
    flash("Din e-post är nu bekräftad! Du kan nu logga in.", "success")
    return redirect(url_for('auth.login'))



@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            or_(
                User.username == form.username.data,
                User.email    == form.username.data
            )
        ).first()

        if user and check_password_hash(user.password, form.password.data):
            # Logga in utan “remember” → session varar bara PERMANENT_SESSION_LIFETIME
            login_user(user)         # Ta bort “remember=True”
            session.permanent = True

            # Eventuellt: spara is_admin-flaggan
            if user.email == 'oskarandreassen01@gmail.com':
                user.is_admin = True
                db.session.commit()

            if not user.email:
                return redirect(url_for('auth.setup_email'))
            if not user.email_confirmed:
                return redirect(url_for('auth.setup_email'))

            return redirect(url_for('dashboard.dashboard_view'))

        flash("Fel användarnamn eller lösenord.", "danger")

    return render_template('login.html', form=form)





@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
