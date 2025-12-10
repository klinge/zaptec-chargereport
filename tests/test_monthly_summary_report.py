import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.reports.monthly_summary_report import MonthlySummaryReport
from src.models.zaptec_models import (
    InstallationReport,
    TotalUserChargerReport,
    UserDetails,
)


class TestMonthlySummaryReport:
    @pytest.fixture
    def sample_installation_report(self):
        """Create sample installation report data for testing"""
        user_reports = [
            TotalUserChargerReport(
                GroupAsString="  Test User 1  ",  # With whitespace to test stripping
                UserDetails=UserDetails(
                    Id="user1", Email="test1@example.com", FullName="Test User 1"
                ),
                TotalChargeSessionCount=5,
                TotalChargeSessionEnergy=125.75,
                TotalChargeSessionDuration=10.5,
            ),
            TotalUserChargerReport(
                GroupAsString="Test User 2",
                UserDetails=UserDetails(
                    Id="user2", Email="test2@example.com", FullName="Test User 2"
                ),
                TotalChargeSessionCount=3,
                TotalChargeSessionEnergy=75.25,
                TotalChargeSessionDuration=6.0,
            ),
        ]

        return InstallationReport(
            InstallationName="Test Installation",
            InstallationAddress="Test Address",
            InstallationZipCode="12345",
            InstallationCity="Test City",
            InstallationTimeZone="Europe/Stockholm",
            GroupedBy="User",
            Fromdate="2024-01-01",
            Enddate="2024-01-31",
            totalUserChargerReportModel=user_reports,
        )

    @patch("src.reports.monthly_summary_report.ZaptecApi")
    @patch("src.reports.monthly_summary_report.get_previous_month_range")
    def test_get_data_for_report(
        self, mock_date_range, mock_api_class, sample_installation_report, mock_logger
    ):
        """Test data retrieval from API"""
        mock_date_range.return_value = (
            "2024-01-01T00:00:00.001",
            "2024-01-31T23:59:59.999",
            "January",
        )

        mock_api = Mock()
        mock_api.get_installation_report.return_value = sample_installation_report
        mock_api_class.return_value.__enter__.return_value = mock_api

        with patch(
            "src.reports.monthly_summary_report.setup_logger", return_value=mock_logger
        ):
            report = MonthlySummaryReport()
            result = report.get_data_for_report()

            assert result == sample_installation_report
            assert report.month_name == "January"
            mock_api.get_installation_report.assert_called_once_with(
                from_date="2024-01-01T00:00:00.001", to_date="2024-01-31T23:59:59.999"
            )

    def test_generate_summary_report(self, sample_installation_report, mock_logger):
        """Test summary report generation from installation data"""
        with patch(
            "src.reports.monthly_summary_report.setup_logger", return_value=mock_logger
        ):
            report = MonthlySummaryReport()
            df = report.generate_summary_report(sample_installation_report)

            # Should have 3 rows: 2 users + 1 total row
            assert len(df) == 3

            # Check column names
            expected_columns = ["user_name", "email", "energy", "duration", "sessions"]
            assert list(df.columns) == expected_columns

            # Check user data (whitespace should be stripped)
            assert df.iloc[0]["user_name"] == "Test User 1"
            assert df.iloc[0]["email"] == "test1@example.com"
            assert df.iloc[0]["energy"] == 125.75
            assert df.iloc[0]["duration"] == 10.5
            assert df.iloc[0]["sessions"] == 5

            assert df.iloc[1]["user_name"] == "Test User 2"
            assert df.iloc[1]["energy"] == 75.25

            # Check totals row
            totals_row = df.iloc[2]
            assert totals_row["user_name"] == "TOTAL"
            assert totals_row["email"] == "-"
            assert totals_row["energy"] == 201.0  # 125.75 + 75.25
            assert totals_row["duration"] == 16.5  # 10.5 + 6.0
            assert totals_row["sessions"] == 8  # 5 + 3

    def test_send_report(self, mock_logger):
        """Test report sending via email"""
        test_df = pd.DataFrame(
            {
                "user_name": ["User 1", "TOTAL"],
                "email": ["test@example.com", "-"],
                "energy": [100.0, 100.0],
                "duration": [5.0, 5.0],
                "sessions": [3, 3],
            }
        )

        mock_email_service = Mock()

        with patch(
            "src.reports.monthly_summary_report.setup_logger", return_value=mock_logger
        ):
            report = MonthlySummaryReport()
            report.month_name = "January"
            report.email_service = mock_email_service

            report.send_report(test_df)

            # Verify email was sent with HTML content
            mock_email_service.send_summary_report.assert_called_once()
            call_args = mock_email_service.send_summary_report.call_args
            body, month = call_args[0]

            assert month == "January"
            assert "<h3>Summering av laddel för January</h3>" in body
            assert "User 1" in body
            assert "test@example.com" in body

    @patch("src.reports.monthly_summary_report.ZaptecApi")
    @patch("src.reports.monthly_summary_report.get_previous_month_range")
    def test_generate_report_end_to_end(
        self, mock_date_range, mock_api_class, sample_installation_report, mock_logger
    ):
        """Test complete report generation workflow"""
        mock_date_range.return_value = (
            "2024-01-01T00:00:00.001",
            "2024-01-31T23:59:59.999",
            "January",
        )

        mock_api = Mock()
        mock_api.get_installation_report.return_value = sample_installation_report
        mock_api_class.return_value.__enter__.return_value = mock_api

        mock_email_service = Mock()

        with patch(
            "src.reports.monthly_summary_report.setup_logger", return_value=mock_logger
        ):
            with patch(
                "src.reports.monthly_summary_report.EmailService",
                return_value=mock_email_service,
            ):
                report = MonthlySummaryReport()
                report.generate_report()

                # Verify API was called
                mock_api.get_installation_report.assert_called_once()

                # Verify email was sent
                mock_email_service.send_summary_report.assert_called_once()

    @patch("src.reports.monthly_summary_report.ZaptecApi")
    @patch("src.reports.monthly_summary_report.get_previous_month_range")
    def test_generate_report_error_handling(
        self, mock_date_range, mock_api_class, mock_logger
    ):
        """Test error handling in report generation"""
        mock_date_range.return_value = (
            "2024-01-01T00:00:00.001",
            "2024-01-31T23:59:59.999",
            "January",
        )

        mock_api = Mock()
        mock_api.get_installation_report.side_effect = Exception("API Error")
        mock_api_class.return_value.__enter__.return_value = mock_api

        mock_email_service = Mock()

        with patch(
            "src.reports.monthly_summary_report.setup_logger", return_value=mock_logger
        ):
            with patch(
                "src.reports.monthly_summary_report.EmailService",
                return_value=mock_email_service,
            ):
                with patch(
                    "src.reports.monthly_summary_report.handle_error"
                ) as mock_handle_error:
                    report = MonthlySummaryReport()
                    report.generate_report()

                    # Verify error handler was called
                    mock_handle_error.assert_called_once()
