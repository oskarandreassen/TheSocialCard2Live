# billing.py

import os
import stripe
from flask import Blueprint, render_template, redirect, url_for, request, abort, jsonify
from flask_login import current_user
from sqlalchemy.sql.functions import user

from app import db
from models import User

stripe.api_key = os.environ['STRIPE_SECRET_KEY']

#ONE_TIME_PRODUCT = os.environ['STRIPE_ONE_TIME_PRODUCT']   # prod_SPGzL8IdlrO5MD
MONTHLY_PRODUCT  = os.environ.get('STRIPE_MONTHLY_PRODUCT', None)   # prod_SPGyLFMbZBQ0PE

billing = Blueprint('billing', __name__, url_prefix='/billing')

@billing.route('/setup-intent', methods=['GET'])
def setup_intent():
    if not current_user.is_authenticated:
        return redirect(url_for('public.login'))

    if not current_user.stripe_customer_id:
        cust = stripe.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = cust.id
        db.session.commit()

    # OBS: Här ska det vara current_user, inte user!
    intent = stripe.SetupIntent.create(
        customer=current_user.stripe_customer_id,
        #payment_method_types=["card"]  # lägg till "sepa_debit" om du vill erbjuda autogiro
    )

    # Skicka intent.client_secret till din template som vanligt
    return render_template(
        "billing/setup_intent.html",
        client_secret=intent.client_secret,
        STRIPE_PUBLISHABLE_KEY=os.environ.get("STRIPE_PUBLISHABLE_KEY")
    )


@billing.route('/create-subscription', methods=['POST'])
def create_subscription():
    """
    Tar emot setup_intent_id och skapar:
      1) engångs-betalning via InvoiceItem
      2) prenumeration
    """
    data = request.json
    si_id = data.get('setup_intent_id')
    customer_id = current_user.stripe_customer_id

    # 1) Lägg till engångsavgift som InvoiceItem
    stripe.InvoiceItem.create(
        customer=customer_id,
        price_data={
            'currency': 'sek',
            'unit_amount': 10000,
            'product': ONE_TIME_PRODUCT
        }
    )

    # 2) Skapa prenumerationen, använder default_payment_method från SetupIntent
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{'price_data': {
                    'currency': 'sek',
                    'unit_amount': 1900,
                    'product': MONTHLY_PRODUCT,
                    'recurring': {'interval': 'month'}
               }}],
        default_payment_method=stripe.SetupIntent.retrieve(si_id).payment_method,
        expand=['latest_invoice.payment_intent']
    )

    # 3) Spara i din DB
    current_user.is_premium = True
    current_user.stripe_subscription_id = subscription.id
    db.session.commit()

    return jsonify({'status': 'success'}), 200


@billing.route('/success')
def success():
    return render_template('billing/success.html')
