from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Load environment variables
PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID")
PRZELEWY24_API_KEY = os.getenv("PRZELEWY24_API_KEY")
ACUITY_API_KEY = os.getenv("ACUITY_API_KEY")  # For storing payment link in Acuity

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

def store_payment_link(appointment_id, payment_link):
    """Store the payment link inside Acuity's custom field."""
    acuity_url = f"https://acuityscheduling.com/api/v1/appointments/{appointment_id}"
    headers = {"Authorization": f"Bearer {ACUITY_API_KEY}"}
    
    # Replace 'CUSTOM_FIELD_ID' with the actual field ID from Acuity
    payload = {"fields": [{"id": "CUSTOM_FIELD_ID", "value": payment_link}]}

    response = requests.put(acuity_url, json=payload, headers=headers)
    return response.status_code == 200

@app.route('/')
def home():
    return "Server is running!", 200

@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    """Handle webhook data from Acuity Scheduling and generate a payment link."""
    data = request.get_json()
    print("Received Acuity Data:", data)

    if not data or 'appointment' not in data:
        return jsonify({"error": "Invalid Acuity payload"}), 400

    appointment = data['appointment']
    appointment_id = appointment['id']
    client_email = appointment.get('email', 'No Email Provided')
    price = float(appointment.get('price', 0)) * 100  # Convert to cents

    # Generate the payment link
    payment_link = create_payment_link(price, client_email)

    if payment_link:
        print(f"Payment link for {client_email}: {payment_link}")

        # Store it in Acuity's custom field
        stored = store_payment_link(appointment_id, payment_link)

        if stored:
            return jsonify({"message": "Payment link stored in Acuity!", "payment_link": payment_link}), 200
        else:
            return jsonify({"message": "Payment link generated, but could not store in Acuity", "payment_link": payment_link}), 500
    else:
        return jsonify({"error": "Failed to generate payment link"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get Render's assigned port
    app.run(host='0.0.0.0', port=port, debug=True)
