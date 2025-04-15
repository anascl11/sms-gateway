from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import modem
from datetime import datetime
import time
import secrets
import hashlib

# create flask app
app = Flask(__name__)

# app secret key for session management
app.secret_key = secrets.token_hex(32)

# database connection
conn = mysql.connector.connect(
    host = "192.168.10.6",
    user = "atrait",
    password = "atrait11!!",
    database = "sms_gateway"
)
cursor = conn.cursor(dictionary=True)

# redirect from root to login page
@app.route("/")
def index():
    return redirect(url_for("login"))

# login system
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
    
        flash('Invalid credentials', 'danger')
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if request.method == 'POST':
        receiver = request.form['receiver']
        message = request.form['message']
        user_id = session['user_id']
        cursor.execute("INSERT INTO outgoing_messages (receiver, message, sent_at, user_id, api_client_id) VALUES (%s, %s, %s, %s, NULL)", (receiver, message, datetime.now(), user_id))
        conn.commit()
        modem.send_sms(receiver, message)
        flash('SMS sent successfully!', 'success')
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM outgoing_messages WHERE user_id = %s ORDER BY sent_at DESC", (session['user_id'],))
    sent_sms = cursor.fetchall()
    return render_template('dashboard.html', sent_sms=sent_sms)
    
# inbox
@app.route("/inbox")
def inbox():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    cursor.execute("SELECT * FROM incoming_messages ORDER BY received_at DESC")
    messages = cursor.fetchall()
    return render_template("inbox.html", messages=messages)

# check new messages
@app.route("/check_messages", methods=["POST"])
def check_messages():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    messages = modem.read_all_sms()
    count = 0
    for msg in messages:
        raw_ts = msg['timestamp']  # e.g., '25/04/11,10:15:25+00'
        # Parse modem timestamp to MySQL-compatible format
        ts_obj = datetime.strptime(raw_ts.split('+')[0], "%y/%m/%d,%H:%M:%S")
        mysql_ts = ts_obj.strftime("%Y-%m-%d %H:%M:%S")
        
        # Check for duplicate and Use converted timestamp in both SELECT and INSERT
        cursor.execute("SELECT * FROM incoming_messages WHERE sender = %s AND message = %s AND received_at = %s", 
                      (msg['sender'], msg['content'], mysql_ts))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO incoming_messages (sender, message, received_at) VALUES (%s, %s, %s)", 
                         (msg['sender'], msg['content'], mysql_ts))
            count += 1
    conn.commit()
    
    flash(f'{count} new messages received', 'info')
    return redirect(url_for('inbox'))

# admin panel
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    if not user or not user['is_admin']:
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    api_client_name = None   # variable to show api clint name
    plain_api_key = None     # variable to show un-hashed key after creation
    if request.method == 'POST':
        if 'new_user' in request.form:
            username = request.form['username']
            password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",(username, password, False))
            conn.commit()
            flash('User created successfully.', 'success')
        elif 'delete_user' in request.form:
            user_id = request.form['delete_user']
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            flash('User deleted.', 'info')
        elif 'new_api' in request.form:
            name = request.form['name']
            api_client_name = name
            plain_api_key = secrets.token_hex(32)
            api_key_hashed = hashlib.sha256(plain_api_key.encode()).hexdigest()
            cursor.execute("INSERT INTO api_clients (name, api_key) VALUES (%s, %s)", (name, api_key_hashed))
            conn.commit()
            flash('API Client created. Save this API key securely.', 'success')
        elif 'delete_api' in request.form:
            api_id = request.form['delete_api']
            cursor.execute("DELETE FROM api_clients WHERE id = %s", (api_id,))
            conn.commit()
            flash('API Client deleted.', 'info')
    # Get users and APIs
    cursor.execute("SELECT id, username, is_admin FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT id, name FROM api_clients")
    apis = cursor.fetchall()
    return render_template("admin.html", users=users, apis=apis, api_client_name=api_client_name, new_api_key=plain_api_key)

# api endpoints
@app.route('/api/send_sms', methods=['POST'])
def api_send_sms():
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 400

    # Hash the incoming API key for comparison
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

    # Find the client by hashed key
    cursor.execute("SELECT id FROM api_clients WHERE api_key = %s", (hashed_key,))
    client = cursor.fetchone()
    if not client:
        return jsonify({'error': 'Invalid API key'}), 403

    data = request.get_json()
    receiver = data.get('receiver')
    message = data.get('message')

    if not receiver or not message:
        return jsonify({'error': 'Missing receiver or message'}), 400

    # Store message (assumes separate modem handler handles actual send)
    cursor.execute("INSERT INTO outgoing_messages (receiver, message, sent_at, user_id, api_client_id) VALUES (%s, %s, %s, NULL, %s)", (receiver, message, datetime.now(), client['id']))
    conn.commit()
    modem.send_sms(receiver, message)
    return jsonify({'status': 'SMS sent successfully!'}), 200

@app.route('/api/read_sms', methods=['GET'])
def api_sent_sms():
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 400

    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    cursor.execute("SELECT id FROM api_clients WHERE api_key = %s", (hashed_key,))
    client = cursor.fetchone()
    if not client:
        return jsonify({'error': 'Invalid API key'}), 403

    cursor.execute("SELECT receiver, message, sent_at FROM outgoing_messages WHERE api_client_id = %s ORDER BY sent_at DESC", (client['id'],))
    messages = cursor.fetchall()

    return jsonify(messages), 200

# run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
