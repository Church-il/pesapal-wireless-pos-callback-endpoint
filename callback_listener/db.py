import os
from datetime import datetime, timedelta, timezone

# East Africa Timezone (UTC+3)
EAT = timezone(timedelta(hours=3))

def get_db_type():
    db_type = os.getenv("DB_TYPE", "sqlserver")
    if db_type:
        return db_type.lower()
    return "sqlserver"

def get_sqlserver_config():
    return {
        "server": os.getenv("DB_SERVER"),
        "database": os.getenv("DB_NAME"),
        "username": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "driver": "ODBC Driver 17 for SQL Server"
    }

def get_postgres_config():
    return {
        "host": os.getenv("POSTGRES_HOST"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
    }

def get_connection():
    db_type = get_db_type()
    print(f"DB_TYPE in get_connection(): {db_type}")

    if db_type == "sqlserver":
        import pyodbc
        cfg = get_sqlserver_config()
        conn_str = (
            f"DRIVER={{{cfg['driver']}}};"
            f"SERVER={cfg['server']};"
            f"DATABASE={cfg['database']};"
            f"UID={cfg['username']};"
            f"PWD={cfg['password']}"
        )
        return pyodbc.connect(conn_str)

    elif db_type == "postgres":
        import psycopg2
        cfg = get_postgres_config()
        return psycopg2.connect(**cfg)

    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")

def save_transaction_to_db(data):
    conn = get_connection()
    cursor = conn.cursor()

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

    placeholders = (
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?" if get_db_type() == "sqlserver" else
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
