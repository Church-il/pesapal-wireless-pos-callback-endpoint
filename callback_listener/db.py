import os
import pyodbc
import time
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

EAT = timezone(timedelta(hours=3))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Creds
DB_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": "ODBC Driver 17 for SQL Server"
}

def get_connection(retry_count=3, retry_delay=2):
    """
    Get database connection with extended timeouts and retry logic
    
    Args:
        retry_count (int): Number of retry attempts
        retry_delay (int): Initial delay between retries (seconds)
    
    Returns:
        pyodbc.Connection: Database connection object
    """
    connection_string = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"LoginTimeout=30;"              # Login timeout (default is 15 seconds)
        f"Connection Timeout=60;"        # Overall connection timeout
        f"ConnectRetryCount=3;"          # Number of reconnect attempts
        f"ConnectRetryInterval=10;"      # Interval between reconnect attempts
        f"CommandTimeout=30;"            # Command execution timeout
        f"Encrypt=yes;"                  # Force encryption (recommended)
        f"TrustServerCertificate=no;"    # Validate server certificate
        f"MultipleActiveResultSets=no;"  # Disable MARS for better performance
    )
    
    for attempt in range(retry_count):
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{retry_count})")
            conn = pyodbc.connect(connection_string)
            logger.info("Database connection successful")
            return conn
            
        except pyodbc.OperationalError as e:
            error_msg = str(e)
            logger.error(f"Database connection attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < retry_count - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("All connection attempts failed")
                # Re-raise the exception after all retries exhausted
                raise pyodbc.OperationalError(f"Failed to connect after {retry_count} attempts: {error_msg}")
                
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {e}")
            raise

def save_transaction_to_db(data):
    """
    Save transaction data to database with enhanced error handling
    
    Args:
        data (dict): Transaction data dictionary
    """
    conn = None
    cursor = None
    
    try:
        # Get connection with retry logic
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
            logger.error(f"Error parsing transaction_date: {raw_date}")
            raise e

        # Debug print
        logger.info("Prepared SQL values: %s", (
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

        # Execute the insert with timeout handling
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
            datetime.now(EAT)
        ))

        conn.commit()
        logger.info(f"Transaction {data['id']} saved successfully")
        
    except pyodbc.OperationalError as e:
        if conn:
            conn.rollback()
        if "Login timeout expired" in str(e):
            logger.error("Database login timeout - check connection parameters and network connectivity")
        elif "Connection timeout expired" in str(e):
            logger.error("Database connection timeout - server may be unreachable")
        else:
            logger.error(f"Database operational error: {e}")
        raise e
        
    except pyodbc.IntegrityError as e:
        if conn:
            conn.rollback()
        logger.error(f"Database integrity error (possibly duplicate transaction): {e}")
        raise e
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error saving transaction to DB: {e}")
        raise e
        
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_connection():
    """
    Test database connection and return status
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True, "Database connection test successful"
    except Exception as e:
        return False, f"Database connection test failed: {str(e)}"