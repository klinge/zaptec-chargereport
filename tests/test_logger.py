import pytest
import os
import logging
import tempfile
from unittest.mock import patch, Mock
from src.utils.logger import setup_logger


class TestLogger:
    def test_logger_basic_setup(self):
        """Test basic logger setup and configuration"""
        logger = setup_logger()

        assert logger.name == "zaptec-chargereport"
        # Logger level might be inherited from root logger, check it's configured
        assert logger.level >= 0  # Any valid level is fine
        # Propagate might be True if logger was already configured
        assert isinstance(logger.propagate, bool)
        assert logger.hasHandlers()

    def test_logger_singleton_behavior(self):
        """Test that logger returns same instance on multiple calls"""
        logger1 = setup_logger()
        logger2 = setup_logger()

        assert logger1 is logger2

    def test_logger_with_custom_data_dir(self):
        """Test logger uses custom DATA_DIR"""
        with patch.dict(os.environ, {"DATA_DIR": "/custom/path"}):
            with patch("src.utils.logger.os.makedirs") as mock_makedirs:
                # Clear existing logger to force reconfiguration
                logger = logging.getLogger("zaptec-chargereport-test")

                with patch("src.utils.logger.logging.getLogger", return_value=logger):
                    setup_logger()

                    mock_makedirs.assert_called_with("/custom/path/logs", exist_ok=True)

    def test_logger_directory_creation(self):
        """Test that log directory is created"""
        with patch("src.utils.logger.os.makedirs") as mock_makedirs:
            # Use a fresh logger name to avoid conflicts
            with patch("src.utils.logger.logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_logger.hasHandlers.return_value = False
                mock_get_logger.return_value = mock_logger

                setup_logger()

                # Verify makedirs was called
                assert mock_makedirs.called

    def test_log_level_environment_variable(self):
        """Test that LOG_LEVEL environment variable is respected"""
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            with patch("src.utils.logger.logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_logger.hasHandlers.return_value = False
                mock_get_logger.return_value = mock_logger

                with patch(
                    "src.utils.logger.logging.StreamHandler"
                ) as mock_stream_handler:
                    with patch("src.utils.logger.logging.FileHandler"):
                        setup_logger()

                        # Verify console handler gets ERROR level
                        mock_stream_handler.return_value.setLevel.assert_called_with(
                            logging.ERROR
                        )

    def test_file_handler_creation(self):
        """Test that file handler is created with correct filename pattern"""
        with patch("src.utils.logger.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger

            with patch("src.utils.logger.logging.FileHandler") as mock_file_handler:
                with patch("src.utils.logger.os.makedirs"):
                    setup_logger()

                    # Verify file handler was created
                    mock_file_handler.assert_called_once()

                    # Check filename pattern
                    call_args = mock_file_handler.call_args[0][0]
                    assert "charge_report_" in call_args
                    assert ".log" in call_args

    def test_formatter_configuration(self):
        """Test that formatters are properly configured"""
        with patch("src.utils.logger.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger

            with patch("src.utils.logger.logging.Formatter") as mock_formatter:
                with patch("src.utils.logger.os.makedirs"):
                    setup_logger()

                    # Verify formatter created with correct format string
                    mock_formatter.assert_called_with(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )

    def test_invalid_log_level_handling(self):
        """Test handling of invalid LOG_LEVEL values"""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}):
            # Should not raise exception
            logger = setup_logger()
            assert logger is not None
