from typing import Optional
from src.utils.logger import setup_logger
import os
import smtplib
from email.message import EmailMessage


class EmailService:
    def __init__(self):
        self.logger = setup_logger()
        self.env = os.getenv("ENV", "DEV")

        # Auto-disable email sending in DEV unless explicitly enabled
        default_send = "0" if self.env == "DEV" else "1"
        self.send_email = os.getenv("SEND_EMAILS", default_send) == "1"
        if not self.send_email:
            self.logger.warning("Email sending turned off")

        # Load environment-specific SMTP settings
        env_prefix = f"{self.env}_" if self.env in ["DEV", "PROD"] else ""

        smtp_username = os.getenv(f"{env_prefix}SMTP_USERNAME") or os.getenv(
            "SMTP_USERNAME"
        )
        if not smtp_username:
            raise ValueError(
                f"{env_prefix}SMTP_USERNAME environment variable is not set"
            )
        self.smtp_username: str = smtp_username

        smtp_password = os.getenv(f"{env_prefix}SMTP_PASSWORD") or os.getenv(
            "SMTP_PASSWORD"
        )
        if not smtp_password:
            raise ValueError(
                f"{env_prefix}SMTP_PASSWORD environment variable is not set"
            )
        self.smtp_password: str = smtp_password

        smtp_server = os.getenv(f"{env_prefix}SMTP_SERVER") or os.getenv("SMTP_SERVER")
        if not smtp_server:
            raise ValueError(f"{env_prefix}SMTP_SERVER environment variable is not set")
        self.smtp_server: str = smtp_server

        smtp_port_str = os.getenv(f"{env_prefix}SMTP_PORT") or os.getenv("SMTP_PORT")
        if not smtp_port_str:
            raise ValueError(f"{env_prefix}SMTP_PORT environment variable is not set")
        self.smtp_port = int(smtp_port_str)

        self.smtp_from = os.getenv(f"{env_prefix}SMTP_FROM_EMAIL") or os.getenv(
            "SMTP_FROM_EMAIL"
        )
        if not self.smtp_from:
            raise ValueError(
                f"{env_prefix}SMTP_FROM_EMAIL environment variable is not set"
            )

        self.smtp_timeout = int(
            os.getenv("SMTP_TIMEOUT", "15")
        )  # Default 15 seconds if not set

        self.logger.info("Initialized EmailService")

    def send_charge_report(self, filename: str, from_date: str, to_date: str):
        if self.send_email:
            recipients = os.getenv("INVOICING_RECIPIENTS")
            if not recipients:
                raise ValueError("INVOICING_RECIPIENTS environment variable is not set")

            recipients = recipients.split(",")
            subject = f"BRF Signalen 1 - Laddningsrapport {from_date} - {to_date}"
            body = (
                f"Här kommer debiteringsunderlag för el förbrukad i laddstolpar för "
                f"BRF Signalen 1. Underlaget avser perioden {from_date} - {to_date}"
            )

            self._send_email(recipients, subject, body, filename, content_type="plain")
        else:
            self.logger.info("Email sending is disabled, skipping charge report email")

    def send_error(self, error_message: str):
        error_recipients = os.getenv("ERROR_RECIPIENTS")
        if not error_recipients:
            raise ValueError("ERROR_RECIPIENTS environment variable is not set")

        error_recipients = error_recipients.split(",")
        subject = "ERROR: Charge report generation failed"

        self._send_email(error_recipients, subject, error_message, content_type="plain")

    def send_summary_report(self, body: str, month: str):
        if self.send_email:
            summary_recipients = os.getenv("SUMMARY_RECIPIENTS")
            if not summary_recipients:
                raise ValueError("SUMMARY_RECIPIENTS environment variable is not set")

            summary_recipients = summary_recipients.split(",")
            subject = f"BRF Signalen 1 - Laddningsstatistik för {month}"

            self._send_email(summary_recipients, subject, body, content_type="html")
        else:
            self.logger.info("Email sending is disabled, skipping summary report email")

    def _send_email(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        content_type: str = "plain",
    ):
        """
        Internal method to send emails with configurable content type
        and optional attachments.

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
            # construct email
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(recipients)
            msg.set_content(body, subtype=content_type)

            if attachment_path:
                with open(attachment_path, "rb") as fp:
                    msg.add_attachment(
                        fp.read(),
                        maintype="text",
                        subtype="csv",
                        filename=attachment_path,
                    )

            with smtplib.SMTP(
                host=self.smtp_server, port=self.smtp_port, timeout=self.smtp_timeout
            ) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            self.logger.info(
                f"Email with subject: {subject} sent successfully to {', '.join(recipients)}"
            )

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
