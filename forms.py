# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo,
    Regexp, ValidationError, Optional
)
from models import User
from disposable_email_domains import blocklist as disposable_domains


class RegisterForm(FlaskForm):
    username = StringField(
        'Användarnamn',
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    email = StringField(
        'E-post',
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        'Lösenord',
        validators=[
            DataRequired(),
            Length(min=5),
            EqualTo('password2', message='Lösenorden måste matcha.')
        ]
    )
    password2 = PasswordField(
        'Bekräfta lösenord',
        validators=[DataRequired()]
    )
    submit = SubmitField('Registrera')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Användarnamnet är redan taget.')

    def validate_email(self, field):
        domain = field.data.split('@')[-1].lower()
        if domain in disposable_domains:
            raise ValidationError(
                'Engångs-mejladresser accepteras inte, vänligen använd en riktig adress.'
            )
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Den här e-postadressen är redan registrerad.')


class LoginForm(FlaskForm):
    username = StringField(
        'Användarnamn',
        validators=[DataRequired(message='Användarnamn saknas')]
    )
    password = PasswordField(
        'Lösenord',
        validators=[DataRequired(message='Lösenord saknas')]
    )
    submit = SubmitField('Logga in')


class ProfileForm(FlaskForm):
    email = StringField(
        'E-post',
        validators=[Optional(), Email(message='Ogiltig e-postadress')]
    )
    show_email = BooleanField('Visa e-post offentligt')
    phone_number = StringField(
        'Telefonnummer',
        validators=[Optional(), Regexp(r'^\+?[0-9 ]*$', message='Endast siffror och mellanslag')]
    )
    show_phone = BooleanField('Visa telefonnummer offentligt')
    submit = SubmitField('Spara kontaktinfo')


class SetupEmailForm(FlaskForm):
    email = StringField(
        'E-post',
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    show_email = BooleanField('Visa e-post offentligt')
    submit = SubmitField('Spara')
