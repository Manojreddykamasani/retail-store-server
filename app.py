import os
from flask import Flask, request, jsonify, render_template
import pymysql.cursors
from dotenv import load_dotenv
from fuzzywuzzy import process
from difflib import SequenceMatcher
from flask_mail import Mail, Message
load_dotenv()

app = Flask(__name__)

# Database configuration
def connect_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),  # Aiven MySQL host
        user=os.getenv('DB_USER'),  # Aiven MySQL user
        password=os.getenv('DB_PASSWORD'),  # Aiven MySQL password
        database=os.getenv('DB_NAME'),  # Aiven MySQL database name
        port=int(os.getenv('DB_PORT', 3306)),  # MySQL port
        cursorclass=pymysql.cursors.DictCursor
    )

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Sender email address
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # App password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')  # Default sender email

mail = Mail(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'running', 'message': 'Application is healthy.'}), 200

# Other routes remain unchanged...
# Include all routes from the original script here, modified to use `os.getenv()` for sensitive data.

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

