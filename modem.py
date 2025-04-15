import serial
import time
import re

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
time.sleep(1)

# Send SMS
def send_sms(number, message):
    ser.write(f'AT+CMGS="{number}"\r'.encode())
    time.sleep(1)
    ser.write(message.encode())
    time.sleep(0.5)
    ser.write(b'\x1A')
    time.sleep(3)

# Read All SMS with proper formatting
def read_all_sms():
    ser.write(b'AT+CMGL="ALL"\r')
    time.sleep(2)
    response = ser.read_all().decode(errors='ignore')

    lines = response.splitlines()
    messages = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("+CMGL:") and i + 1 < len(lines):
            # Extract metadata from the header
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
    # Each SMS is stored as a dictionary with these keys index, status, sender, timestamp, content
    # All SMS'S are collected in the messages list
