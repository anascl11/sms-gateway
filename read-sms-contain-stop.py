import serial
import time
import re
import mysql.connector
from datetime import datetime
import binascii
import logging

# Configuration
device_id = 11
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'atrait11!!',
    'database': 'GSM_AT',
    'charset': 'utf8mb4'
}
serial_port = '/dev/ttyUSB0'
baudrate = 115200

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Change timestamp format to match the database format
def parse_timestamp(ts_str):
    match = re.match(r'(\d{2}/\d{2}/\d{2}),(\d{2}:\d{2}:\d{2})', ts_str)
    if match:
        dt_str = f"{match.group(1)} {match.group(2)}"
        return datetime.strptime(dt_str, "%y/%m/%d %H:%M:%S")
    return None

# Encode SMS content to UCS2 format (Unicode)
def encode_sms_ucs2(text):
    utf16 = text.encode("utf-16be")
    byte_count = len(utf16)
    hex_encoded = binascii.hexlify(utf16).decode().upper()
    return f"{byte_count:02X}{hex_encoded}"

# Read all SMS messages from the modem
def read_all_sms():
    ser.write(b'AT+CMGF=1\r') 
    time.sleep(1)
    ser.write(b'AT+CMGL="ALL"\r')
    time.sleep(2)
    response = ser.read_all().decode(errors='ignore')
    lines = response.splitlines()
    messages = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("+CMGL:") and i + 1 < len(lines):
            match = re.match(r'\+CMGL: (\d+),"(.*?)","(.*?)",,"(.*?)"', line)
            if match:
                messages.append({
                    'index': match.group(1),
                    'status': match.group(2),
                    'sender': match.group(3),
                    'timestamp': match.group(4),
                    'content': lines[i + 1].strip()
                })
            i += 2
        else:
            i += 1
    return messages

# Use with statements for serial and db
with serial.Serial(serial_port, baudrate, timeout=2) as ser, \
     mysql.connector.connect(**db_config) as conn:
    time.sleep(1)
    ser.write(b'ATZ\r')  # Reset the modem
    time.sleep(1)
    cursor = conn.cursor()

    logging.info("SMS Import script started.")

    # Main loop to read SMS and insert into the database
    while True:
        sms_list = read_all_sms()
        for sms in sms_list:
            content = sms['content'].strip()
            sender = sms['sender'].strip()
            timestamp_str = sms['timestamp'].strip()
            
            # Log the SMS content
            logging.info(f"Processing SMS - Sender: {sender} | Timestamp: {timestamp_str} | Content: {content}")
            
            if 'stop' in content.lower():
                sms_time = parse_timestamp(timestamp_str)
                if not sms_time:
                    logging.warning(f"Skipping SMS from {sender} due to invalid timestamp.")
                    continue
                
                check_query = "SELECT COUNT(*) FROM GSM_InSMS WHERE SenderNumber = %s AND HDentree = %s"
                cursor.execute(check_query, (sender, sms_time))
                exists = cursor.fetchone()[0]
                
                if exists == 0:
                    encoded = encode_sms_ucs2(content)
                    insert_query = """
                        INSERT INTO GSM_InSMS (
                            ID_Active_Device, SenderNumber, ContentEncoded, ContentDecoded,
                            CodingType, ClassType, Stat, HDentree, SMSCNumber,
                            LastUpdateRow, MultiPart, NbParts
                        ) VALUES (%s, %s, %s, %s, %s, 'NORMAL', 1, %s, 'PAS ENCORE DEFINI', NOW(), 'FALSE', 1)
                    """
                    values = (
                        device_id, sender, encoded, content, 'UNICODE', sms_time
                    )
                    cursor.execute(insert_query, values)
                    conn.commit()
                    ser.write(f'AT+CMGD={sms["index"]}\r'.encode())
                    time.sleep(0.5)
                    
                    logging.info(f"Inserted SMS from {sender} into the database.")
                else:
                    logging.info(f"Skipping duplicate SMS from {sender} (already in database).")
                    ser.write(f'AT+CMGD={sms["index"]}\r'.encode())
                    time.sleep(0.5)
            else:
                logging.info(f"Skipping SMS from {sender} as it does not contain 'stop'.")
                ser.write(f'AT+CMGD={sms["index"]}\r'.encode())
                time.sleep(0.5)
        
        time.sleep(10)  # Wait for 10 seconds before checking again
        logging.info("Waiting for the next check...")
