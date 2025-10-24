Private SMS Gateway : 
- A private SMS gateway web application and REST API that enables users and external applications to send and receive SMS messages securely and privately through a GSM modem connected to a telecom network.

Features : 
- User Authentication System — supports admin and regular user accounts
- Inbox — view and manage received SMS messages
- Dashboard — send SMS messages directly via web interface
- Admin Panel — manage users and API access
- Create and delete user accounts
- Generate and revoke API keys
- REST API — send SMS from external applications
- GSM Modem Integration — powered by PySerial
- Responsive UI — built with Bootstrap 5

Requirements :
- Python ≥ 3.9
- MySQL Server
- GSM Modem with serial port access
- Required Python Packages : pip install flask mysql-connector-python pyserial werkzeug
 
API Usage : 
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
    
Notes :
Ensure the GSM modem is properly connected and accessible via serial port.
Admin users can manage accounts and API keys through the dashboard.
The API key must be included in every request for authentication.

Technologies Used :
Frontend : HTML, CSS (Bootstrap 5)
Backend : Python (Flask) 
Database : MySQL
Operating System : Linux (CentOS 9)
Application Server : Gunicorn 
Web Server : Nginx 
