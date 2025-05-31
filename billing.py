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
    import sys, traceback
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
            client_reference_id = session.get('client_reference_id')
            customer_email = session.get('customer_email', '').strip().lower()
            print(f"[Webhook] checkout.session.completed! Stripe email: '{customer_email}', client_reference_id: '{client_reference_id}'", file=sys.stderr)

            from models import User
            user = None

            if client_reference_id:
                user = User.query.filter_by(username=client_reference_id).first()
                # eller om du kör id:
                # try:
                #     user = User.query.get(int(client_reference_id))
                # except Exception:
                #     user = None

            if not user and customer_email:
                user = User.query.filter(db.func.lower(User.email) == customer_email).first()

            if user:
                user.is_premium = True
                db.session.commit()
                print(f"[Webhook] User hittad & uppdaterad: id={user.id}, username={user.username}, email={user.email}", file=sys.stderr)
            else:
                print(f"[Webhook] Ingen user hittad för client_reference_id '{client_reference_id}' eller email '{customer_email}'", file=sys.stderr)
    except Exception as e:
        print("[Webhook] Undantag/fel i handler:", e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return f"Internal Server Error: {e}", 500

    return '', 200


