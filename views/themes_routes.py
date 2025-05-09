from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from werkzeug.utils import secure_filename
import os

themes = Blueprint('themes', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@themes.route('/themes', methods=['GET', 'POST'])
@login_required
def themes_view():
    if request.method == 'POST':
        file = request.files.get('profile_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = 'static/uploads'
            filepath = os.path.join(upload_folder, filename)
            os.makedirs(upload_folder, exist_ok=True)
            file.save(filepath)
            current_user.profile_image = f'uploads/{filename}'

        current_user.font_family = request.form.get('font_family')
        current_user.theme_color = request.form.get('theme_color')
        current_user.bio = request.form.get('bio')
        current_user.template = request.form.get('template')
        db.session.commit()
        flash("Profil uppdaterad!")
        return redirect(url_for('dashboard.dashboard_view'))

    return render_template('profile_settings.html', user=current_user)
