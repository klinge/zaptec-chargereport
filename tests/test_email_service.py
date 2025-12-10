import pytest
import os
from unittest.mock import patch, Mock
from src.services.email_service import EmailService

class TestEmailService:
    def test_init_dev_environment(self, mock_logger):
        """Test EmailService initialization in DEV environment"""
        with patch.dict(os.environ, {'ENV': 'DEV'}):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                
                assert service.env == 'DEV'
                assert service.send_email == False  # Auto-disabled in DEV

    def test_init_prod_environment(self, mock_logger):
        """Test EmailService initialization in PROD environment"""
        with patch.dict(os.environ, {'ENV': 'PROD', 'SEND_EMAILS': '1'}):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                
                assert service.env == 'PROD'
                assert service.send_email == True

    def test_environment_specific_smtp_settings(self, mock_logger):
        """Test that environment-specific SMTP settings are loaded"""
        test_env = {
            'ENV': 'DEV',
            'DEV_SMTP_SERVER': 'dev.smtp.com',
            'DEV_SMTP_PORT': '587',
            'DEV_SMTP_USERNAME': 'dev_user',
            'DEV_SMTP_PASSWORD': 'dev_pass',
            'DEV_SMTP_FROM_EMAIL': 'dev@test.com',
            'SMTP_TIMEOUT': '15'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                
                assert service.smtp_server == 'dev.smtp.com'
                assert service.smtp_port == 587
                assert service.smtp_username == 'dev_user'
                assert service.smtp_password == 'dev_pass'
                assert service.smtp_from == 'dev@test.com'

    def test_fallback_to_generic_smtp_settings(self, mock_logger):
        """Test fallback to generic SMTP settings when env-specific not available"""
        test_env = {
            'ENV': 'DEV',
            'SMTP_SERVER': 'generic.smtp.com',
            'SMTP_PORT': '465',
            'SMTP_USERNAME': 'generic_user',
            'SMTP_PASSWORD': 'generic_pass',
            'SMTP_FROM_EMAIL': 'generic@test.com',
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                
                assert service.smtp_server == 'generic.smtp.com'
                assert service.smtp_port == 465

    @patch('src.services.email_service.smtplib.SMTP')
    def test_send_email_disabled(self, mock_smtp, mock_logger):
        """Test that emails are not sent when disabled"""
        with patch.dict(os.environ, {'ENV': 'DEV', 'SEND_EMAILS': '0'}):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                service.send_charge_report('test.csv', '2024-01-01', '2024-01-31')
                
                mock_smtp.assert_not_called()

    def test_constructor_missing_env_vars(self, mock_logger):
        """Test constructor fails with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                with pytest.raises(ValueError, match="SMTP_USERNAME"):
                    EmailService()

    def test_constructor_smtp_timeout_default(self, mock_logger):
        """Test constructor uses default SMTP timeout"""
        test_env = {
            'ENV': 'DEV',
            'SMTP_SERVER': 'test.smtp.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test',
            'SMTP_PASSWORD': 'test',
            'SMTP_FROM_EMAIL': 'test@test.com'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                assert service.smtp_timeout == 15

    @patch('src.services.email_service.smtplib.SMTP')
    @patch('builtins.open', create=True)
    def test_send_charge_report_success(self, mock_open, mock_smtp, mock_logger):
        """Test successful charge report sending"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_file = Mock()
        mock_file.read.return_value = b'csv,data'
        mock_open.return_value.__enter__.return_value = mock_file
        
        test_env = {
            'ENV': 'PROD',
            'SEND_EMAILS': '1',
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_pass',
            'SMTP_FROM_EMAIL': 'from@test.com',
            'INVOICING_RECIPIENTS': 'user1@test.com,user2@test.com'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                service.send_charge_report('test_report.csv', '2024-01-01', '2024-01-31')
                
                mock_smtp.assert_called_once_with(
                    host='smtp.test.com', port=587, timeout=15
                )
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with('test_user', 'test_pass')
                mock_server.send_message.assert_called_once()

    def test_send_charge_report_missing_recipients(self, mock_logger):
        """Test charge report fails with missing recipients"""
        test_env = {
            'ENV': 'PROD',
            'SEND_EMAILS': '1',
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_pass',
            'SMTP_FROM_EMAIL': 'from@test.com'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                with pytest.raises(ValueError, match="INVOICING_RECIPIENTS"):
                    service.send_charge_report('test.csv', '2024-01-01', '2024-01-31')

    @patch('src.services.email_service.smtplib.SMTP')
    @patch('builtins.open', create=True)
    def test_send_email_with_attachment(self, mock_open, mock_smtp, mock_logger):
        """Test _send_email method with file attachment"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_file = Mock()
        mock_file.read.return_value = b'csv,data\ntest,123'
        mock_open.return_value.__enter__.return_value = mock_file
        
        test_env = {
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_pass',
            'SMTP_FROM_EMAIL': 'from@test.com'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                service._send_email(
                    recipients=['test@example.com'],
                    subject='Test Subject',
                    body='Test Body',
                    attachment_path='test.csv'
                )
                
                mock_open.assert_called_once_with('test.csv', 'rb')
                mock_server.send_message.assert_called_once()

    @patch('src.services.email_service.smtplib.SMTP')
    def test_send_email_smtp_auth_error(self, mock_smtp, mock_logger):
        """Test _send_email handles SMTP authentication errors"""
        import smtplib
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        test_env = {
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'bad_user',
            'SMTP_PASSWORD': 'bad_pass',
            'SMTP_FROM_EMAIL': 'from@test.com'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                with pytest.raises(smtplib.SMTPAuthenticationError):
                    service._send_email(
                        recipients=['test@example.com'],
                        subject='Test Subject',
                        body='Test Body'
                    )

    @patch('src.services.email_service.smtplib.SMTP')
    def test_send_email_file_not_found(self, mock_smtp, mock_logger):
        """Test _send_email handles missing attachment files"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        test_env = {
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_pass',
            'SMTP_FROM_EMAIL': 'from@test.com'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.services.email_service.setup_logger', return_value=mock_logger):
                service = EmailService()
                with pytest.raises(FileNotFoundError):
                    service._send_email(
                        recipients=['test@example.com'],
                        subject='Test Subject',
                        body='Test Body',
                        attachment_path='nonexistent.csv'
                    )