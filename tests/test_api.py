import pytest
import responses
from unittest.mock import patch, Mock
from src.api.zaptec_api import ZaptecApi
from src.api.base_api import BaseApi


class TestBaseApi:
    def test_ssl_verification_enabled_by_default(self):
        """Test that SSL verification is enabled by default"""
        with patch.dict("os.environ", {}, clear=True):
            api = BaseApi("https://test.com")
            assert api.session.verify

    def test_ssl_verification_disabled_in_dev(self):
        """Test that SSL verification can be disabled via env var"""
        with patch.dict("os.environ", {"SSL_VERIFY": "false"}):
            api = BaseApi("https://test.com")
            assert api.session.verify == False

    def test_token_validity_check(self):
        """Test token validity checking logic"""
        from datetime import datetime, timedelta

        api = BaseApi("https://test.com")

        # No token should be invalid
        assert api.is_token_valid() == False

        # Expired token should be invalid
        api.access_token = "test_token"
        api.token_expiry = datetime.now() - timedelta(minutes=5)
        assert api.is_token_valid() == False

        # Valid token should be valid
        api.token_expiry = datetime.now() + timedelta(minutes=10)
        assert api.is_token_valid()


class TestZaptecApi:
    @responses.activate
    def test_get_auth_token(self):
        """Test authentication token retrieval"""
        # Mock the OAuth token endpoint
        responses.add(
            responses.POST,
            "https://api.zaptec.com/oauth/token",
            json={"access_token": "test_token", "expires_in": 3600},
            status=200,
        )

        with patch.dict(
            "os.environ",
            {"ZAPTEC_USERNAME": "test_user", "ZAPTEC_PASSWORD": "test_pass"},
        ):
            api = ZaptecApi()
            token_data = api.get_auth_token()

            assert token_data["access_token"] == "test_token"
            assert api.access_token == "test_token"

    @responses.activate
    def test_get_installation(self):
        """Test installation data retrieval"""
        # Mock auth token
        responses.add(
            responses.POST,
            "https://api.zaptec.com/oauth/token",
            json={"access_token": "test_token", "expires_in": 3600},
        )

        # Mock installation endpoint with minimal required fields
        responses.add(
            responses.GET,
            "https://api.zaptec.com/api/installation",
            json={
                "Data": [
                    {
                        "Id": "550e8400-e29b-41d4-a716-446655440000",
                        "Name": "Test Installation",
                        "Address": "Test Address",
                        "ZipCode": "12345",
                        "City": "Test City",
                        "CountryId": "550e8400-e29b-41d4-a716-446655440001",
                        "InstallationType": 1,
                        "MaxCurrent": 32.0,
                        "AvailableCurrent": 32.0,
                        "AvailableCurrentPhase1": 32.0,
                        "AvailableCurrentPhase2": 32.0,
                        "AvailableCurrentPhase3": 32.0,
                        "AvailableCurrentMode": 1,
                        "AvailableCurrentScheduleWeekendActive": False,
                        "InstallationCategoryId": "550e8400-e29b-41d4-a716-446655440002",
                        "InstallationCategory": "Test Category",
                        "UseLoadBalancing": True,
                        "IsRequiredAuthentication": True,
                        "Latitude": 59.3293,
                        "Longitude": 18.0686,
                        "Active": True,
                        "NetworkType": 1,
                        "AvailableInternetAccessPLC": True,
                        "AvailableInternetAccessWiFi": True,
                        "CreatedOnDate": "2024-01-01T00:00:00Z",
                        "UpdatedOn": "2024-01-01T00:00:00Z",
                        "CurrentUserRoles": 1,
                        "AuthenticationType": 1,
                        "MessagingEnabled": True,
                        "RoutingId": "test-routing",
                        "OcppCloudUrlVersion": 1,
                        "IsSubscriptionsAvailableForCurrentUser": True,
                        "AvailableFeatures": 1,
                        "EnabledFeatures": 1,
                    }
                ]
            },
            status=200,
        )

        api = ZaptecApi()
        installations = api.get_installation()

        assert len(installations) == 1
        assert installations[0].Name == "Test Installation"

    @responses.activate
    def test_get_chargers(self):
        """Test chargers data retrieval"""
        responses.add(
            responses.POST,
            "https://api.zaptec.com/oauth/token",
            json={"access_token": "test_token", "expires_in": 3600},
        )

        responses.add(
            responses.GET,
            "https://api.zaptec.com/api/chargers",
            json={
                "Pages": 1,
                "Data": [
                    {
                        "OperatingMode": 1,
                        "IsOnline": True,
                        "Id": "550e8400-e29b-41d4-a716-446655440000",
                        "MID": "TEST123",
                        "DeviceId": "device1",
                        "SerialNo": "SN123",
                        "Name": "Test Charger",
                        "CreatedOnDate": "2024-01-01T00:00:00Z",
                        "CircuitId": "550e8400-e29b-41d4-a716-446655440001",
                        "Active": True,
                        "CurrentUserRoles": 1,
                        "Pin": "1234",
                        "DeviceType": 1,
                        "InstallationName": "Test Installation",
                        "InstallationId": "550e8400-e29b-41d4-a716-446655440002",
                        "AuthenticationType": 1,
                        "IsAuthorizationRequired": True,
                    }
                ],
            },
        )

        api = ZaptecApi()
        chargers = api.get_chargers()

        assert chargers.Pages == 1
        assert len(chargers.Data) == 1
        assert chargers.Data[0].Name == "Test Charger"

    @responses.activate
    def test_get_charging_sessions(self):
        """Test charging sessions data retrieval"""
        responses.add(
            responses.POST,
            "https://api.zaptec.com/oauth/token",
            json={"access_token": "test_token", "expires_in": 3600},
        )

        responses.add(
            responses.GET,
            "https://api.zaptec.com/api/chargehistory",
            json={
                "Pages": 1,
                "Data": [
                    {
                        "UserUserName": "test_user",
                        "Id": "session1",
                        "DeviceId": "device1",
                        "StartDateTime": "2024-01-01T10:00:00Z",
                        "EndDateTime": "2024-01-01T12:00:00Z",
                        "Energy": 25.5,
                        "CommitMetadata": 1,
                        "CommitEndDateTime": "2024-01-01T12:00:00Z",
                        "UserFullName": "Test User",
                        "ChargerId": "charger1",
                        "DeviceName": "Plats 01",
                        "UserEmail": "test@example.com",
                        "UserId": "user1",
                        "ExternallyEnded": False,
                        "ChargerFirmwareVersion": {
                            "Major": 1,
                            "Minor": 0,
                            "Build": 0,
                            "Revision": 0,
                            "MajorRevision": 1,
                            "MinorRevision": 0,
                        },
                        "SignedSession": "large_signed_data_to_be_removed",
                    }
                ],
            },
        )

        with patch.dict("os.environ", {"ZAPTEC_INSTALLATION_ID": "test-installation"}):
            api = ZaptecApi()
            sessions = api.get_charging_sessions(
                "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.999Z"
            )

            assert sessions.Pages == 1
            assert len(sessions.Data) == 1
            assert sessions.Data[0].Energy == 25.5

    @responses.activate
    def test_get_installation_report(self):
        """Test installation report data retrieval"""
        responses.add(
            responses.POST,
            "https://api.zaptec.com/oauth/token",
            json={"access_token": "test_token", "expires_in": 3600},
        )

        responses.add(
            responses.POST,
            "https://api.zaptec.com/api/chargehistory/installationreport",
            json={
                "InstallationName": "Test Installation",
                "InstallationAddress": "Test Address",
                "InstallationZipCode": "12345",
                "InstallationCity": "Test City",
                "InstallationTimeZone": "Europe/Stockholm",
                "GroupedBy": "User",
                "Fromdate": "2024-01-01",
                "Enddate": "2024-01-31",
                "totalUserChargerReportModel": [
                    {
                        "GroupAsString": "Test User",
                        "UserDetails": {
                            "Id": "user1",
                            "Email": "test@example.com",
                            "FullName": "Test User",
                        },
                        "TotalChargeSessionCount": 5,
                        "TotalChargeSessionEnergy": 125.5,
                        "TotalChargeSessionDuration": 10.5,
                    }
                ],
            },
        )

        with patch.dict("os.environ", {"ZAPTEC_INSTALLATION_ID": "test-installation"}):
            api = ZaptecApi()
            report = api.get_installation_report(
                "2024-01-01T00:00:00.000", "2024-01-31T23:59:59.999"
            )

            assert report.InstallationName == "Test Installation"
            assert len(report.totalUserChargerReportModel) == 1
            assert (
                report.totalUserChargerReportModel[0].TotalChargeSessionEnergy == 125.5
            )
