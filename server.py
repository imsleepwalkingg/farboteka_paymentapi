from flask import Flask, request, jsonify
import os
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Load environment variables
PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID")
PRZELEWY24_API_KEY = os.getenv("PRZELEWY24_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # SendGrid API Key
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # Your verified sender email

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

def send_email(to_email, payment_link):
    """Send an email with the payment link using SendGrid."""
    subject = "Complete Your Payment for Your Appointment"
    body = f"""
    Hello,

    Thank you for booking an appointment. Please complete your payment using the link below:

    {payment_link}

    If you have any questions, feel free to reach out.

    Best regards,
    Your Business
    """
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.sendgrid.net", 587)
        server.starttls()
        server.login("apikey", SENDGRID_API_KEY)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/')
def home():
    return "Server is running!", 200

@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    """Handle webhook data from Acuity Scheduling and generate a payment link."""
    data = request.get_json()
    print("Received Acuity Data:", data)  # Debugging log

    if not data or 'appointment' not in data:
        return jsonify({"error": "Invalid Acuity payload"}), 400

    appointment = data['appointment']
    client_email = appointment.get('email', 'No Email Provided')
    price = float(appointment.get('price', 0)) * 100  # Convert to cents

    # Create a payment link
    payment_link = create_payment_link(price, client_email)

    if payment_link:
        print(f"Payment link for {client_email}: {payment_link}")

        # Send payment link via email
        email_sent = send_email(client_email, payment_link)
        if email_sent:
            return jsonify({"message": "Payment link generated and email sent!", "payment_link": payment_link}), 200
        else:
            return jsonify({"message": "Payment link generated, but email failed!", "payment_link": payment_link}), 500
    else:
        return jsonify({"error": "Failed to generate payment link"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get Render's assigned port
    app.run(host='0.0.0.0', port=port, debug=True)
