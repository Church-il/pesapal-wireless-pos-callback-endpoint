from flask import Flask, request, jsonify, render_template
import logging
import datetime
import os
import sys
from callback_listener.db import save_transaction_to_db

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# ===============================
# Dual Logging Setup (File + Render stdout)
# ===============================
log_dir = 'logs'
log_file = os.path.join(log_dir, 'pesapal.log')


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
# Root Health Check Endpoint
# ===============================
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "pesapal-callback-endpoint"
    }), 200


# ===============================
# App Root Endpoint
# ===============================
@app.route('/')
def home():
    # Check if request wants JSON
    if request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            "service": "Pesapal Wireless POS Callback Endpoint",
            "status": "running",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0"
        })
    
    # Return simple HTML
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pesapal Wireless POS - Callback Service</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .card {
                background: linear-gradient(145deg, #1e293b, #334155);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            .logo {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            h1 {
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: #f1f5f9;
            }
            .subtitle {
                color: #94a3b8;
                margin-bottom: 2rem;
            }
            .status-indicator {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: #10b981;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 50px;
                font-weight: 600;
                animation: glow 2s ease-in-out infinite alternate;
            }
            @keyframes glow {
                from { box-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }
                to { box-shadow: 0 0 20px rgba(16, 185, 129, 0.6); }
            }
            .dot {
                width: 8px;
                height: 8px;
                background: white;
                border-radius: 50%;
                animation: pulse 1s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .info {
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid #334155;
                font-size: 0.9rem;
                color: #64748b;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">🏪</div>
            <h1>Pesapal Wireless POS</h1>
            <p class="subtitle">Callback Endpoint Service</p>
            <div class="status-indicator">
                <div class="dot"></div>
                Service Running
            </div>
            <div class="info">
                Ready to receive payment callbacks
            </div>
        </div>
    </body>
    </html>
    """

# Favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content status code

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
    #ssl_context = ('certs/fullchain.pem', 'certs/privkey.pem')
    #app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), ssl_context=ssl_context)

    # Enable debug mode for local testing
    #app.debug = True  
    
    
    # For HTTP testing or cloud deployment (e.g. Render)
    # Use PORT environment variable for flexibility
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))