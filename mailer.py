import json
import smtplib
import os
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def get_attachments_today():
    attachments = []
    today_date = datetime.now().strftime("%Y-%m-%d")
    for f in os.listdir("./reports"):
        if f.endswith(".xlsx") and today_date in f:
            attachments.append(f"./reports/{f}")
    return attachments


class Mailer:
    def __init__(self):
        self.read_config()

    def read_config(self):
        with open("config.json", "r") as f:
            config = json.load(f)
            config_credentials = config["credentials"]
            self.smtp_ip = config_credentials["smtp_ip"]
            self.smtp_port = config_credentials["smtp_port"]
            self.mail = config_credentials["mail"]
            self.password = config_credentials["password"]

    def send_reports(self):
        msg = MIMEMultipart()
        msg["From"] = self.mail

        sent_to = ["adomasval04@gmail.com", "nerijus@herba.lt"]
        msg[
            "Subject"
        ] = f"Herba Humana savaitinė eshop kainų palyginimo ataskaita {datetime.now().strftime('%Y-%m')}"

        # Add email body
        body = "Šios savaitės ataskaitos. ESHOP kainų palyginimas. \n\n Ne visi produktai yra šiame spreadsheet'e!\n Ne visi produktai turi 100% teisingą informaciją!"
        msg.attach(MIMEText(body, "plain"))

        # Attach Excel files
        attachments = get_attachments_today()
        for f in attachments:
            with open(f, "rb") as attachment:
                file_name = os.path.basename(f)
                part = MIMEApplication(attachment.read(), Name=file_name)
                part["Content-Disposition"] = f"attachment; filename={file_name}"
                msg.attach(part)

        with smtplib.SMTP_SSL(self.smtp_ip, self.smtp_port) as server:
            server.login(self.mail, self.password)
            for to in sent_to:
                msg["To"] = to
                server.send_message(msg)

        print("Email sent successfully.")
