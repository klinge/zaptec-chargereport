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
        if not self.smtp_username:
            raise ValueError("SMTP_USERNAME environment variable is not set")
        
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        if not self.smtp_password:
            raise ValueError("SMTP_PASSWORD environment variable is not set")
        
        self.smtp_server = os.getenv('SMTP_SERVER')
        if not self.smtp_server:
            raise ValueError("SMTP_SERVER environment variable is not set")
        
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        if not self.smtp_port:
            raise ValueError("SMTP_PORT environment variable is not set")
        
        recipients = os.getenv('REPORT_RECIPIENTS')
        if not recipients:
            raise ValueError("REPORT_RECIPIENTS environment variable is not set")
        self.recipients = recipients.split(',')

        self.smtp_timeout = int(os.getenv('SMTP_TIMEOUT', '15'))  # Default 15 seconds if not set
        
        self.logger.info("Initialized EmailService")

    def send_report(self, filename: str, from_date: str, to_date: str):
        try:
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
                            timeout=self.smtp_timeout) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {', '.join(self.recipients)}")
        
        except FileNotFoundError:
            self.logger.error(f"Report file not found: {filename}")
            raise
        except smtplib.SMTPAuthenticationError:
            self.logger.error("SMTP authentication failed")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error sending report: {str(e)}")
            raise


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
