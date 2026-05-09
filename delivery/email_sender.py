# delivery/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

def send_audit_email(to_email: str, username: str, report_text: str, pdf_path: str = None):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_ADDRESS")
    msg["To"] = to_email
    msg["Subject"] = f"Instagram Audit Report — @{username}"
    
    msg.attach(MIMEText(report_text, "html"))
    
    if pdf_path:
        with open(pdf_path, "rb") as f:
            pdf = MIMEApplication(f.read(), _subtype="pdf")
            pdf.add_header("Content-Disposition", "attachment", filename=f"audit_{username}.pdf")
            msg.attach(pdf)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_APP_PASSWORD"))
        server.send_message(msg)
