import requests
import urllib3
import os
from typing import Dict, List, Optional
from models import ChargingSessionResponse, Installation, ChargersResponse, InstallationReport

urllib3.disable_warnings()

class ZaptecApi:
    def __init__(self):
        self.base_url = "https://api.zaptec.com"
        self.username = os.getenv('ZAPTEC_USERNAME')
        self.password = os.getenv('ZAPTEC_PASSWORD')
        self.installation_id = os.getenv('ZAPTEC_INSTALLATION_ID')
        self.access_token: Optional[str] = None
    
    def get_auth_token(self) -> str:
        """
        Authenticate with Zaptec API and obtain access token.
    
        Returns:
            str: Authentication token response containing access_token
        
        Raises:
            ValueError: If response doesn't contain access token
            requests.exceptions.HTTPError: If authentication fails
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }

        response = requests.post(
            f'{self.base_url}/oauth/token',
            headers=headers,
            data=data,
            verify=False
        )

        response.raise_for_status()
        token_data = response.json()

        if 'access_token' not in token_data:
            raise ValueError("No access token in response")
        
        self.access_token = token_data['access_token']
        return token_data
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication token for API requests.
    
        Returns:
            Dict[str, str]: Headers dictionary containing Authorization and Content-Type
        
        Note:
            Automatically fetches new auth token if none exists
        """
        if not self.access_token:
            self.get_auth_token()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_installation(self) -> List[Installation]:
        headers = self.get_headers()
        response = requests.get(
            f'{self.base_url}/api/installation',
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        return [Installation.model_validate(item) for item in response.json()['Data']]

    def get_chargers(self) -> ChargersResponse:
        """
        Fetch information about all chargers in the installation.
    
        Returns:
            ChargersResponse: Object containing details like
            ID, name, status, and configuration
        """
        headers = self.get_headers()
        response = requests.get(
            f'{self.base_url}/api/chargers',
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        return ChargersResponse.model_validate(response.json())
    
    def get_charging_sessions(self, from_date: str, to_date: str) -> ChargingSessionResponse:
        """
        Fetch charging session data for a specific date range.

        Args:
            from_date (str): Start date in format YYYY-MM-DDThh:mm:ss.sssZ
            to_date (str): End date in format YYYY-MM-DDThh:mm:ss.sssZ
    
        Returns:
            ChargingSessionResponse: Object containing charging session data
        """
        headers = self.get_headers()
        
        params = {
            'installationId': self.installation_id,
            'From': from_date,
            'To': to_date,
            'DetailLevel': 0
        }
        
        response = requests.get(
            f'{self.base_url}/api/chargehistory',
            headers=headers,
            params=params,
            verify=False
        )
        response.raise_for_status()
        jsonResponse = response.json()

        # Remove SignedSession from each session, it's big and never needed
        for session in jsonResponse["Data"]:
            session.pop('SignedSession', None)
        
        return ChargingSessionResponse.model_validate(response.json())
    

    def get_installation_report(self, from_date: str, to_date: str) -> InstallationReport:
        """
        Fetches summarized energy usage for all users in an installation for a specific date range.
    
        Args:
            from_date (str): Start date in format YYYY-MM-DDThh:mm:ss.sss
            to_date (str): End date in format YYYY-MM-DDThh:mm:ss.sss
        
        Returns:
            InstallationReport: Object containing summarized charging data per user
        
        Note:
            This endpoint requires dates without 'Z' suffix, unlike get_charging_sessions
        """
        headers = self.get_headers()

        payload = {
            "fromDate": from_date,
            "endDate": to_date,
            "installationId": self.installation_id,
            "groupBy": 0
        }

        response = requests.post(
            f'{self.base_url}/api/chargehistory/installationreport',
            headers=headers,
            json=payload,
            verify=False
        )

        response.raise_for_status()
        return InstallationReport.model_validate(response.json())



