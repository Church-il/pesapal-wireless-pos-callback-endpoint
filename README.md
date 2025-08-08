# Pesapal Wireless POS Callback Listener

A Python + Flask application that receives Pesapal wireless POS transaction callbacks and stores them in a remote SQL Server database, with support for Docker deployment on [Render.com](https://render.com). Please refer to the [Pesapal Wireless POS Documentation](https://developer.pesapal.com/how-to-integrate/point-of-sale/wireless-connection) for integration details.

---

## 🚀 Features

- **Secure HTTPS Callback Handling**  
- **SQL Server Integration (via ODBC Driver 17)**  
- **Production-ready Deployment with Docker**  
- **Support for Render Deployment with `.env` Secrets**  
- **Structured Logging (Local File + Render Logs)**  
- **Robust Date Parsing and Validation**

---

## 📦 Deployment Options

### 🔹 Local Development

You can run the app locally for testing and debugging.

### 🔹 Render Deployment (Docker)

Deploy easily to Render using Docker with a `render.yaml` and `.env` file.

---

## 📁 Project Structure

```
callback_listener/
├── app.py                  # Flask entrypoint
├── db.py                   # SQL Server DB logic
├── requirements.txt        # Python packages
├── Dockerfile              # Docker build config
├── render.yaml             # Render deployment file
├── .env                    # Environment variables (not committed)
├── certs/                  # SSL certificate folder (optional)
│   ├── fullchain.pem       
│   └── privkey.pem         
├── logs/
│   └── pesapal.log         # Local log output
```

---

## ⚙️ Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup `.env`

Create a `.env` file at the project root:

```
DB_SERVER=localhost
DB_NAME=PesapalDB
DB_USERNAME=sa
DB_PASSWORD=your_password
PORT=10000
```

### 3. Generate SSL Certificates (Optional for Local)

```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes
```

---

## 🐳 Docker Deployment

### Dockerfile Overview

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y     curl gnupg apt-transport-https unixodbc unixodbc-dev gcc g++     && rm -rf /var/lib/apt/lists/*

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - &&     curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list &&     apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 10000

CMD ["gunicorn", "callback_listener.app:app", "--bind", "0.0.0.0:10000"]
```

---

## 🌐 Render Deployment

### render.yaml

```yaml
services:
  - type: web
    name: pesapal-callback-listener
    env: docker
    plan: free
    dockerfilePath: ./Dockerfile
    envVars:
      - key: DB_SERVER
        value: 7.tcp.eu.ngrok.io,15590
      - key: DB_NAME
        value: PesapalDB
      - key: DB_USERNAME
        value: sa
      - key: DB_PASSWORD
        value: michaelakoko2025
      - key: PORT
        value: 10000
```

> ✅ Don't commit your `.env` or `render.yaml` file with credentials — add them to `.gitignore`.

---

## 🗄️ SQL Server Setup

1. Create the database and table:

```sql
CREATE DATABASE PesapalDB;
GO

USE PesapalDB;
GO

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

2. Enable mixed authentication and SA login.

---

## 💻 API Endpoint

### `POST /pesapal-callback`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**

```json
{
  "id": 10463,
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+254712345678",
  "amount": 1.0,
  "payment_option": "Visa",
  "transaction_date": "2022-02-04T14:19:05.0210431Z",
  "currency": "KES",
  "merchant_reference": "TEST",
  "confirmation_code": "abc123"
}
```

**Response:**

```json
{
  "status": "200",
  "message": "Ok"
}
```

---

## 🐞 Debugging & Logs

- Local logs stored at: `logs/pesapal.log`
- Render logs visible in the Render dashboard

---

## 🧪 Testing Locally

```bash
curl -X POST http://localhost:10000/pesapal-callback   -H "Content-Type: application/json"   -d '{...}'   # Replace with actual JSON
```

---

## 🔐 Security Best Practices

- Use `.env` for sensitive credentials
- Don't expose SQL ports publicly
- For production, use valid SSL certs
- Rate-limit and IP-whitelist Pesapal servers

---

## 📩 Support

- Email me here --> **akokomichael37@gmail.com**