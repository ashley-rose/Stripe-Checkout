import stripe
from flask import Flask, request, redirect

app = Flask(__name__)

# REPLACE THIS with your actual Stripe Secret Key
stripe.api_key = 'sk_test_51LKOjaBbaYzPvUYj0r24EILaDTBMtft1YhgjZqYObQsdjTuIFTQrvL8vdyNS1kLxwDjxBwdDeWOK4SQsC74ckXvG00b2hCb3LL'

@app.route('/')
def index():
    return '''
        <h2>Enter the amount you want to send (we’ll add the card fee)</h2>
        <form action="/create-checkout-session" method="POST">
            <input name="amount" type="number" step="0.01" required>
            <button type="submit">Pay</button>
        </form>
    '''

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        amount = float(request.form['amount'])

        # Stripe fee logic
        fixed_fee = 0.30
        percent_fee = 0.029
        total = (amount + fixed_fee) / (1 - percent_fee)
        total_cents = round(total * 100)  # Stripe uses cents

        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Payment of ${amount:.2f}'},
                    'unit_amount': total_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
