import os    
import stripe
from flask import Flask, request, redirect

app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

@app.route('/')
def index():
    return '''
        <h2>Send a Payment</h2>
        <form action="/create-checkout-session" method="POST">
            <label>Amount you want to send ($):</label><br>
            <input name="amount" type="number" step="0.01" required><br><br>

            <label>Payment Method:</label><br>
            <input type="radio" name="method" value="card" checked> Card (fee added)<br>
            <input type="radio" name="method" value="ach"> ACH Bank Transfer (no fee)<br><br>

            <button type="submit">Pay</button>
        </form>
    '''

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        amount = float(request.form['amount'])
        method = request.form['method']

        if method == 'card':
            # Apply fee
            fixed_fee = 0.30
            percent_fee = 0.029
            total = (amount + fixed_fee) / (1 - percent_fee)
        else:
            # No fee for ACH
            total = amount

        total_cents = round(total * 100)

        # Set payment method types based on user choice
        if method == 'card':
            payment_methods = ['card']
        else:
            payment_methods = ['us_bank_account']

        session = stripe.checkout.Session.create(
            payment_method_types=payment_methods,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Payment via {method.upper()} for ${amount:.2f}'
                    },
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
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
