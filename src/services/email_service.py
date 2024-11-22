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
        
        self.smtp_from = os.getenv('SMTP_FROM_EMAIL')
        if not self.smtp_username:
            raise ValueError("SMTP_USERNAME environment variable is not set")

        self.smtp_timeout = int(os.getenv('SMTP_TIMEOUT', '15'))  # Default 15 seconds if not set
        
        self.logger.info("Initialized EmailService")


    def send_charge_report(self, filename: str, from_date: str, to_date: str):
        recipients = os.getenv('INVOICING_RECIPIENTS')
        if not recipients:
            raise ValueError("INVOICING_RECIPIENTS environment variable is not set")
        
        recipients = recipients.split(',')
        subject = f'BRF Signalen 1 - Laddningsrapport {from_date} - {to_date}'
        body = f'Här kommer debiteringsunderlag för el förbrukad i laddstolpar för BRF Signalen 1. Underlaget avser perioden {from_date} - {to_date}'
       
        self._send_email(recipients, subject, body, filename, content_type='plain')

    def send_error(self, error_message: str):
        error_recipients = os.getenv('ERROR_RECIPIENTS')
        if not error_recipients:
            raise ValueError("ERROR_RECIPIENTS environment variable is not set")
        
        error_recipients = error_recipients.split(',')
        subject = 'ERROR: Charge report generation failed'
        
        self._send_email(error_recipients, subject, error_message, content_type='plain')

    def send_summary_report(self, body: str, month: str):
        summary_recipients = os.getenv('SUMMARY_RECIPIENTS')
        if not summary_recipients:
            raise ValueError("SUMMARY_RECIPIENTS environment variable is not set")
        subject = f"BRF Signalen 1 - Laddningsstatistik för {month}"

        self._send_email(summary_recipients, subject, body, content_type='html')

    def _send_email(self, recipients: list[str], subject: str, body: str, attachment_path: str = None, content_type: str = 'plain'):
        """
        Internal method to send emails with configurable content type and optional attachments.

        Args:
            recipients: List of email addresses to send to
            subject: Email subject line
            body: Email body content
            attachment_path: Optional path to file attachment (default: None)
            content_type: Type of email content - 'plain' or 'html' (default: 'plain')

        Raises:
            FileNotFoundError: If attachment file cannot be found
            smtplib.SMTPAuthenticationError: If SMTP authentication fails
            smtplib.SMTPException: If email sending fails
            Exception: For other unexpected errors

        Note:
            Uses SMTP configuration from environment variables
        """
        try: 
            with smtplib.SMTP(host=self.smtp_server, port=self.smtp_port, timeout=self.smtp_timeout) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
                msg = MIMEMultipart()
                msg['Subject'] = subject
                msg['From'] = self.smtp_from
                msg['To'] = ', '.join(recipients)
            
                msg.attach(MIMEText(body, content_type))
            
                if attachment_path:
                    with open(attachment_path, 'rb') as f:
                        attachment = MIMEApplication(f.read(), _subtype='csv')
                        attachment.add_header('Content-Disposition', 'attachment', filename=attachment_path)
                        msg.attach(attachment)
            
                server.send_message(msg)
            
            self.logger.info(f"Email with subject: {subject} sent successfully to {', '.join(recipients)}")
        
        except FileNotFoundError:
            self.logger.error(f"Report file not found: {attachment_path}")
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

        

