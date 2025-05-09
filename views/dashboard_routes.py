from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Link

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_view():
    if request.method == 'POST':
        label = request.form['label']
        url = request.form['url']
        position = len(current_user.links)
        new_link = Link(label=label, url=url, user=current_user, position=position)
        db.session.add(new_link)
        db.session.commit()

    sorted_links = Link.query.filter_by(user_id=current_user.id).order_by(Link.position).all()
    return render_template('dashboard.html', user=current_user, sorted_links=sorted_links)

@dashboard.route('/profile')
@login_required
def profile():
    sorted_links = Link.query.filter_by(user_id=current_user.id).order_by(Link.position).all()
    return render_template('profile.html', user=current_user, sorted_links=sorted_links)

@dashboard.route('/edit_link_inline/<int:link_id>', methods=['POST'])
@login_required
def edit_link_inline(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        return "Unauthorized", 403

    data = request.get_json()
    link.label = data.get('label', link.label)
    link.url = data.get('url', link.url)
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

