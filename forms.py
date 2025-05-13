# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo               # ← Lagt till EqualTo här
from utils.validators import password_strength

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
