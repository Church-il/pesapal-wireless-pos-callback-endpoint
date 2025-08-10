import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

if os.getenv("RENDER") is None:
    # Only load local .env when not running on Render
    load_dotenv()

# East Africa Timezone (UTC+3)
EAT = timezone(timedelta(hours=3))

# DB type: 'sqlserver' (local) or 'postgres' (Render)
DB_TYPE = os.getenv("DB_TYPE", "postgres").lower()

print(f"DB_TYPE is: {DB_TYPE}")


# SQL Server config (local)
SQLSERVER_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": "ODBC Driver 17 for SQL Server"
}

# Postgres config (Render)
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

def get_connection():
    """Return a DB connection based on DB_TYPE."""
    if DB_TYPE == "sqlserver":
        import pyodbc  # Import here to avoid errors if pyodbc isn't installed on Render
        conn_str = (
            f"DRIVER={{{SQLSERVER_CONFIG['driver']}}};"
            f"SERVER={SQLSERVER_CONFIG['server']};"
            f"DATABASE={SQLSERVER_CONFIG['database']};"
            f"UID={SQLSERVER_CONFIG['username']};"
            f"PWD={SQLSERVER_CONFIG['password']}"
        )
        return pyodbc.connect(conn_str)
    
    elif DB_TYPE == "postgres":
        import psycopg2
        return psycopg2.connect(**POSTGRES_CONFIG)
    
    else:
        raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

def save_transaction_to_db(data):
    """Save transaction data to the configured database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Parse transaction_date string safely
    raw_date = data.get('transaction_date')
    if not raw_date:
        raise ValueError("Missing transaction_date in data.")

    # Remove trailing 'Z' if present (UTC indicator)
    if raw_date.endswith('Z'):
        raw_date = raw_date[:-1]

    # Handle fractional seconds safely (truncate to 6 digits for microseconds)
    if '.' in raw_date:
        date_part, fractional = raw_date.split('.', 1)
        fractional_trimmed = fractional[:6]  # max 6 digits for microseconds
        raw_date_trimmed = f"{date_part}.{fractional_trimmed}"
        parsed_date = datetime.strptime(raw_date_trimmed, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S")

    # Set placeholders depending on DB driver
    placeholders = (
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?" if DB_TYPE == "sqlserver" else
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
    )

    cursor.execute(f"""
        INSERT INTO pesapal_transactions (
            id, first_name, last_name, phone, amount, payment_option,
            transaction_date, currency, merchant_reference, confirmation_code,
            received_at
        ) VALUES ({placeholders})
    """, (
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
