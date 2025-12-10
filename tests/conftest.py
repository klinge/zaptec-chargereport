import pytest
import os
from unittest.mock import patch
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def setup_test_env():
    """Load test environment variables for all tests"""
    load_dotenv('.env.test', override=True)
    yield
    # Cleanup after test
    for key in os.environ.copy():
        if key.startswith(('ZAPTEC_', 'SMTP_', 'CHARGING_', 'DATA_', 'REPORT_')):
            os.environ.pop(key, None)

@pytest.fixture
def mock_logger():
    """Mock logger to avoid log output during tests"""
    with patch('src.utils.logger.setup_logger') as mock:
        mock.return_value.info = lambda x: None
        mock.return_value.debug = lambda x: None
        mock.return_value.warning = lambda x: None
        mock.return_value.error = lambda x: None
        yield mock.return_value