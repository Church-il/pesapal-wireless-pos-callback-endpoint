from flask import Flask, request, jsonify
import logging
import os
import sys
from callback_listener.db import save_transaction_to_db

app = Flask(__name__)

# ===============================
# Dual Logging Setup (File + Render stdout)
# ===============================
log_dir = 'logs'
log_file = os.path.join(log_dir, 'pesapal.log')

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

# Set up a root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clear any existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# File handler for internal logs
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

# Console handler for Render stdout logs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

# Add both handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ===============================
# Global Error Handler
# ===============================
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"message": "Internal server error", "status": "500"}), 500

# ===============================
# Expected Payload Fields
# ===============================
REQUIRED_FIELDS = [
    "id", "first_name", "last_name", "phone", "amount",
    "payment_option", "transaction_date", "currency",
    "merchant_reference", "confirmation_code"
]

# ===============================
# Callback Endpoint
# ===============================
@app.route('/pesapal-callback', methods=['POST'])
def pesapal_callback():
    if not request.is_json:
        logger.warning("Non-JSON request received.")
        return jsonify(status="400", message="Invalid content type. Expecting application/json"), 400

    data = request.get_json()
    missing_fields = [field for field in REQUIRED_FIELDS if field not in data]

    if missing_fields:
        logger.error(f"Missing fields in payload: {missing_fields}")
        return jsonify(status="400", message=f"Missing fields: {missing_fields}"), 400

    logger.info(f"Transaction received from {request.remote_addr}: {data}")

    try:
        save_transaction_to_db(data)
    except Exception as e:
        logger.exception("Error saving transaction to DB")
        return jsonify(status="500", message="Internal server error"), 500

    logger.info("Transaction saved successfully.")
    return jsonify(status="200", message="Ok"), 200

# ===============================
# Run App
# ===============================
if __name__ == '__main__':
    # For local HTTPS testing with certs
    # ssl_context = ('certs/fullchain.pem', 'certs/privkey.pem')
    # app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)

    # For HTTP testing or cloud deployment (e.g. Render)
    app.run(host='0.0.0.0', port=10000)
