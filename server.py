from flask import Flask, request, jsonify
import requests
import hashlib
import os

app = Flask(__name__)

# Environment Variables (Set these in your hosting environment)
ACUITY_API_KEY = os.getenv("ACUITY_API_KEY", "your_acuity_api_key")
PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID", "your_merchant_id")
PRZELEWY24_CRC_KEY = os.getenv("PRZELEWY24_CRC_KEY", "your_crc_key")

# Webhook to handle new appointments
@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    data = request.json
    appointment_id = data.get('id')
    email = data.get('email')
    amount = int(float(data.get('price')) * 100)  # Convert to cents
    session_id = f"order_{appointment_id}"

    # Generate Przelewy24 signature
    sign_data = f"{PRZELEWY24_MERCHANT_ID}|{session_id}|{amount}|PLN|{PRZELEWY24_CRC_KEY}"
    sign = hashlib.sha384(sign_data.encode()).hexdigest()

    # Create payment request to Przelewy24
    payment_request = {
        "merchantId": PRZELEWY24_MERCHANT_ID,
        "sessionId": session_id,
        "amount": amount,
        "currency": "PLN",
        "description": "Appointment Payment",
        "email": email,
        "country": "PL",
        "language": "pl",
        "urlReturn": "https://yourwebsite.com/thank-you",
        "urlStatus": "https://yourserver.com/payment-webhook",
        "sign": sign
    }

    response = requests.post("https://secure.przelewy24.pl/api/v1/transaction/register", json=payment_request)
    response_data = response.json()

    if 'data' in response_data and 'token' in response_data['data']:
        payment_link = f"https://secure.przelewy24.pl/trnRequest/{response_data['data']['token']}"

        # Update Acuity appointment notes with the payment link
        acuity_url = f"https://acuityscheduling.com/api/v1/appointments/{appointment_id}/notes"
        headers = {"Content-Type": "application/json"}
        auth = (ACUITY_API_KEY, '')

        acuity_data = {"note": f"Payment link: {payment_link}"}
        requests.post(acuity_url, json=acuity_data, headers=headers, auth=auth)

        return jsonify({"message": "Payment link created and added to appointment", "payment_link": payment_link})
    else:
        return jsonify({"error": "Failed to create payment link"}), 400

# Webhook to handle Przelewy24 payment notifications
@app.route('/payment-webhook', methods=['POST'])
def handle_payment():
    data = request.json
    if data.get("status") == "success":
        session_id = data.get("sessionId")
        order_id = data.get("orderId")
        amount = data.get("amount")

        # Generate verification signature
        sign_data = f"{PRZELEWY24_MERCHANT_ID}|{session_id}|{amount}|PLN|{order_id}|{PRZELEWY24_CRC_KEY}"
        sign = hashlib.sha384(sign_data.encode()).hexdigest()

        verification_request = {
            "merchantId": PRZELEWY24_MERCHANT_ID,
            "sessionId": session_id,
            "amount": amount,
            "currency": "PLN",
            "orderId": order_id,
            "sign": sign
        }

        verify_response = requests.post("https://secure.przelewy24.pl/api/v1/transaction/verify", json=verification_request)
        verify_data = verify_response.json()

        if verify_data.get("data", {}).get("status") == "success":
            return jsonify({"message": "Payment verified successfully"}), 200
        else:
            return jsonify({"error": "Payment verification failed"}), 400
    return jsonify({"error": "Invalid payment status"}), 400
import os

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get the Render-assigned port
    app.run(host='0.0.0.0', port=port, debug=True)

