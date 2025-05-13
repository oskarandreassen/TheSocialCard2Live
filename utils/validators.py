import re
from wtforms import ValidationError

def password_strength(form, field):
    pwd = field.data or ""
    errors = []
    if len(pwd) < 5:
        errors.append("minst 5 tecken")
    if not re.search(r"[A-ZÅÄÖ]", pwd):
        errors.append("en versal (A–Z)")
    if not re.search(r"[a-zåäö]", pwd):
        errors.append("en gemen (a–z)")
    if not re.search(r"\d", pwd):
        errors.append("en siffra (0–9)")
    # Om du vill ha specialtecken:
    # if not re.search(r"[!@#\$%\^&\*]", pwd):
    #     errors.append("ett specialtecken (!@#$%^&*)")
    if errors:
        raise ValidationError("Lösenordet måste innehålla " + ", ".join(errors) + ".")
