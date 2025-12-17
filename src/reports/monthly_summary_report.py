from src.api.zaptec_api import _ZaptecApi as ZaptecApi
from src.models.zaptec_models import InstallationReport
from src.services.email_service import EmailService
from src.utils.logger import setup_logger
from src.utils.dateutils import get_previous_month_range
from src.utils.error_handler import handle_error
import pandas as pd
from typing import NoReturn, Optional


class MonthlySummaryReport:
    """A class for generating and distributing monthly summary reports of charging activities.

    This class handles the complete workflow of generating monthly summary reports from Zaptec
    charging data, including data retrieval, processing into a pandas DataFrame, and email
    distribution. The report summarizes charging statistics for the previous month for all users.

    Attributes:
        logger: Configured logger instance for tracking operations
        email_service (EmailService): Service instance for handling email operations
        month_name (Optional[str]): Name of the month for which the report is generated

    The report includes the following metrics per user:
        - User name
        - Email address
        - Total energy consumption (kWh)
        - Total charging duration
        - Number of charging sessions

    The report generation process includes:
        1. Retrieving data for the previous month from Zaptec API
        2. Processing data into a pandas DataFrame with user-specific metrics
        3. Adding a totals row with aggregate statistics
        4. Formatting and sending the report via email

    Example:
        >>> report = MonthlySummaryReport()
        >>> report.generate_report()
    """

    def __init__(self, zaptec_api: ZaptecApi):
        self.zaptec_api = zaptec_api
        self.logger = setup_logger()
        self.email_service = EmailService()
        self.month_name: Optional[str] = None

    def generate_report(self) -> None:
        try:
            data = self.get_data_for_report()
            df = self.generate_summary_report(data)
            self.send_report(df)
        except Exception as e:
            handle_error(e, self.logger, self.email_service)

    def get_data_for_report(self) -> InstallationReport:
        from_date, to_date, self.month_name = get_previous_month_range(include_z=False)
        self.logger.info(
            f"---Started generating summary report for period: {from_date} - {to_date}"
        )

        # Get data from the zaptec API
        with self.zaptec_api as api:
            report: InstallationReport = api.get_installation_report(
                from_date=from_date, to_date=to_date
            )

        return report

    def generate_summary_report(self, data: InstallationReport) -> pd.DataFrame:
        df = pd.DataFrame(
            [
                {
                    "user_name": report.GroupAsString,
                    "email": report.UserDetails.Email if report.UserDetails else None,
                    "energy": round(number=report.TotalChargeSessionEnergy, ndigits=2),
                    "duration": round(
                        number=report.TotalChargeSessionDuration, ndigits=2
                    ),
                    "sessions": report.TotalChargeSessionCount,
                }
                for report in data.totalUserChargerReportModel
            ]
        )

        # Strip whitespace from user_name column
        df["user_name"] = df["user_name"].str.strip()

        # Add a row for the totals
        totals = {
            "user_name": "TOTAL",
            "email": "-",
            "energy": df["energy"].sum(),
            "duration": df["duration"].sum(),
            "sessions": df["sessions"].sum(),
        }

        # Add the totals row to the DataFrame
        df.loc[len(df)] = totals
        self.logger.info(f"Generated summary report for month: {self.month_name}")
        self.logger.debug(f"Summary DataFrame:\n{df}")

        return df

    def send_report(self, df: pd.DataFrame):
        body = f"<h3>Summering av laddel för {self.month_name}</h3><br/>"
        body += df.to_html(index=False)

        self.email_service.send_summary_report(body, self.month_name)
