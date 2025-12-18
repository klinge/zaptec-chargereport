import pytest
import os
from unittest.mock import patch, Mock
from src.services.email_service import EmailService


class TestEmailService:
    def test_init_dev_environment(self, mock_logger):
        """Test EmailService initialization in DEV environment"""
        with patch.dict(os.environ, {"ENV": "DEV"}):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()

                assert service.env == "DEV"
                assert service.send_email == False  # Auto-disabled in DEV

    def test_init_prod_environment(self, mock_logger):
        """Test EmailService initialization in PROD environment"""
        with patch.dict(os.environ, {"ENV": "PROD", "SEND_EMAILS": "1"}):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()

                assert service.env == "PROD"
                assert service.send_email

    def test_environment_specific_smtp_settings(self, mock_logger):
        """Test that environment-specific SMTP settings are loaded from .env"""
        # This test now relies on DEV_SMTP_* values from .env.test
        with patch.dict(os.environ, {"ENV": "DEV"}):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()

                assert service.smtp_server == "dev.smtp.com"
                assert service.smtp_port == 587
                assert service.smtp_username == "dev_user"
                assert service.smtp_password == "dev_pass"
                assert service.smtp_from == "dev@test.com"

    def test_fallback_to_generic_smtp_settings(self, mock_logger):
        """Test fallback to generic SMTP settings when env-specific not available"""
        # Only set generic SMTP vars, no DEV_SMTP_* so it falls back
        test_env = {
            "ENV": "DEV",
            "SMTP_SERVER": "generic.smtp.com",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "generic_user",
            "SMTP_PASSWORD": "generic_pass",
            "SMTP_FROM_EMAIL": "generic@test.com",
        }

        # Use clear=True to start fresh and only include what we explicitly want
        with patch.dict(os.environ, test_env, clear=True):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()

                assert service.smtp_server == "generic.smtp.com"
                assert service.smtp_port == 465

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_email_disabled(self, mock_smtp, mock_logger):
        """Test that emails are not sent when disabled"""
        with patch.dict(os.environ, {"ENV": "DEV", "SEND_EMAILS": "0"}):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                service.send_charge_report("test.csv", "2024-01-01", "2024-01-31")

                mock_smtp.assert_not_called()

    def test_constructor_missing_env_vars(self, mock_logger):
        """Test constructor fails with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                with pytest.raises(ValueError, match="SMTP_USERNAME"):
                    EmailService()

    def test_constructor_smtp_timeout_default(self, mock_logger):
        """Test constructor uses default SMTP timeout"""
        test_env = {
            "ENV": "DEV",
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test",
            "SMTP_PASSWORD": "test",
            "SMTP_FROM_EMAIL": "test@test.com",
        }

        with patch.dict(os.environ, test_env):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                assert service.smtp_timeout == 15

    @patch("src.services.email_service.smtplib.SMTP")
    @patch("builtins.open", create=True)
    def test_send_charge_report_success(self, mock_open, mock_smtp, mock_logger):
        """Test successful charge report sending"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_file = Mock()
        mock_file.read.return_value = b"csv,data"
        mock_open.return_value.__enter__.return_value = mock_file

        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "1",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
            "INVOICING_RECIPIENTS": "user1@test.com,user2@test.com",
        }

        with patch.dict(os.environ, test_env):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                service.send_charge_report(
                    "test_report.csv", "2024-01-01", "2024-01-31"
                )

                mock_smtp.assert_called_once_with(
                    host="smtp.test.com", port=587, timeout=15
                )
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with("test_user", "test_pass")
                mock_server.send_message.assert_called_once()

    def test_send_charge_report_missing_recipients(self, mock_logger):
        """Test charge report fails with missing recipients"""
        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "1",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                with pytest.raises(ValueError, match="INVOICING_RECIPIENTS"):
                    service.send_charge_report("test.csv", "2024-01-01", "2024-01-31")

    @patch("src.services.email_service.smtplib.SMTP")
    @patch("builtins.open", create=True)
    def test_send_email_with_attachment(self, mock_open, mock_smtp, mock_logger):
        """Test _send_email method with file attachment"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_file = Mock()
        mock_file.read.return_value = b"csv,data\ntest,123"
        mock_open.return_value.__enter__.return_value = mock_file

        test_env = {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
        }

        with patch.dict(os.environ, test_env):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                service._send_email(
                    recipients=["test@example.com"],
                    subject="Test Subject",
                    body="Test Body",
                    attachment_path="test.csv",
                )

                mock_open.assert_called_once_with("test.csv", "rb")
                mock_server.send_message.assert_called_once()

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_email_smtp_auth_error(self, mock_smtp, mock_logger):
        """Test _send_email handles SMTP authentication errors"""
        import smtplib

        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        test_env = {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "bad_user",
            "SMTP_PASSWORD": "bad_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
        }

        with patch.dict(os.environ, test_env):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                with pytest.raises(smtplib.SMTPAuthenticationError):
                    service._send_email(
                        recipients=["test@example.com"],
                        subject="Test Subject",
                        body="Test Body",
                    )

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_email_file_not_found(self, mock_smtp, mock_logger):
        """Test _send_email handles missing attachment files"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        test_env = {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
        }

        with patch.dict(os.environ, test_env):
            with patch(
                "src.services.email_service.setup_logger", return_value=mock_logger
            ):
                service = EmailService()
                with pytest.raises(FileNotFoundError):
                    service._send_email(
                        recipients=["test@example.com"],
                        subject="Test Subject",
                        body="Test Body",
                        attachment_path="nonexistent.csv",
                    )

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_error_success(self, mock_smtp, mock_logger):
        """send_error should send a plain email to ERROR_RECIPIENTS when enabled"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "1",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
            "ERROR_RECIPIENTS": "err1@test.com,err2@test.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with patch("src.services.email_service.setup_logger", return_value=mock_logger):
                service = EmailService()
                service.send_error("Something went wrong")

                mock_smtp.assert_called_once_with(host="smtp.test.com", port=587, timeout=15)
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with("test_user", "test_pass")
                # inspect sent EmailMessage
                assert mock_server.send_message.call_count == 1
                sent_msg = mock_server.send_message.call_args[0][0]
                assert "ERROR: Charge report generation failed" in sent_msg["Subject"]

    def test_send_error_missing_recipients_raises(self, mock_logger):
        """send_error should raise ValueError when ERROR_RECIPIENTS missing"""
        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "1",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with patch("src.services.email_service.setup_logger", return_value=mock_logger):
                service = EmailService()
                with pytest.raises(ValueError, match="ERROR_RECIPIENTS"):
                    service.send_error("boom")

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_summary_report_disabled(self, mock_smtp, mock_logger):
        """When sending is disabled, summary report should not attempt SMTP connection"""
        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "0",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
            "SUMMARY_RECIPIENTS": "sum@test.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with patch("src.services.email_service.setup_logger", return_value=mock_logger):
                service = EmailService()
                service.send_summary_report("<p>summary</p>", "January")

                mock_smtp.assert_not_called()

    @patch("src.services.email_service.smtplib.SMTP")
    def test_send_summary_report_success(self, mock_smtp, mock_logger):
        """send_summary_report should send an HTML email to SUMMARY_RECIPIENTS when enabled"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        test_env = {
            "ENV": "PROD",
            "SEND_EMAILS": "1",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_FROM_EMAIL": "from@test.com",
            "SUMMARY_RECIPIENTS": "sum1@test.com,sum2@test.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with patch("src.services.email_service.setup_logger", return_value=mock_logger):
                service = EmailService()
                service.send_summary_report("<b>HTML</b>", "February")

                mock_smtp.assert_called_once_with(host="smtp.test.com", port=587, timeout=15)
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with("test_user", "test_pass")
                assert mock_server.send_message.call_count == 1
                sent_msg = mock_server.send_message.call_args[0][0]
                # ensure HTML content type
                assert sent_msg.get_content_subtype() == "html"
