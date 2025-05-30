# billing.py

import os
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
import stripe
from flask_login import login_required, current_user
from app import db
from models import User

stripe.api_key = os.environ['STRIPE_SECRET_KEY']

# Ta bort gamla, inaktuella rader om du vill – bara behåll price_id i koden nedan
# ONE_TIME_PRODUCT = os.environ['STRIPE_ONE_TIME_PRODUCT']   # prod_SPGzL8IdlrO5MD
# MONTHLY_PRODUCT  = os.environ.get('STRIPE_MONTHLY_PRODUCT', None)   # prod_SPGyLFMbZBQ0PE

billing = Blueprint('billing', __name__, url_prefix='/billing')



@billing.route('/success')
@login_required
def success():
    return render_template('billing/success.html')

import stripe
from flask import Blueprint, request

billing = Blueprint('billing', __name__, url_prefix='/billing')

@billing.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return str(e), 400

    # Hantera olika event-typer:
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Hämta kunden/emailet från sessionen
        customer_email = session.get('customer_email')
        # --- Här: markera användare som premium i din DB ---
        from models import User
        user = User.query.filter_by(email=customer_email).first()
        if user:
            user.is_premium = True
            db.session.commit()
        # (lägg till annan logik om du har stripe_customer_id etc)
    # Lägg till fler event om du vill

    return '', 200