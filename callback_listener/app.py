from flask import Flask, request, jsonify
import logging
import os
from db import save_transaction_to_db

app = Flask(__name__)

# logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/pesapal.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

REQUIRED_FIELDS = [
    "id", "first_name", "last_name", "phone", "amount",
    "payment_option", "transaction_date", "currency",
    "merchant_reference", "confirmation_code"
]

@app.route('/pesapal-callback', methods=['POST'])
def pesapal_callback():
    if not request.is_json:
        logging.warning("Non-JSON request received.")
        return jsonify(status="400", message="Invalid content type. Expecting application/json"), 400

    data = request.get_json()
    missing_fields = [field for field in REQUIRED_FIELDS if field not in data]

    if missing_fields:
        logging.error(f"Missing fields in payload: {missing_fields}")
        return jsonify(status="400", message=f"Missing fields: {missing_fields}"), 400

    logging.info(f"Transaction received from {request.remote_addr}: {data}")

    try:
        save_transaction_to_db(data)
    except Exception as e:
        logging.exception("Error saving transaction to DB")
        return jsonify(status="500", message="Internal server error"), 500
    logging.info("Transaction saved successfully.")
    return jsonify(status="200", message="Ok"), 200

if __name__ == '__main__':
    

    # SSL Certificate paths
    ssl_context = ('certs/fullchain.pem', 'certs/privkey.pem')

    # Please run on port 443 (HTTPS) - whenever you are testing locally - 
    # ssh has to be set up to forward port 443 to your local machine
    # Uncomment the line below to run the app with SSL context:
    app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)
    
    #app.run(host='0.0.0.0', port=10000)
