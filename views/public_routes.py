from flask import Blueprint, render_template
from models import User, Link
from flask import redirect


public = Blueprint('public', __name__)

@public.route("/u/<username>")
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.main_public_link_id:
        link = Link.query.get(user.main_public_link_id)
        if link and link.is_visible:
            return redirect(link.url)
    return render_template("public_profile.html", user=user)

