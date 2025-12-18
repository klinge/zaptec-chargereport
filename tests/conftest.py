import pytest
import os
from unittest.mock import patch
from dotenv import load_dotenv
from src.api.zaptec_api import _ZaptecApi


# Load environment at session start BEFORE creating API instance
# This ensures credentials are available for session-scoped fixtures
def pytest_configure(config):
    """Pytest hook that runs before any tests."""
    # Load real .env first (production credentials)
    load_dotenv(".env", override=False)
    # Then load test overrides (.env.test) only for specific variables
    # but don't override real credentials
    load_dotenv(".env.test", override=False)


@pytest.fixture(autouse=True)
def setup_test_env(request):
    """
    Reset and load environment for each test based on test type.
    - Unit tests: Load .env.test with mock credentials (clears old values first)
    - Integration tests: Load real .env credentials (clears old values first)
    """
    is_integration = request.node.get_closest_marker("integration") is not None
    
    # Clear all test-related env vars first (for clean slate)
    # Include environment-prefixed vars like DEV_SMTP_* and PROD_SMTP_*
    for key in list(os.environ.keys()):
        if key.startswith(("ZAPTEC_", "SMTP_", "CHARGING_", "DATA_", "REPORT_", 
                          "DEV_", "PROD_", "TEST_")):
            os.environ.pop(key, None)
    
    # Load appropriate environment file with override=True (ensures proper values are set)
    if is_integration:
        # Integration tests: load real .env credentials
        load_dotenv(".env", override=True)
    else:
        # Unit tests: load mock .env.test credentials
        load_dotenv(".env.test", override=True)
    
    yield
    
    # Cleanup after test
    for key in list(os.environ.keys()):
        if key.startswith(("ZAPTEC_", "SMTP_", "CHARGING_", "DATA_", "REPORT_", 
                          "DEV_", "PROD_", "TEST_")):
            os.environ.pop(key, None)


@pytest.fixture
def mock_logger():
    """Mock logger to avoid log output during tests"""
    with patch("src.utils.logger.setup_logger") as mock:
        mock.return_value.info = lambda x: None
        mock.return_value.debug = lambda x: None
        mock.return_value.warning = lambda x: None
        mock.return_value.error = lambda x: None
        yield mock.return_value


@pytest.fixture(scope="session")
def zaptec_api_context():
    """
    Session-scoped context manager that keeps the API session open for all tests.
    This prevents session closure between tests and avoids repeated auth calls.
    Authenticates ONCE at setup so all tests share the same token.
    """
    api = _ZaptecApi()
    api.__enter__()  # Start the context but don't exit it
    
    # Authenticate once at the start - this is ONE auth call for the entire session
    try:
        api.get_auth_token()
    except Exception as e:
        # Auth failed - tests will still share this broken state rather than each trying individually
        api.logger.warning(f"Initial session auth failed: {e}")
    
    yield api
    api.__exit__(None, None, None)  # Clean up only after all tests


@pytest.fixture(scope="class", autouse=True)
def api(request, zaptec_api_context):
    """
    Attach the zaptec_api instance to test classes so tests can use `self.api`.
    This avoids creating multiple auth requests across tests.
    """
    request.cls.api = zaptec_api_context
    yield
