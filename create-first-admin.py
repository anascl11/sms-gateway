from werkzeug.security import generate_password_hash
import mysql.connector

# connect to DB
conn = mysql.connector.connect(
    host = "192.168.10.6",
    user = "atrait",
    password = "atrait11!!",
    database = "sms_gateway"
)
cursor = conn.cursor()

# create admin
username = 'admin'
password = generate_password_hash('admin', method='pbkdf2:sha256')

cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)", (username, password, True))
conn.commit()

print("Admin user created.")
