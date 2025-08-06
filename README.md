# Pesapal Wireless POS Callback Listener

A complete Flask application that receives Pesapal wireless POS transaction callbacks over HTTPS and stores them in a SQL Server database.

## 🚀 Features

- **HTTPS SSL Support** - Secure callback endpoint
- **SQL Server Integration** - Stores transactions in SQL Server Express
- **Request Validation** - Validates required fields and JSON format
- **Comprehensive Logging** - Detailed transaction and error logging
- **Error Handling** - Graceful error handling with proper HTTP responses

## 📋 Prerequisites

- Python 3.8+
- SQL Server Express (.\SQLEXPRESS)
- SSL certificate and private key
- ODBC Driver 17 for SQL Server
- Port 443 available for HTTPS

## 📁 Project Structure

```
callback_listener/
├── app.py                  # Main Flask application
├── db.py                   # Database connection and operations
├── requirements.txt        # Python dependencies
├── certs/
│   ├── fullchain.pem      # SSL certificate (public)
│   └── privkey.pem        # SSL private key
├── logs/
│   └── pesapal.log        # Transaction and error logs
└── transactions.db        # Auto-created database file
```

## ⚙️ Installation

### 1. Install Python Dependencies

```bash
pip install Flask==2.3.3 pyodbc
```

### 2. Install ODBC Driver

Download and install the ODBC Driver 17 for SQL Server:
- [Microsoft ODBC Driver Download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 3. Generate SSL Certificates (for testing)

```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes
```

*Note: Use dummy information when prompted for certificate details.*

## 🗄️ Database Setup

### Step 1: Create Database in SQL Server Management Studio (SSMS)

1. Open **SQL Server Management Studio (SSMS)**
2. Connect to `.\SQLEXPRESS` using Windows Authentication
3. Click **"New Query"** in the toolbar
4. Run the following SQL commands:

```sql
-- Create the database
CREATE DATABASE PesapalDB;
GO

-- Use the new database
USE PesapalDB;
GO

-- Create the transactions table
CREATE TABLE pesapal_transactions (
    id INT PRIMARY KEY,
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    phone NVARCHAR(20),
    amount DECIMAL(18,2),
    payment_option NVARCHAR(50),
    transaction_date DATETIME,
    currency NVARCHAR(10),
    merchant_reference NVARCHAR(100),
    confirmation_code NVARCHAR(100),
    received_at DATETIME
);
```

### Step 2: Configure SQL Server Authentication

1. In SSMS Object Explorer, right-click the server name (e.g., `MICHAELAKOKO\SQLEXPRESS`) → **Properties**
2. Go to **Security** tab
3. Select **"SQL Server and Windows Authentication mode"**
4. Click **OK**
5. **Restart SQL Server** via SQL Server Configuration Manager

### Step 3: Enable SA Account

1. In SSMS, expand **Security** → **Logins**
2. Right-click **sa** → **Properties**
3. **General tab**: Set a strong password
4. **Status tab**: 
   - Set **Login**: Enabled
   - Set **Permission to connect**: Grant
5. Click **OK**

## 💻 Code Implementation

### db.py - Database Operations

```python
import pyodbc
from datetime import datetime

# Database Credentials
DB_CONFIG = {
    "server": "localhost\\SQLEXPRESS",
    "database": "PesapalDB",
    "username": "sa",
    "password": "your_strong_password",  # Replace with your actual password
    "driver": "ODBC Driver 17 for SQL Server"
}

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )

def save_transaction_to_db(data):
    conn = get_connection()
    cursor = conn.cursor()

    # Parse and clean transaction_date
    raw_date = data.get('transaction_date')
    try:
        # Handles format with Zulu time and full microseconds
        transaction_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        # Fallback: trim microseconds if they exceed 6 digits
        transaction_date = datetime.strptime(raw_date[:26], "%Y-%m-%dT%H:%M:%S.%f")

    cursor.execute('''
        INSERT INTO pesapal_transactions (
            id, first_name, last_name, phone, amount, payment_option,
            transaction_date, currency, merchant_reference, confirmation_code,
            received_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['id'],
        data['first_name'],
        data['last_name'],
        data['phone'],
        data['amount'],
        data['payment_option'],
        transaction_date,
        data['currency'],
        data['merchant_reference'],
        data['confirmation_code'],
        datetime.utcnow()
    ))

    conn.commit()
    cursor.close()
    conn.close()
```

### app.py - Flask Application

```python
from flask import Flask, request, jsonify
import logging
import os
from db import save_transaction_to_db

app = Flask(__name__)

# Logging setup
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
        logging.info("Transaction saved successfully.")
    except Exception as e:
        logging.exception("Error saving transaction to DB")
        return jsonify(status="500", message="Internal server error"), 500

    return jsonify(status="200", message="Ok"), 200

if __name__ == '__main__':
    # SSL Certificate paths
    ssl_context = ('certs/fullchain.pem', 'certs/privkey.pem')

    # Run on port 443 (HTTPS)
    app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)
```

## 🚀 Running the Application

1. **Update Database Credentials**: Edit the password in `db.py`
2. **Start the Application**:
   ```bash
   python app.py
   ```
3. **Verify Setup**: The server should start on `https://localhost:443/pesapal-callback`

## 🧪 Testing

### Test with curl

```bash
curl -X POST https://localhost/pesapal-callback \
  --insecure \
  -H "Content-Type: application/json" \
  -d '{
    "id":10463,
    "first_name":"joe",
    "last_name":"doe",
    "phone":"+254712345678",
    "amount":1.0,
    "payment_option":"Visa",
    "transaction_date":"2022-02-04T14:19:05.0210431Z",
    "currency":"KES",
    "merchant_reference":"TEST",
    "confirmation_code":"test10"
  }'
```

*Note: `--insecure` flag skips SSL verification for self-signed certificates.*

### Verify Data in Database

In SQL Server Management Studio:

```sql
USE PesapalDB;
SELECT * FROM pesapal_transactions;
```

## 📊 Expected Transaction Structure

The callback endpoint expects JSON payloads with the following structure:

```json
{
  "id": 10463,
  "first_name": "john",
  "last_name": "doe",
  "phone": "+254712345678",
  "amount": 100.50,
  "payment_option": "Visa",
  "transaction_date": "2022-02-04T14:19:05.0210431Z",
  "currency": "KES",
  "merchant_reference": "INV001",
  "confirmation_code": "ABC123"
}
```

## 🔧 Troubleshooting

### Common Issues

**1. Login Failed Error (18456)**
- Ensure SQL Server is in Mixed Mode Authentication
- Verify SA account is enabled with correct password
- Restart SQL Server after authentication changes

**2. Date Conversion Error (22007)**
- The datetime parsing in `db.py` handles ISO 8601 format with microseconds
- Ensure `transaction_date` column is `DATETIME` or `DATETIME2` type

**3. SSL Certificate Issues**
- For production, use valid SSL certificates from a trusted CA
- For testing, use the `--insecure` flag with curl

**4. Port 443 Access Denied**
- Run as administrator/sudo for port 443
- Or use alternative port like 8443 for testing

## 🚀 Production Considerations

- **Web Server**: Use Gunicorn, uWSGI, or Waitress instead of Flask's dev server
- **SSL Certificates**: Obtain valid certificates from Let's Encrypt or commercial CA
- **Database**: Consider connection pooling for high-volume transactions
- **Security**: Implement IP whitelisting for Pesapal's servers
- **Monitoring**: Add health check endpoints and monitoring

## 📝 Logging

The application logs to `logs/pesapal.log` with:
- Transaction receipts
- Validation errors
- Database errors
- Connection issues

## 🔒 Security Notes

- Store database credentials securely
- Use HTTPS only for production and generate certs for local
- Consider rate limiting for the callback endpoint

## 📞 Support

For issues with:
- **Pesapal Integration**: write to me -> **akokomichael37@gmail.com**
- **SQL Server**: Check Microsoft documentation
- **Flask Application**: Review logs in `logs/pesapal.log`