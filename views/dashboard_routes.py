from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from models import db, Link
from forms import ProfileForm
from flask import flash


dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_view():
    # Initiera kontaktformuläret med befintliga värden
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Spara e-post och telefon på användaren
        current_user.email        = form.email.data
        current_user.show_email   = form.show_email.data
        current_user.phone_number = form.phone_number.data
        current_user.show_phone   = form.show_phone.data
        db.session.commit()
        flash("Din kontaktinfo är uppdaterad!", "success")
        return redirect(url_for('dashboard.dashboard_view'))

    # Hantera tillägg av länk
    if request.method == 'POST' and 'label' in request.form:
        label = request.form['label']
        url = request.form['url']
        position = len(current_user.links)
        new_link = Link(label=label, url=url, user=current_user, position=position)
        db.session.add(new_link)
        db.session.commit()

    # Hämta ordnade länkar för visning
    sorted_links = Link.query.filter_by(user_id=current_user.id) \
                             .order_by(Link.position).all()

    return render_template(
        'dashboard.html',
        user=current_user,
        sorted_links=sorted_links,
        form=form
    )


@dashboard.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Spara formulärdata på current_user
        current_user.email        = form.email.data
        current_user.show_email   = form.show_email.data
        current_user.phone_number = form.phone_number.data
        current_user.show_phone   = form.show_phone.data
        db.session.commit()
        flash("Din kontaktinfo är uppdaterad!", "success")
        return redirect(url_for('dashboard.profile'))

    # Hämta länkar också om du vill visa i profilen
    sorted_links = Link.query.filter_by(user_id=current_user.id)\
                             .order_by(Link.position).all()

    return render_template('profile.html',
                           user=current_user,
                           sorted_links=sorted_links,
                           form=form)

@dashboard.route('/edit_link_inline/<int:link_id>', methods=['POST'])
@login_required
def edit_link_inline(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        return "Unauthorized", 403

    data = request.get_json()
    link.label = data.get('label', link.label)
    link.url   = data.get('url', link.url)
    db.session.commit()
    return '', 204

@dashboard.route('/update_order', methods=['POST'])
@login_required
def update_order():
    data = request.get_json()
    for index, link_id in enumerate(data.get('order', [])):
        link = Link.query.get(int(link_id))
        if link and link.user_id == current_user.id:
            link.position = index
    db.session.commit()
    return '', 204

@dashboard.route('/delete_link/<int:link_id>')
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(link)
    db.session.commit()
    return redirect(url_for('dashboard.dashboard_view'))

@dashboard.route('/toggle_visibility/<int:link_id>', methods=['POST'])
@login_required
def toggle_link_visibility(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        return "Unauthorized", 403
    link.is_visible = not link.is_visible
    db.session.commit()
    return redirect(url_for('dashboard.dashboard_view'))

@dashboard.route('/update_contact', methods=['POST'])
@login_required
def update_contact():
    data = request.get_json() or {}
    # Observera: vi lyssnar på fältnamn 'email' och 'phone_number'
    if 'email' in data:
        current_user.email      = data['email']
        current_user.show_email = data.get('show_email', True)
    if 'phone_number' in data:
        current_user.phone_number = data['phone_number']
        current_user.show_phone   = data.get('show_phone', True)
    db.session.commit()
    return jsonify(success=True)


@dashboard.route('/set_main_public_link/<int:link_id>', methods=['POST'])
@login_required
def set_main_public_link(link_id):
    if not current_user.is_premium:
        return "Premium krävs", 403

    link = Link.query.get_or_404(link_id)
    user = current_user
    if user.main_public_link_id == link.id:
        user.main_public_link_id = None
    else:
        user.main_public_link_id = link.id
    db.session.commit()
    return ('', 204)


