from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is running!", 200

@app.route('/acuity-webhook', methods=['POST'])
def handle_appointment():
    # Print raw request data to debug
    print("Raw request data:", request.data)
    print("Headers:", request.headers)

    try:
        # Ensure JSON is being received correctly
        data = request.get_json()
        print("Parsed JSON:", data)  # Debugging log

        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400
        if 'price' not in data:
            return jsonify({"error": "Missing 'price' field"}), 400

        # Convert price to cents
        amount = int(float(data['price']) * 100)

        return jsonify({
            "message": "Webhook received!",
            "amount": amount
        }), 200

    except Exception as e:
        print("Error:", str(e))  # Print any error for debugging
        return jsonify({"error": "Invalid request format"}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Get Render's assigned port
    app.run(host='0.0.0.0', port=port, debug=True)
