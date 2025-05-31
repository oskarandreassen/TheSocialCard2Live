# billing.py

import os
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
import stripe
from flask_login import login_required, current_user
from app import db
from models import User
import json

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
    import sys, traceback, json
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        print("[Webhook] Signature error:", e, file=sys.stderr)
        return str(e), 400

    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print("[Webhook] RAW EVENT:", json.dumps(session, indent=2), file=sys.stderr)

            # Hämta mail från customer_email, annars customer_details.email
            customer_email_raw = (
                session.get('customer_email')
                or (session.get('customer_details', {}) or {}).get('email')
                or ''
            )
            customer_email = customer_email_raw.strip().lower() if customer_email_raw else ''

            print(f"[Webhook] checkout.session.completed! Stripe email: '{customer_email}'", file=sys.stderr)

            from models import User
            user = None

            # Koppla endast på email (client_reference_id finns inte vid Payment Links)
            if customer_email:
                user = User.query.filter(db.func.lower(User.email) == customer_email).first()

            if user:
                user.is_premium = True
                db.session.commit()
                print(f"[Webhook] User hittad & uppdaterad: id={user.id}, username={user.username}, email={user.email}", file=sys.stderr)
            else:
                print(f"[Webhook] Ingen user hittad för email '{customer_email}'", file=sys.stderr)

    except Exception as e:
        print("[Webhook] Undantag/fel i handler:", e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return f"Internal Server Error: {e}", 500

    return '', 200




