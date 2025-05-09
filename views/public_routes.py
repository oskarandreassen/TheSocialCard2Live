from flask import Blueprint, render_template
from models import User, Link

public = Blueprint('public', __name__)

@public.route('/u/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    links = Link.query.filter_by(user_id=user.id).order_by(Link.position).all()
    return render_template('public_profile.html', user=user, links=links)
