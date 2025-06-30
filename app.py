import os
import stripe
from flask import Flask, request, redirect
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, static_folder='static')
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

# ✅ Styled homepage
@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Send a Payment</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f6f9fc;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
                box-sizing: border-box;
                text-align: center;
            }
            .logo {
                max-width: 160px;
                margin-bottom: 20px;
            }
            h2 {
                margin-bottom: 20px;
                color: #32325d;
            }
            label {
                display: block;
                margin-top: 15px;
                margin-bottom: 5px;
                text-align: left;
                color: #525f7f;
            }
            input[type="number"] {
                width: 100%;
                padding: 10px;
                font-size: 16px;
                margin-bottom: 10px;
                border: 1px solid #ccd0d5;
                border-radius: 4px;
                box-sizing: border-box;
            }
            .radio {
                text-align: left;
                margin-bottom: 20px;
                color: #525f7f;
            }
            button {
                background-color: #6772e5;
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 16px;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
            }
            button:hover {
                background-color: #5469d4;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img class="logo" src="/static/logo.png" alt="Company Logo">
            <h2>Secure Payment</h2>
            <form action="/create-checkout-session" method="POST">
                <label>Amount you want to send ($):</label>
                <input name="amount" type="number" step="0.01" required>

                <div class="radio">
                    <label><input type="radio" name="method" value="card" checked> Card (Fee Added)</label><br>
                    <label><input type="radio" name="method" value="ach"> ACH Bank Transfer (No Fee)</label>
                </div>

                <button type="submit">Pay Securely</button>
            </form>
        </div>
    </body>
    </html>
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
            customer_email=None,
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

@app.route('/success')
def success():
    return '''
    <html><head><title>Payment Successful</title>
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
           background-color: #f6f9fc; display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; }
    .container { background: white; padding: 40px; border-radius: 8px;
                 box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 400px; text-align: center; }
    h2 { color: #2ecc71; }
    p { color: #525f7f; }
    a { display: inline-block; background-color: #6772e5; color: white;
        padding: 12px 20px; border-radius: 4px; text-decoration: none; }
    a:hover { background-color: #5469d4; }
    </style></head>
    <body><div class="container">
    <h2>✅ Payment Successful</h2>
    <p>Thank you — your payment was received. A confirmation email has been sent.</p>
    <a href="/">Return to Home</a></div></body></html>
    '''

@app.route('/cancel')
def cancel():
    return '''
    <html><head><title>Payment Canceled</title>
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
           background-color: #f6f9fc; display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; }
    .container { background: white; padding: 40px; border-radius: 8px;
                 box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 400px; text-align: center; }
    h2 { color: #e74c3c; }
    p { color: #525f7f; }
    a { display: inline-block; background-color: #6772e5; color: white;
        padding: 12px 20px; border-radius: 4px; text-decoration: none; }
    a:hover { background-color: #5469d4; }
    </style></head>
    <body><div class="container">
    <h2>❌ Payment Canceled</h2>
    <p>No worries — your payment wasn’t completed. You can try again anytime.</p>
    <a href="/">Return to Home</a></div></body></html>
    '''

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return f"Webhook Error: {str(e)}", 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        if customer_email:
            send_email(customer_email)

    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
