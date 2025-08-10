from flask import Flask, request, jsonify
import logging
from datetime import datetime, timedelta, timezone
import os
import sys
from db import save_transaction_to_db
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE")
if not DB_TYPE:
    DB_TYPE = os.environ.get("DB_TYPE")  # fallback to env var set by Render or Docker

print("DB_TYPE:", DB_TYPE)

EAT = timezone(timedelta(hours=3))

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
        "timestamp": datetime.now(EAT).isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
                margin-bottom: 1rem;
            }
            .logo img {
                max-width: 200px;
                max-height: 80px;
                width: auto;
                height: auto;
                filter: brightness(1.1);
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
            <div class="logo">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhzoCjQJNz7hYHw-9zYEgI-5Qx7QkpH63-aA&s" alt="Pesapal Logo" />
            </div>
            <h1>Pesapal Wireless POS</h1>
            <p class="subtitle">Callback Endpoint Listener</p>
            <div class="status-indicator">
                <div class="dot"></div>
                Service Running
            </div>
            <div class="info">
                <p>Version: 1.0.0</p>
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
    except Exception:
        logger.exception("Error saving transaction to DB")
        return jsonify(status="500", message="Internal server error"), 500

    logger.info("Transaction saved successfully.")
    return jsonify(status="200", message="Ok"), 200

# ===============================
# Run App
# ===============================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8999))
    ssl_cert = os.getenv("SSL_CERT_PATH")
    ssl_key = os.getenv("SSL_KEY_PATH")

    if ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print(f"🔐 Running with HTTPS on port {port}")
        app.run(host="0.0.0.0", port=port, ssl_context=(ssl_cert, ssl_key))
    else:
        print(f"⚠️ Running without SSL on port {port}")
        app.run(host="0.0.0.0", port=port)
        
