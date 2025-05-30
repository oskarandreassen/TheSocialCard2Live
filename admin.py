from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session, send_file
from flask_login import login_required, current_user, login_user
from datetime import datetime, timedelta
from app import db
from models import User
import csv, io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dekorator som ser till att endast inloggad admin når vyerna
def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return login_required(wrapped)

# Registrera blueprint i app.py med:
#   app.register_blueprint(admin_bp)


@admin_bp.route('/', methods=['GET'])
@admin_required
def index():
    # Statistiska mått
    total_users      = User.query.count()
    recent_week      = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    confirmed_emails = User.query.filter_by(email_confirmed=True).count()
    confirmed_phones = User.query.filter_by(show_phone=True).count()
    nfc_sent_count   = User.query.filter_by(nfc_sent=True).count()

    # Sök‐ och filterparametrar
    q            = request.args.get('q', '').strip()
    filter_email = request.args.get('email_confirmed')
    filter_admin = request.args.get('is_admin')
    page         = int(request.args.get('page', 1))

    users_q = User.query
    if q:
        users_q = users_q.filter(
            (User.username.ilike(f'%{q}%')) |
            (User.email.ilike(f'%{q}%'))
        )
    if filter_email in ('yes','no'):
        users_q = users_q.filter_by(email_confirmed=(filter_email=='yes'))
    if filter_admin in ('yes','no'):
        users_q = users_q.filter_by(is_admin=(filter_admin=='yes'))

    # Sortera fallande på registreringsdatum
    # ⚠️ Här är ändringen: alla argument som keyword-only:
    paginated = users_q.order_by(User.created_at.desc()) \
                       .paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/index.html',
        total_users=total_users,
        recent_week=recent_week,
        confirmed_emails=confirmed_emails,
        confirmed_phones=confirmed_phones,
        nfc_sent_count=nfc_sent_count,
        users=paginated.items,
        pagination=paginated,
        q=q,
        filter_email=filter_email,
        filter_admin=filter_admin
    )


@admin_bp.route('/user/<int:user_id>', methods=['GET','POST'])
@admin_required
def user_detail(user_id):
    u = User.query.get_or_404(user_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'toggle_nfc':
            u.nfc_sent = not u.nfc_sent
        elif action == 'disable':
            u.is_visible = False
        elif action == 'activate':
            u.is_visible = True
        elif action == 'impersonate':
            session['admin_id'] = current_user.id
            login_user(u)
            return redirect(url_for('dashboard.dashboard_view'))
        db.session.commit()
        flash('Åtgärd utförd', 'success')
        return redirect(request.url)

    return render_template('admin/detail.html', user=u)


@admin_bp.route('/export.csv')
@admin_required
def export_csv():
    users = User.query.order_by(User.id).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['id','username','email','is_admin','email_confirmed','show_phone','nfc_sent','created_at'])
    for u in users:
        cw.writerow([
            u.id, u.username, u.email,
            u.is_admin, u.email_confirmed,
            u.show_phone, u.nfc_sent,
            u.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output,
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='users_export.csv')


@admin_bp.route('/impersonate/stop')
@login_required
def stop_impersonate():
    admin_id = session.pop('admin_id', None)
    if admin_id:
        admin = User.query.get(admin_id)
        login_user(admin)
        flash('Återgick till admin-konto', 'info')
    return redirect(url_for('admin.index'))
