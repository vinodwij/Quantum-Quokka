import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# Load email credentials from secrets.toml
EMAIL_ADDRESS = st.secrets["email"]["address"]
EMAIL_PASSWORD = st.secrets["email"]["password"]

# Original email-sending function
def send_project_email():
    # Email details
    to_emails = ["deneize.perera@digitalt.hayleys.com"]
    subject = "Digital Transformation Project Agent"
    body = "Dear Sir, Hi"

    # Build the email
    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_emails, message.as_string())
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

# New function for sending registration email
def send_registration_email(user_email, password):
    # Email details
    to_emails = [user_email]
    subject = "Welcome to The Digital Transformation Project Agent"
    body = f"""
Dear User,

Welcome to the Digital Transformation Project Agent platform!

Your login credentials are as follows:
Email: {user_email}
Password: {password}

Please use these credentials to log in to the platform.

Best regards,
Digital Transformation Team
"""

    # Build the email
    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_emails, message.as_string())
        print(f"✅ Registration email sent successfully to {user_email}!")
    except Exception as e:
        print(f"❌ Error sending registration email to {user_email}: {e}")