# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo               # ← Lagt till EqualTo här
from utils.validators import password_strength


from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import Optional, Email, Regexp


class RegisterForm(FlaskForm):
    username = StringField(
        'Användarnamn',
        validators=[DataRequired(message="Användarnamn saknas")]
    )
    password = PasswordField(
        'Lösenord',
        validators=[
            DataRequired(message="Lösenord saknas"),
            password_strength
        ]
    )
    confirm = PasswordField(
        'Bekräfta lösenord',
        validators=[
            DataRequired(message="Bekräfta lösenord saknas"),
            EqualTo('password', message='Lösenorden måste matcha.')
        ]
    )
    submit = SubmitField('Skapa konto')

class LoginForm(FlaskForm):
    username = StringField(
        'Användarnamn',
        validators=[DataRequired(message="Användarnamn saknas")]
    )
    password = PasswordField(
        'Lösenord',
        validators=[DataRequired(message="Lösenord saknas")]
    )
    submit = SubmitField('Logga in')


class ProfileForm(FlaskForm):
    email = StringField(
        "E-post",
        validators=[Optional(), Email(message="Ogiltig e-postadress")]
    )
    show_email = BooleanField("Visa e-post offentligt")
    phone_number = StringField(
        "Telefonnummer",
        validators=[Optional(), Regexp(r'^\+?[0-9 ]*$', message="Endast siffror och mellanslag")]
    )
    show_phone = BooleanField("Visa telefonnummer offentligt")
    submit = SubmitField("Spara kontaktinfo")
