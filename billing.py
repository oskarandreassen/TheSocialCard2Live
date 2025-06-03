import os
import stripe
from flask import Blueprint, render_template, request, jsonify, abort, url_for, current_app
from flask_login import login_required, current_user
from models import db, User, Link
from flask_mail import Message

billing = Blueprint('billing', __name__)

# ── Hämta Stripe­-nycklar från miljövariabler ──────────────────────────────
stripe.api_key             = os.getenv('STRIPE_SECRET_KEY')          # Ex: sk_live_... eller sk_test_...
STRIPE_PUBLISHABLE_KEY     = os.getenv('STRIPE_PUBLISHABLE_KEY')      # Ex: pk_live_... eller pk_test_...
PRICE_ID                   = os.getenv('STRIPE_PRICE_ID')            # Ex: price_*****
MONTHLY_PRODUCT_ID         = os.getenv('STRIPE_MONTHLY_PRODUCT')      # (om du vill hämta produkt­-ID separat)

#
# ── 1) Valfri “checkout”-vy (endast för debugging / alternativ knapp­-vy) ────
#
@billing.route('/checkout')
@login_required
def checkout_page():
    """
    (Valfritt) Visa en enkel sida med “Skaffa Premium”-knapp.
    Om du redan har knappen i t.ex. dashboard.html, behövs inte denna.
    """
    return render_template('billing/checkout.html',
                           stripe_public_key=STRIPE_PUBLISHABLE_KEY)


#
# ── 2) Skapa Stripe Checkout Session ─────────────────────────────────────
#
@billing.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Anropas via JS när användaren trycker “Skaffa Premium”.
    Skapar en Stripe Checkout Session och returnerar sessionId till JS.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    # Säkerställ att JS verkligen skickade rätt user_id
    if not user_id or int(user_id) != current_user.id:
        abort(403)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': PRICE_ID,
                'quantity': 1,
            }],
            # Förifyll e-post så Stripe slipper fråga
            customer_email=current_user.email or None,

            # ── Tillåt rabattkod (promotion code) ──
            allow_promotion_codes=True,

            # ── Be om leveransadress (sparas i Stripe, ej lokalt) ──
            shipping_address_collection={
                'allowed_countries': ['SE', 'NO', 'DK', 'FI', 'US']
            },

            # Lägg in vår egen metadata så webhook kan koppla ihop betalning ↔ user
            metadata={
                'user_id': str(current_user.id),
                'username': current_user.username
            },

            # Redirect efter lyckad betalning
            success_url=url_for('billing.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            # Om användaren klickar “avbryt”
            cancel_url=url_for('billing.checkout_cancel', _external=True),
        )
        return jsonify({'sessionId': checkout_session.id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#
# ── 3) Sidor som visas efter Checkout ─────────────────────────────────────
#
@billing.route('/success')
@login_required
def checkout_success():
    """
    Visas efter lyckad betalning. (Stripe skickar med ?session_id=… i URL.)
    Du kan plocka ut session_id och visa detaljer om du vill.
    """
    session_id = request.args.get('session_id')
    return render_template('billing/success.html', session_id=session_id)


@billing.route('/cancel')
@login_required
def checkout_cancel():
    """
    Visas om användaren avbryter Checkout-processen.
    """
    return render_template('billing/cancel.html')


#
# ── 4) Stripe Webhook: checkout.session.completed ────────────────────────
#
@billing.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        print("⚠️  Webhook signature verification failed.", e)
        return jsonify({'error': str(e)}), 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        # Läs ut vår metadata:
        user_id_str = session_obj.get('metadata', {}).get('user_id')

        if user_id_str:
            try:
                user = User.query.get(int(user_id_str))
            except:
                user = None

            if user:
                # Markera användaren som Premium i databasen
                user.is_premium = True
                user.stripe_customer_id     = session_obj.get('customer')
                user.stripe_subscription_id = session_obj.get('subscription')
                db.session.commit()
                print(f"[Webhook] Användare {user.id} uppdaterad till premium.")

                # ── Skicka bekräftelse-mail (utan cirkulär import) ────────────
                try:
                    msg = Message(
                        subject="Din Premium-beställning är bekräftad!",
                        sender=("SocialCard", "noreply@socialcard.se"),
                        recipients=[user.email]
                    )
                    msg.body = f"""
Hej {user.display_name or user.username}!

Tack för att du uppgraderade till Premium på SocialCard. 
Vi har mottagit din betalning och ditt konto är nu Premium-uppgraderat.

Om du har några frågor, svara gärna på detta mail eller kontakta oss direkt.

Vänliga hälsningar,
Team SocialCard
                    """.strip()

                    # Hämta Mail-instansen från appens extensions och skicka
                    mail_inst = current_app.extensions.get('mail')
                    mail_inst.send(msg)
                    print(f"[Webhook] Bekräftelsemail skickat till {user.email}")
                except Exception as e:
                    print(f"[Webhook] Kunde inte skicka bekräftelsemail: {e}")
                # ────────────────────────────────────────────────────────────

            else:
                print("[Webhook] Kunde inte hitta user för user_id:", user_id_str)
        else:
            print("[Webhook] session metadata saknar user_id")

    return '', 200
