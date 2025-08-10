import os
import psycopg2
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# East Africa Timezone
EAT = timezone(timedelta(hours=3))

# Read DB type from environment
DB_TYPE = os.getenv("DB_TYPE", "sqlserver").lower()

# SQL Server Config
SQLSERVER_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": "ODBC Driver 17 for SQL Server"
}

# PostgreSQL Config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_NAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

def get_connection():
    """Return a database connection based on DB_TYPE."""
    if DB_TYPE == "sqlserver":
        import pyodbc
        return pyodbc.connect(
            f"DRIVER={{{SQLSERVER_CONFIG['driver']}}};"
            f"SERVER={SQLSERVER_CONFIG['server']};"
            f"DATABASE={SQLSERVER_CONFIG['database']};"
            f"UID={SQLSERVER_CONFIG['username']};"
            f"PWD={SQLSERVER_CONFIG['password']}"
        )
    elif DB_TYPE == "postgres":
        
        return psycopg2.connect(**POSTGRES_CONFIG)
    else:
        raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

def save_transaction_to_db(data):
    """Save transaction data to the configured database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Parse transaction date safely
    raw_date = data.get('transaction_date')
    if not raw_date:
        raise ValueError("Missing transaction_date in data.")

    # Remove 'Z' timezone indicator if present
    if raw_date.endswith('Z'):
        raw_date = raw_date[:-1]

    # Handle fractional seconds if present
    if "." in raw_date:
        date_part, fractional = raw_date.split(".")
        fractional_trimmed = fractional[:6]  # Keep microseconds up to 6 digits
        raw_date_trimmed = f"{date_part}.{fractional_trimmed}"
        parsed_date = datetime.strptime(raw_date_trimmed, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S")

    # SQL placeholders differ for pyodbc (SQL Server) and psycopg2 (Postgres)
    placeholders = (
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?" 
        if DB_TYPE == "sqlserver" 
        else "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
    )

    cursor.execute(f'''
        INSERT INTO pesapal_transactions (
            id, first_name, last_name, phone, amount, payment_option,
            transaction_date, currency, merchant_reference, confirmation_code,
            received_at
        )
        VALUES ({placeholders})
    ''', (
        data['id'],
        data['first_name'],
        data['last_name'],
        data['phone'],
        data['amount'],
        data['payment_option'],
        parsed_date,
        data['currency'],
        data['merchant_reference'],
        data['confirmation_code'],
        datetime.now(EAT)
    ))

    conn.commit()
    cursor.close()
    conn.close()
