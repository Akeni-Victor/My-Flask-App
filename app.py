import os
import mysql.connector
from flask import Flask, jsonify, request
from flask import Flask, jsonify
import smtplib
import traceback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from email.mime.text import MIMEText
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')


# Rest of the code here

# MySQL configurations
db_config = {
    'host': 'localhost',
    'user': 'my_user',
    'password': 'my_password',
    'database': 'my_database'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Route to get all users
@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    results = cur.fetchall()
    cur.close()
    conn.close()

    users = []
    for row in results:
        users.append({
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[4].strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(users)

# Route to get a user by registration number
@app.route('/users/<int:reg_number>', methods=['GET'])
def get_user_by_reg_number(reg_number):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (reg_number,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        user = {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'created_at': result[4].strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404

# Welcome route
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Flask MySQL API!"

@app.route('/request-add-record', methods=['POST'])
def request_add_record():
    data = request.get_json()

    # Check for required fields
    if not data or 'regNumber' not in data or 'phoneNumber' not in data:
        return jsonify({'error': 'Missing required fields: regNumber and phoneNumber'}), 400

    reg_number = data['regNumber']
    phone_number = data['phoneNumber']

    # Prepare the email to request the addition of a new record
    message = Mail(
        from_email='victorakeni@flapmax.com',  # Replace with your SendGrid verified email
        to_emails='akenivictor16@gmail.com',  # Replace with the recipient's email
        subject='Request to Add New Record',
        html_content=f'<strong>A request to add a new record has been made for the following hospital registration number:</strong> {reg_number}<br><strong>Phone Number:</strong> {phone_number}'
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return jsonify({'success': 'Request to add record sent successfully!', 'status_code': response.status_code}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send request for new record', 'details': str(e)}), 500


# New endpoint to handle form submission and send email
@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        data = request.json

        # Extract details from the request
        username = data.get('username')
        email = data.get('email')
        phone_number = data.get('phoneNumber')

        if not username or not email or not phone_number:
            return jsonify({"message": "Missing required fields"}), 400

        # Create the email content
        message = Mail(
            from_email='victorakeni@flapmax.com',  # Replace with your verified SendGrid sender email
            to_emails='akenivictor@gmail.com',  # Replace with recipient's email
            subject='New Profile Update',
            plain_text_content=f"User: {username}\nEmail: {email}\nPhone: {phone_number}"
        )

        try:
            # Send the email using SendGrid API
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            # Log the response from SendGrid
            print(response.status_code)
            print(response.body)
            print(response.headers)
            
            return jsonify({"message": "Email sent successfully"}), 200
        except Exception as e:
            print(f"Error sending email: {e}")
            return jsonify({"message": "Error sending email"}), 500

    except Exception as e:
        print(f"Error processing the request: {e}")
        return jsonify({"message": "Server error occurred"}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
