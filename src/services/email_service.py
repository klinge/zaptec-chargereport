from src.utils.logger import setup_logger
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

class EmailService:
    def __init__(self):
        self.logger = setup_logger()
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        self.recipients = os.getenv('REPORT_RECIPIENTS').split(',')
        self.logger.info("Initialized EmailService")

    def send_report(self, filename: str, from_date: str, to_date: str):
        msg = MIMEMultipart()
        msg['Subject'] = f'Laddningsrapport {from_date} - {to_date}'
        msg['From'] = self.smtp_username
        msg['To'] = ', '.join(self.recipients)
        
        body = f'Här kommer laddningsrapporten för perioden {from_date} - {to_date}'
        msg.attach(MIMEText(body, 'plain'))
        
        with open(filename, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='csv')
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
        
        with smtplib.SMTP(host=self.smtp_server, 
                          port=self.smtp_port, 
                          timeout=15) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    def send_error(self, error_message: str):
        msg = MIMEMultipart()
        msg['Subject'] = 'ERROR: Laddningsrapport generation failed'
        msg['From'] = self.smtp_username
        msg['To'] = ', '.join(self.recipients)
        
        msg.attach(MIMEText(error_message, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
