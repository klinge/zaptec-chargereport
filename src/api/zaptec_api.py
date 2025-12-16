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

        # Build a single combined response with all sessions
        combined_response = jsonResponse.copy()
        combined_response["Data"] = all_sessions

        # === NEW 20251215: Filter out guest/unauthenticated sessions ===
        original_count = len(all_sessions)
        filtered_sessions = []
        skipped_count = 0

        for session_dict in all_sessions:
            # A session is considered "guest" if it lacks any of the key user fields
            if not session_dict.get("UserId") or not session_dict.get("UserUserName"):
                skipped_count += 1
                self.logger.warning(
                    "Skipping guest/unauthenticated charging session during invoicing report. "
                    "Session details: Id=%s, Start=%s, End=%s, Energy=%.3f kWh, DeviceName=%s",
                    session_dict.get("Id"),
                    session_dict.get("StartDateTime"),
                    session_dict.get("EndDateTime"),
                    session_dict.get("Energy", 0),
                    session_dict.get("DeviceName"),
                )
                continue
            filtered_sessions.append(session_dict)

        if skipped_count > 0:
            self.logger.warning(
                f"Skipped {skipped_count} guest/unauthenticated session(s) out "
                "of %s total sessions",
                original_count,
            )

        combined_response["Data"] = filtered_sessions

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

        data = response.json()
        self.logger.debug(f"Raw response JSON: {data}")

        # Temporary workaround: Check if first item is a "ghost" row without user info
        reports = data.get("totalUserChargerReportModel", [])
        if reports and "UserDetails" not in reports[0] and "GroupAsString" not in reports[0]:
            self.logger.warning(
                "Detected anomalous first row in installation report (likely guest/unknown sessions). "
                "Skipping it temporarily. First row data: %s",
                reports[0]
            )
            # Remove the first item
            data["totalUserChargerReportModel"] = reports[1:]

        # Now validate the (possibly modified) data
        return InstallationReport.model_validate(data)
