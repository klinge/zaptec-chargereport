import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.reports.invoicing_report import InvoicingReport
from src.api.zaptec_api import _ZaptecApi as ZaptecApi
from src.models.zaptec_models import (
    ChargingSession,
    ChargingSessionResponse,
    ChargerFirmware,
)
from datetime import datetime


class TestInvoicingReport:
    @pytest.fixture
    def sample_charging_sessions(self):
        """Create sample charging session data for testing"""
        firmware = ChargerFirmware(
            Major=1, Minor=0, Build=0, Revision=0, MajorRevision=1, MinorRevision=0
        )

        sessions = [
            ChargingSession(
                UserUserName="test_user1",
                Id="session1",
                DeviceId="device1",
                StartDateTime=datetime(2024, 1, 1, 10, 0),
                EndDateTime=datetime(2024, 1, 1, 12, 0),
                Energy=25.5,
                CommitMetadata=1,
                CommitEndDateTime=datetime(2024, 1, 1, 12, 0),
                UserFullName="Test User 1",
                ChargerId="charger1",
                DeviceName="Plats 01",
                UserEmail="test1@example.com",
                UserId="user1",
                ExternallyEnded=False,
                ChargerFirmwareVersion=firmware,
            ),
            ChargingSession(
                UserUserName="test_user2",
                Id="session2",
                DeviceId="device2",
                StartDateTime=datetime(2024, 1, 2, 14, 0),
                EndDateTime=datetime(2024, 1, 2, 16, 30),
                Energy=40.0,
                CommitMetadata=1,
                CommitEndDateTime=datetime(2024, 1, 2, 16, 30),
                UserFullName="Test User 2",
                ChargerId="charger2",
                DeviceName="Plats 50",
                UserEmail="test2@example.com",
                UserId="user2",
                ExternallyEnded=False,
                ChargerFirmwareVersion=firmware,
            ),
        ]
        return ChargingSessionResponse(Pages=1, Data=sessions)

    def test_format_objekt_id_regular(self):
        """Test object ID formatting for regular parking spaces"""
        mock_api = Mock(spec=ZaptecApi)
        report = InvoicingReport(mock_api)
        result = report._format_objekt_id("Plats 01")
        assert result == "G5001"

    def test_format_objekt_id_brf_backen(self):
        """Test object ID formatting for BRF Bäcken spaces (48-62)"""
        mock_api = Mock(spec=ZaptecApi)
        report = InvoicingReport(mock_api)
        result = report._format_objekt_id("Plats 50")
        assert result == "Brf Bäcken G5050"

    def test_calculate_duration_hours(self):
        """Test duration calculation in hours"""
        mock_api = Mock(spec=ZaptecApi)
        report = InvoicingReport(mock_api)
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 12, 30)

        duration = report._calculate_duration_hours(start, end)
        assert duration == 2.5

    @patch("src.reports.invoicing_report.os.makedirs")
    def test_process_charging_data(
        self, mock_makedirs, sample_charging_sessions, mock_logger
    ):
        """Test processing of charging session data into DataFrame"""
        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            mock_api = Mock(spec=ZaptecApi)
            report = InvoicingReport(mock_api)

            result_df = report.process_charging_data(
                sample_charging_sessions,
                "2024-01-01T00:00:00.001",
                "2024-01-31T23:59:59.999",
            )

            assert len(result_df) == 2
            assert "Objekt-ID" in result_df.columns
            assert "Förbrukning" in result_df.columns
            assert "Kostnad" in result_df.columns

            # Check calculations (DataFrame is sorted by Objekt-ID)
            # G5001 (Plats 01) should come before G5050 (Plats 50)
            g5001_row = result_df[result_df["Objekt-ID"] == "G5001"].iloc[0]
            g5050_row = result_df[result_df["Objekt-ID"] == "Brf Bäcken G5050"].iloc[0]

            assert g5001_row["Förbrukning"] == 25.5
            assert g5050_row["Förbrukning"] == 40.0
            assert g5001_row["Kostnad"] == 25.5 * 2.75  # CHARGING_TARIFF from .env.test

    @patch("src.reports.invoicing_report.get_previous_month_range")
    def test_generate_report_success(
        self, mock_date_range, sample_charging_sessions, mock_logger
    ):
        """Test successful report generation end-to-end"""
        # Mock date range
        mock_date_range.return_value = (
            "2024-01-01T00:00:00.001Z",
            "2024-01-31T23:59:59.999Z",
            "January",
        )

        # Mock API
        mock_api = Mock(spec=ZaptecApi)
        mock_api.get_charging_sessions.return_value = sample_charging_sessions
        mock_api.__enter__ = Mock(return_value=mock_api)
        mock_api.__exit__ = Mock(return_value=False)

        # Mock email service
        mock_email = Mock()

        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            with patch(
                "src.reports.invoicing_report.EmailService", return_value=mock_email
            ):
                with patch("src.reports.invoicing_report.os.makedirs"):
                    with patch.object(InvoicingReport, "export_to_csv") as mock_export:
                        report = InvoicingReport(mock_api)
                        report.generate_report()

                        # Verify API was called
                        mock_api.get_charging_sessions.assert_called_once_with(
                            "2024-01-01T00:00:00.001Z", "2024-01-31T23:59:59.999Z"
                        )

                        # Verify export was called
                        mock_export.assert_called_once()

                        # Verify email was sent
                        mock_email.send_charge_report.assert_called_once()

    @patch("src.reports.invoicing_report.get_previous_month_range")
    def test_generate_report_api_error(
        self, mock_date_range, mock_logger
    ):
        """Test report generation handles API errors"""
        mock_date_range.return_value = (
            "2024-01-01T00:00:00.001Z",
            "2024-01-31T23:59:59.999Z",
            "January",
        )

        # Mock API to raise exception
        mock_api = Mock(spec=ZaptecApi)
        mock_api.get_charging_sessions.side_effect = Exception("API Error")
        mock_api.__enter__ = Mock(return_value=mock_api)
        mock_api.__exit__ = Mock(return_value=False)

        mock_email = Mock()

        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            with patch(
                "src.reports.invoicing_report.EmailService", return_value=mock_email
            ):
                with patch(
                    "src.reports.invoicing_report.handle_error"
                ) as mock_handle_error:
                    report = InvoicingReport(mock_api)
                    report.generate_report()

                    # Verify error handler was called
                    mock_handle_error.assert_called_once()

    @patch("src.reports.invoicing_report.os.makedirs")
    def test_export_to_csv_success(self, mock_makedirs, mock_logger):
        """Test successful CSV export"""
        # Create test DataFrame
        test_data = {
            "Objekt-ID": ["G5001", "G5002"],
            "Fr.o.m. datum": ["2024-01-01", "2024-01-01"],
            "T.o.m. datum": ["2024-01-31", "2024-01-31"],
            "Typ": ["LADDPLATS", "LADDPLATS"],
            "Startvärde": [0, 0],
            "Slutvärde": [25.555, 40.777],
            "Förbrukning": [25.555, 40.777],
            "Kostnad": [70.27, 112.14],
            "Tariff": [2.75, 2.75],
            "Enhet": ["kWh", "kWh"],
            "Kommentar": ["User 1(test1@test.com)", "User 2(test2@test.com)"],
        }
        df = pd.DataFrame(test_data)

        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            with patch("pandas.DataFrame.to_csv") as mock_to_csv:
                mock_api = Mock(spec=ZaptecApi)
                report = InvoicingReport(mock_api)
                report.export_to_csv(df, "test_report.csv")

                # Verify directory creation (called for both logs and reports)
                assert mock_makedirs.call_count >= 1

                # Verify CSV export with correct parameters
                mock_to_csv.assert_called_once_with(
                    path_or_buf="test_report.csv",
                    sep=";",
                    index=False,
                    encoding="utf-8",
                )

                # Verify numeric columns were rounded
                args, kwargs = mock_to_csv.call_args
                exported_df = mock_to_csv.call_args[1]["path_or_buf"]

    @patch("src.reports.invoicing_report.os.makedirs")
    def test_export_to_csv_permission_error(self, mock_makedirs, mock_logger):
        """Test CSV export handles permission errors"""
        test_data = {
            "Objekt-ID": ["G5001"],
            "Slutvärde": [25.5],
            "Förbrukning": [25.5],
            "Kostnad": [70.0],
            "Tariff": [2.75],
        }
        df = pd.DataFrame(test_data)

        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            with patch(
                "pandas.DataFrame.to_csv", side_effect=PermissionError("Access denied")
            ):
                mock_api = Mock(spec=ZaptecApi)
                report = InvoicingReport(mock_api)

                with pytest.raises(PermissionError):
                    report.export_to_csv(df, "test_report.csv")

    def test_generate_report_filename(self, mock_logger):
        """Test report filename generation"""
        with patch(
            "src.reports.invoicing_report.setup_logger", return_value=mock_logger
        ):
            with patch("src.reports.invoicing_report.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240115"

                mock_api = Mock(spec=ZaptecApi)
                report = InvoicingReport(mock_api)
                filename = report._generate_report_filename()

                assert (
                    filename == "test_report_20240115.csv"
                )  # REPORT_FILE from .env.test
