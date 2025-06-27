import os
import stripe
from flask import Flask, request, redirect
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ✅ Stripe API key from environment variable
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# ✅ Send email via Outlook SMTP
def send_email(to_email):
    from_email = os.environ.get('EMAIL_SENDER')
    password = os.environ.get('EMAIL_PASSWORD')

    subject = "Payment Confirmation"
    body = "Thank you! Your payment was received successfully."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP('smtp.office365.com', 587) as smtp:
        smtp.starttls()
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, msg.as_string())

@app.route('/')
def index():
    return '''
        <h2>Send a Payment</h2>
        <form action="/create-checkout-session" method="POST">
            <label>Amount you want to send ($):</label><br>
            <input name="amount" type="number" step="0.01" required><br><br>

            <label>Payment Method:</label><br>
            <input type="radio" name="method" value="card" checked> Card (Fee Added)<br>
            <input type="radio" name="method" value="ach"> ACH Bank Transfer (No Fee)<br><br>

            <button type="submit">Pay</button>
        </form>
    '''

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        amount = float(request.form['amount'])
        method = request.form['method']

        if method == 'card':
            fixed_fee = 0.30
            percent_fee = 0.029
            total = (amount + fixed_fee) / (1 - percent_fee)
            item_name = f'Payment via CARD for ${amount:.2f} + Fee'
            payment_methods = ['card']
        else:
            total = amount
            item_name = f'Payment via ACH for ${amount:.2f}'
            payment_methods = ['us_bank_account']

        total_cents = round(total * 100)

        session = stripe.checkout.Session.create(
            payment_method_types=payment_methods,
            customer_email=None,  # Stripe will prompt for email in Checkout
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item_name
                    },
                    'unit_amount': total_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://stripe-checkout-398f.onrender.com/success',
            cancel_url='https://stripe-checkout-398f.onrender.com/cancel',
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return f"Error: {str(e)}", 500

# ✅ Confirmation Page Route
@app.route('/success')
def success():
    return '''
        <h2>✅ Payment Successful!</h2>
        <p>Thank you — your payment was received. A confirmation email has been sent to you.</p>
        <a href="/">Return to home</a>
    '''

# ✅ Cancel Page Route
@app.route('/cancel')
def cancel():
    return '''
        <h2>❌ Payment Cancelled</h2>
        <p>No worries — your payment wasn’t completed. You can try again anytime.</p>
        <a href="/">Return to home</a>
    '''

# ✅ Webhook listener for Stripe events
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return f"Webhook Error: {str(e)}", 400

    # ✅ Trigger on successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')

        if customer_email:
            send_email(customer_email)

    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
