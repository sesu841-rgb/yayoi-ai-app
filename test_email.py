import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    print(f"Connecting to {smtp_server}:{smtp_port} with user {smtp_user}...")
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            print("Login successful!")
    except Exception as e:
        print(f"SMTP error: {e}")

if __name__ == "__main__":
    test_smtp()
