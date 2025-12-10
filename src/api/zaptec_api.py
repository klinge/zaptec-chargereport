import urllib3
import json
from typing import Dict, List, Optional
from pydantic import ValidationError
from src.api.base_api import BaseApi
from src.utils.logger import setup_logger
from src.models.zaptec_models import (
    ChargingSessionResponse,
    Installation,
    ChargersResponse,
    InstallationReport,
)

urllib3.disable_warnings()


class ZaptecApi(BaseApi):
    def __init__(self):
        self.base_url = "https://api.zaptec.com"
        super().__init__(self.base_url)
        self.logger = setup_logger()

    def get_installation(self) -> List[Installation]:
        """Fetches basic information about installations you have access to"""
        self.logger.debug("Calling /api/installation")
        response = self._make_request(
            method="GET",
            endpoint="/api/installation",
        )
        return [Installation.model_validate(item) for item in response.json()["Data"]]

    def get_chargers(self) -> ChargersResponse:
        """
        Fetch information about all chargers in the installation.

        Returns:
            ChargersResponse: Object containing details like
            ID, name, status, and configuration
        """
        self.logger.debug("Calling /api/chargers")
        response = self._make_request("GET", endpoint="/api/chargers")
        return ChargersResponse.model_validate(response.json())

    def get_charging_sessions(
        self, from_date: str, to_date: str
    ) -> ChargingSessionResponse:
        """
        Fetch charging session data for a specific date range.

        Args:
            from_date (str): Start date in format YYYY-MM-DDThh:mm:ss.sssZ
            to_date (str): End date in format YYYY-MM-DDThh:mm:ss.sssZ

        Returns:
            ChargingSessionResponse: Object containing charging session data
        """
        params = {
            "installationId": self.installation_id,
            "From": from_date,
            "To": to_date,
            "DetailLevel": 0,
            "PageIndex": 0,
        }

        all_sessions = []
        page_index = 0
        page_count = 1  # Assume at least one page
        jsonResponse = {}  # Ensure jsonResponse is always defined

        while page_index < page_count:
            params = {
                "installationId": self.installation_id,
                "From": from_date,
                "To": to_date,
                "DetailLevel": 0,
                "PageIndex": page_index,
            }

            self.logger.debug(f"Calling /api/chargehistory with params: {params}")
            response = self._make_request(
                method="GET", endpoint="/api/chargehistory", params=params
            )

            jsonResponse = response.json()
            # Remove SignedSession from each session, it's big and never needed
            for session in jsonResponse["Data"]:
                session.pop("SignedSession", None)

            all_sessions.extend(jsonResponse["Data"])

            # Update page_count from response (if available)
            page_count = jsonResponse["Pages"]
            self.logger.info(
                f"Fetched page {page_index + 1}/{page_count} with {len(jsonResponse['Data'])} sessions"
            )
            page_index += 1

        # Build a single response object with all sessions
        combined_response = jsonResponse.copy()
        combined_response["Data"] = all_sessions

        return ChargingSessionResponse.model_validate(obj=combined_response)

    def get_installation_report(
        self, from_date: str, to_date: str
    ) -> InstallationReport:
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
        self.logger.debug("Starting method: get_installation_report")
        payload = {
            "fromDate": from_date,
            "endDate": to_date,
            "installationId": self.installation_id,
            "groupBy": 0,  # 0 = by user, 1 = by charger, 2 = by charge card
        }
        self.logger.debug(f"Payload: {payload}")

        self.logger.debug(
            f"Calling /api/chargehistory/installationreport with params: {payload}"
        )
        response = self._make_request(
            method="POST",
            endpoint="/api/chargehistory/installationreport",
            json=payload,
        )
        return InstallationReport.model_validate(response.json())
