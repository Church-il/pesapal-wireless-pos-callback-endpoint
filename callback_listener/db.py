import os
import pyodbc
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# Database Creds
DB_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
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

    # Parse the transaction_date field
    raw_date = data.get('transaction_date')
    if raw_date and raw_date.endswith('Z'):
        raw_date = raw_date[:-1]  # remove the trailing 'Z'

    try:
        if "." in raw_date:
            # Handle fractional seconds, limit to 6 digits
            date_part, fractional = raw_date.split(".")
            fractional_trimmed = fractional[:6]  # microseconds = max 6 digits
            raw_date_trimmed = f"{date_part}.{fractional_trimmed}"
            parsed_date = datetime.strptime(raw_date_trimmed, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        print("Error parsing transaction_date:", raw_date)
        raise e


    # Debug print
    print("Prepared SQL values:", (
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
        datetime.utcnow()
    ))

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
        parsed_date,
        data['currency'],
        data['merchant_reference'],
        data['confirmation_code'],
        datetime.utcnow()
    ))

    conn.commit()
    cursor.close()
    conn.close()    
