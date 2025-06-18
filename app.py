from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
# Load .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client["authdb"]
users_collection = db["users"]

# Email config
SENDER_EMAIL = 'suresh752005@gmail.com'
APP_PASSWORD = 'syjxfbszltvecccs'

# Send OTP function
def send_otp_email(to_email, otp):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your OTP Code"
    message["From"] = SENDER_EMAIL
    message["To"] = to_email

    text = f"Your OTP is: {otp}"
    message.attach(MIMEText(text, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, message.as_string())

# Home route
@app.route('/')
def home():
    return redirect('/login')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if users_collection.find_one({'username': username}):
            return render_template('register.html', error="Username already exists")

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': password,
            'otp': None
        })
        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username})

        if user and user['password'] == password:
            otp = str(random.randint(100000, 999999))
            users_collection.update_one({'username': username}, {'$set': {'otp': otp}})
            send_otp_email(user['email'], otp)
            session['username'] = username
            return redirect('/verify-otp')
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# Verify OTP
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        entered_otp = request.form['otp']
        user = users_collection.find_one({'username': session['username']})

        if user and user['otp'] == entered_otp:
            users_collection.update_one({'username': session['username']}, {'$set': {'otp': None}})
            return render_template('dashboard.html', username=session['username'])
        else:
            return render_template('verify_otp.html', error="Invalid OTP")

    return render_template('verify_otp.html')
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect('/login')

@app.route('/home')
def home_page():
    return render_template('home.html', username=session.get('username'))

@app.route('/about')
def about_page():
    return render_template('about.html', username=session.get('username'))

@app.route('/contact')
def contact_page():
    return render_template('contact.html', username=session.get('username'))


# Resend OTP
@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({'username': username})

        if user:
            otp = str(random.randint(100000, 999999))
            users_collection.update_one({'username': username}, {'$set': {'otp': otp}})
            send_otp_email(user['email'], otp)
            return redirect('/verify-otp')

    return redirect('/login')

# Logout (optional)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Run app
if __name__ == '__main__':
    app.run(debug=True)
