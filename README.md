+ Flask SMS Gateway
 
A web-based SMS Gateway built with Flask, MySQL, and PySerial, allowing users to send and receive SMS messages via a connected GSM modem. It also provides a secure API interface for external systems to send SMS

---
 + Features
  
- User login system (admin & normal users)
- Inbox for received messages
- Dashboard to send SMS
- Admin panel to:
  - Manage users
  - Generate & revoke API keys
-  API for external systems to send SMS
-  GSM modem integration using PySerial
-  Bootstrap 5-based responsive UI

---
+ Requirements

- Python 3.9+
- MySQL Server
- GSM modem (with serial port access)
- Required Python packages : flask mysql-connector-python pyserial werkzeug

---
+ API Usage

- Endpoint : POST /api/send_sms
  - Headers :
    * Content-Type: application/json
    * X-API-KEY: your_api_key
  - Body :
    {
       "receiver": "+2126xxxxxxxx",
        "message": "Hello from the API"
    }
- Endpoint : POST /api/read_sms
  - Headers : 
    * Content-Type: application/json
    * X-API-KEY: your_api_key
