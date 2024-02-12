from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from wakeonlan import send_magic_packet
import configparser
import requests
import os
import time
import paho.mqtt.client as mqtt
import ssl


app = Flask(__name__)
app.secret_key = 'hakgiabn1nmfi'  # Consider moving this to config.ini as well
app.config['SESSION_TYPE'] = 'filesystem'


# Load configurations
config = configparser.ConfigParser()
config.read('config.ini')


# MQTT Setup
mqtt_config = config['MQTT']
# MQTT Setup with a specific client ID
client_id = "WakeMyDevice_" + os.urandom(3).hex()  # Generates a somewhat unique client ID
client = mqtt.Client(client_id)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connected successfully to MQTT broker")
    else:
        print("Failed to connect, return code %d\n", rc)
    # Subscribe to the topic on successful connect
    client.subscribe(mqtt_config['topic'])

def on_message(client, userdata, msg):
    print(f"Message received-> {msg.topic} {str(msg.payload)}")
    # Assuming the message payload is a MAC address
    mac_address = str(msg.payload.decode())
    try:
        send_magic_packet(mac_address)
        print(f"Wake-up signal sent successfully to {mac_address}")
    except Exception as e:
        print(f"Error sending wake-up signal: {e}")

client.on_connect = on_connect
client.on_message = on_message

def start_mqtt_client():
    client.username_pw_set(mqtt_config['username'], mqtt_config['password'])
    client.connect(mqtt_config['server'], int(mqtt_config['port']), 60)
    client.loop_start()


# FLASK ROUTES
# Basic auth
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Authentication against config values
        if username == config['Auth']['username'] and password == config['Auth']['password']:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return 'Login Failed'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@auth_required
def index():
    devices = config['Devices']
    return render_template('index.html', devices=devices)

@app.route('/wake/<mac>')
@auth_required
def wake(mac):
    try:
        send_magic_packet(mac)
        flash('Wake-up signal sent successfully!', 'success')
    except ValueError as e:
        flash(f'Error sending wake-up signal: {e}', 'danger')
    return redirect(url_for('index'))

def send_pushover_notification(message):
    user_key = config['Pushover']['user_key']
    api_token = config['Pushover']['api_token']
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": api_token,
        "user": user_key,
        "message": message
    })


if __name__ == '__main__':

    # check the file is here
    while not os.path.exists('tunnelled_urls.txt'):
        time.sleep(1)

    # Read the URLs from your text file and send them
    with open('tunnelled_urls.txt', 'r') as file:
        urls = file.read()

    print("URLS", urls)
    try:
        urls = urls.split('\n')
        urls = [url.split(' ')[0] for url in urls]
        urls = [url for url in urls if url.startswith('https')]
        url = urls[0]
    except:
        url = ''
    
    # if url is empty then send an error message
    if url == '':
        message = "No tunneled URLs found"
    else:
        message = f"New tunneled URL found: {url}"

    send_pushover_notification(message)
    print(message)


    # Initialize and start the MQTT client
    mqtt_config = config['MQTT']
    client.username_pw_set(mqtt_config['username'], mqtt_config['password'])

    # Set TLS/SSL parameters for the connection
    client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                   tls_version=ssl.PROTOCOL_TLS, ciphers=None)
    client.tls_insecure_set(False)  # Set to True only if the server uses a self-signed certificate

    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(mqtt_config['server'], int(mqtt_config['port']), 60)
        client.loop_start()
        print(f"Attempting to connect to MQTT broker at {mqtt_config['server']} on port {mqtt_config['port']}")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

    app.run(host='0.0.0.0', port=5005, debug=False)