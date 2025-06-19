from flask import Blueprint, render_template, redirect, url_for
from models import User, Link, db


public = Blueprint('public', __name__)

@public.route("/u/<username>")
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    user.page_views = (user.page_views or 0) + 1
    db.session.commit()

    # Om användaren har satt en “main_public_link_id” och den finns & är synlig → redirect
    if user.main_public_link_id:
        link = Link.query.get(user.main_public_link_id)
        if link and link.is_visible:
            return redirect(link.url)

    # Skicka med alla länkar (så kan templaten filtrera fram synliga)
    links = user.links

    return render_template(
        "public_profile.html",
        user=user,
        links=links
    )


@public.route('/r/<int:link_id>')
def redirect_link(link_id):
    link = Link.query.get_or_404(link_id)
    link.click_count = (link.click_count or 0) + 1
    db.session.commit()
    return redirect(link.url)


