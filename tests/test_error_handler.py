import pytest
from unittest.mock import Mock
from src.utils.error_handler import handle_error
from src.services.email_service import EmailService

class TestErrorHandler:
    def test_handle_error_logs_and_sends_email(self):
        """Test that handle_error logs the error and sends email notification"""
        # Create mocks
        mock_logger = Mock()
        mock_email_service = Mock(spec=EmailService)
        test_error = Exception("Test error message")
        
        # Call the error handler
        handle_error(test_error, mock_logger, mock_email_service)
        
        # Verify logger was called
        mock_logger.error.assert_called_once_with("Test error message")
        mock_logger.debug.assert_called_once()
        
        # Verify email service was called
        mock_email_service.send_error.assert_called_once()
        
        # Check that the error message contains the exception details
        call_args = mock_email_service.send_error.call_args[0][0]
        assert "Test error message" in call_args
        assert "Traceback:" in call_args

    def test_handle_error_email_failure(self):
        """Test that handle_error handles email sending failures gracefully"""
        mock_logger = Mock()
        mock_email_service = Mock(spec=EmailService)
        mock_email_service.send_error.side_effect = Exception("Email failed")
        test_error = Exception("Original error")
        
        # Should not raise exception even if email fails
        handle_error(test_error, mock_logger, mock_email_service)
        
        # Verify both errors were logged (original error first, then email error)
        assert mock_logger.error.call_count == 2
        mock_logger.error.assert_any_call("Original error")
        mock_logger.error.assert_any_call("Failed to send error email: Email failed")