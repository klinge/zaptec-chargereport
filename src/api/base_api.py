import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.logger import setup_logger


class BaseApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.username = os.getenv("ZAPTEC_USERNAME")
        self.password = os.getenv("ZAPTEC_PASSWORD")
        self.installation_id = os.getenv("ZAPTEC_INSTALLATION_ID")
        self.environment = os.getenv("ENV", "DEV")
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.session = requests.Session()
        # SSL verification: enabled by default, can be disabled for DEV environments
        self.session.verify = os.getenv("SSL_VERIFY", "true").lower() == "true"
        self.logger = setup_logger()

    def get_auth_token(self) -> str:
        """
        Authenticate with Zaptec API and obtain access token.

        Returns:
            str: Authentication token response containing access_token

        Raises:
            ValueError: If response doesn't contain access token
            requests.exceptions.HTTPError: If authentication fails
        """
        self.logger.debug("Started get_auth_token")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }
        self.logger.debug(f"In get_auth_token. Data is: {data}")
        self.logger.debug(f"headers is: {headers}")
        self.logger.debug(f"base_url is: {self.base_url}")
        self.logger.debug(f"session is: {self.session}")
        response = self.session.post(
            f"{self.base_url}/oauth/token", headers=headers, data=data
        )

        response.raise_for_status()
        token_data = response.json()

        if "access_token" not in token_data:
            raise ValueError("No access token in response")

        self.access_token = token_data["access_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
        self.logger.debug(f"Token set. Expires at: {self.token_expiry}")
        return token_data

    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication token for API requests.

        Returns:
            Dict[str, str]: Headers dictionary containing Authorization and Content-Type

        Note:
            Automatically fetches new auth token if none exists
        """
        self.logger.debug("Started get_headers")
        if not self.is_token_valid():
            self.logger.info("Token not existing or expired - Getting new auth token")
            self.get_auth_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def is_token_valid(self) -> bool:
        if not self.access_token or not self.token_expiry:
            self.logger.debug("Token is invalid: No access token or expiry")
            return False
        # Add buffer time (e.g., 2 minutes) to prevent edge cases
        return datetime.now() < (self.token_expiry - timedelta(minutes=2))

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Generic method to make API calls with automatic token handling using session

        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response:  the response object from the API call
        """
        self.logger.debug("Started _make_request")
        headers = self.get_headers()
        url = f'{self.base_url}/{endpoint.lstrip("/")}'
        response = self.session.request(method, url, headers=headers, **kwargs)

        self.logger.debug(
            f"Response: {response.status_code} {response.text}. Endpoint: {endpoint}"
        )
        response.raise_for_status()

        return response

    # Enable context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
