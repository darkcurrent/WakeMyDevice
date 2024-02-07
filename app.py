from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from wakeonlan import send_magic_packet
import configparser
import requests
import os
import time


app = Flask(__name__)
app.secret_key = 'hakgiabn1nmfi'  # Consider moving this to config.ini as well

# Load configurations
config = configparser.ConfigParser()
config.read('config.ini')

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
    app.run(host='0.0.0.0', port=5005, debug=False)