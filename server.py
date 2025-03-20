from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Load environment variables
PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID")
PRZELEWY24_API_KEY = os.getenv("PRZELEWY24_API_KEY")

# Przelewy24 API URL
PRZELEWY24_URL = "https://secure.przelewy24.pl/api/v1/transaction/register"

def create_payment_link(amount, client_email):
    """Generate a Przelewy24 payment link for the given amount and email."""
    payload = {
        "merchantId": PRZELEWY24_MERCHANT_ID,
        "posId": PRZELEWY24_MERCHANT_ID,
        "sessionId": "unique-session-id",
        "amount": int(amount),  # In cents
        "currency": "PLN",
        "description": "Appointment Payment",
        "email": client_email,
        "country": "PL",
        "language": "pl",
        "urlReturn": "https://yourwebsite.com/payment-success",
        "urlStatus": "https://your-app-name.onrender.com/payment-status",
        "sign": "your_generated_signature"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PRZELEWY24_API_KEY}"
    }

    response = requests.post(PRZELEWY24_URL, json=payload, headers=headers)

    if response.status_code == 200:
        payment_data = response.json()
        return payment_data.get('data', {}).get('url', None)

    print("Payment error:", response.text)
    return None

@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    """Handle webhook data from Acuity Scheduling and return only the payment link."""
    data = request.get_json()
    print("Received Acuity Data:", data)

    if not data or 'appointment' not in data:
        return jsonify({"error": "Invalid Acuity payload"}), 400

    appointment = data['appointment']
    client_email = appointment.get('email', 'No Email Provided')
    price = float(appointment.get('price', 0)) * 100  # Convert to cents

    # Generate the payment link
    payment_link = create_payment_link(price, client_email)

    if payment_link:
        return jsonify({"payment_link": payment_link}), 200
    else:
        return jsonify({"error": "Failed to generate payment link"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get Render's assigned port
    app.run(host='0.0.0.0', port=port, debug=True)
