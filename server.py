from flask import Flask, request, jsonify
import os
import stripe

app = Flask(__name__)

# Load environment variables
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_SUCCESS_URL = "https://yourwebsite.com/payment-success"
STRIPE_CANCEL_URL = "https://yourwebsite.com/payment-cancel"

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

def create_stripe_checkout(amount, client_email):
    """Generate a Stripe Checkout Session with Przelewy24 as a payment method."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card", "p24"],  # Enables Przelewy24
            line_items=[
                {
                    "price_data": {
                        "currency": "pln",
                        "unit_amount": int(amount),  # Amount in cents
                        "product_data": {
                            "name": "Appointment Payment",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=STRIPE_SUCCESS_URL,
            cancel_url=STRIPE_CANCEL_URL,
            customer_email=client_email,
        )
        return session.url
    except Exception as e:
        print("Stripe Error:", str(e))
        return None

@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    """Handle webhook data from Acuity Scheduling and return only the Stripe payment link."""
    data = request.get_json()
    print("Received Acuity Data:", data)

    if not data or 'appointment' not in data:
        return jsonify({"error": "Invalid Acuity payload"}), 400

    appointment = data['appointment']
    client_email = appointment.get('email', 'No Email Provided')
    price = float(appointment.get('price', 0)) * 100  # Convert to cents

    # Generate Stripe Checkout link
    payment_link = create_stripe_checkout(price, client_email)

    if payment_link:
        return jsonify({"payment_link": payment_link}), 200
    else:
        return jsonify({"error": "Failed to generate payment link"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get Render's assigned port
    app.run(host='0.0.0.0', port=port, debug=True)
