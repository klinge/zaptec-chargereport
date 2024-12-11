from src.api.zaptec_api import ZaptecApi
from src.models.zaptec_models import ChargingSessionResponse
from src.services.email_service import EmailService
from src.utils.logger import setup_logger
from src.utils.dateutils import get_previous_month_range
from src.utils.error_handler import handle_error
from datetime import datetime
import pandas as pd
import os


class InvoicingReport:
    """A class for generating and managing charging session reports for electric vehicle charging stations.

    This class handles the complete workflow of generating invoicing reports from Zaptec charging
    sessions, including data retrieval, processing, and distribution via email. It supports
    separate reporting for different housing associations.

    Attributes:
        report_dir (str): Directory path where report files will be stored
        logger: Configured logger instance for tracking operations
        report_file (str): Full path to the generated report file
        email_service (EmailService): Service instance for handling email operations

    Environment Variables Required:
        DATA_DIR: Base directory for data storage (defaults to "data")
        CHARGING_TARIFF: Price per kWh for charging sessions
        REPORT_FILE: Base name for the report file (defaults to "charge_report")

    The report generation process includes:
        1. Retrieving charging session data from Zaptec API
        2. Processing and aggregating charging data per user
        3. Calculating costs based on configured tariffs
        4. Generating separate CSV reports for different housing associations
        5. Distributing reports via email

    Example usage:
        >>> report = InvoicingReport()
        >>> report.generate_report()
    """

    def __init__(self):
        data_dir = os.getenv("DATA_DIR", "data")
        self.report_dir = data_dir + "/reports"
        self.logger = setup_logger()
        self.report_file = self.report_dir + "/" + self._generate_report_filename()
        self.email_service = EmailService()

    def generate_report(self):
        """Main method to generate and send the invoicing report"""
        try:
            # Set report date to first and last day of previous month
            from_date, to_date, month_name = get_previous_month_range(include_z=True)
            from_date_no_z, to_date_no_z, month_name = get_previous_month_range(
                include_z=False
            )
            self.logger.info(
                f"---Started generating invoicing report for period: {from_date} - {to_date}"
            )
            # Get data from the zaptec API
            with ZaptecApi() as api:
                sessions = api.get_charging_sessions(from_date, to_date)
            # Put all sessions in a dataframe and sum them per user
            summary_df = self.process_charging_data(
                sessions, from_date_no_z, to_date_no_z
            )
            # Export the summary to csv files
            self.export_to_csv(summary_df, filename=self.report_file)
            # Send the csv files as email attachments
            self.email_service.send_charge_report(
                self.report_file,
                from_date_no_z.split("T")[0],
                to_date_no_z.split("T")[0],
            )

        except Exception as e:
            handle_error(e, self.logger, self.email_service)

    def process_charging_data(
        self, sessions: ChargingSessionResponse, from_date_no_z: str, to_date_no_z: str
    ) -> pd.DataFrame:
        """
        Processes raw charging session data into a formatted DataFrame for reporting.

        Args:
            sessions: Raw charging session data from Zaptec API
            from_date_no_z: Start date without timezone in format YYYY-MM-DD
            to_date_no_z: End date without timezone in format YYYY-MM-DD

        Returns:
            DataFrame: containing aggregated charging data per user with costs
        """
        df = pd.DataFrame(
            [
                {
                    "user_email": session.UserEmail,
                    "user_name": session.UserFullName,
                    "user_id": session.UserId,
                    "device_name": session.DeviceName,
                    "energy": session.Energy,
                    "duration": self._calculate_duration_hours(
                        session.StartDateTime, session.EndDateTime
                    ),
                }
                for session in sessions.Data
            ]
        )

        self.logger.info(f"Processed {len(df)} charging sessions")

        # Group and aggregate data
        summary_df = (
            df.groupby("user_email")
            .agg(
                {
                    "energy": "sum",
                    "duration": "sum",
                    "user_name": "first",
                    "user_id": "first",
                    "device_name": lambda x: list(set(x)),
                }
            )
            .reset_index()
        )

        # Format final output
        TARIFF = float(os.getenv("CHARGING_TARIFF"))
        if TARIFF is None:
            raise ValueError("CHARGING_TARIFF environment variable is not set")

        result_df = pd.DataFrame(
            {
                "Objekt-ID": summary_df["device_name"].apply(
                    lambda x: self._format_objekt_id(x[0])
                ),
                "Fr.o.m. datum": from_date_no_z.split("T")[0],
                "T.o.m. datum": to_date_no_z.split("T")[0],
                "Typ": "LADDPLATS",
                "Startvärde": 0,
                "Slutvärde": summary_df["energy"],
                "Förbrukning": summary_df["energy"],
                "Kostnad": summary_df["energy"] * TARIFF,
                "Tariff": TARIFF,
                "Enhet": "kWh",
                "Kommentar": summary_df.apply(
                    lambda row: f"{row['user_name']}({row['user_email']}), Total laddtid: {row['duration']}",
                    axis=1,
                ),
            }
        )
        self.logger.info(f"Created summary dataframe with {len(result_df)} rows")
        return result_df.sort_values("Objekt-ID")

    def export_to_csv(self, df: pd.DataFrame, filename="charge-report.csv") -> None:
        """
        Exports charging data to CSV files, splitting data between different housing associations.

        Args:
            df: DataFrame containing the charge report data
            filename: Target filename for the CSV export
        """
        # Format numeric columns
        df[["Slutvärde", "Förbrukning", "Kostnad", "Tariff"]] = df[
            ["Slutvärde", "Förbrukning", "Kostnad", "Tariff"]
        ].round(2)

        # Make csv report for BRF Signalen
        try:
            # Make sure the reports directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            # Filter out rows for BRF Signalen based on parking lot numbers
            df_signalen = df[~df["Objekt-ID"].between("G5048", "G5062")]
            df_signalen.to_csv(
                path_or_buf=filename, sep=";", index=False, encoding="utf-8"
            )
            self.logger.info(f"Exported csv file: {filename}")
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to write CSV file {filename}: {str(e)}")
            raise

        # Filter out rows for BRF Bäcken and export to csv
        df_backen = df[df["Objekt-ID"].between("G5048", "G5062")]
        try:
            filename_backen = f"{self.report_dir}/laddstolpar_backen_{datetime.now().strftime('%Y%m%d')}.csv"
            df_backen.to_csv(
                path_or_buf=filename_backen, sep=";", index=False, encoding="utf-8"
            )
            self.logger.info(f"Exported csv file: {filename_backen}")
        except (PermissionError, OSError) as e:
            self.logger.error(msg=f"Failed to write CSV file {filename}: {str(e)}")
            raise

    def _generate_report_filename(self):
        return f"{os.getenv('REPORT_FILE', 'charge_report')}_{datetime.now().strftime('%Y%m%d')}.csv"

    def _calculate_duration_hours(self, start: str, end: str):
        """
        Calculates charging duration in hours between two timestamps.

        Args:
            start: Start timestamp of charging session
            end: End timestamp of charging session

        Returns:
            Float representing duration in hours
        """
        duration = end - start
        return duration.total_seconds() / 3600

    def _format_objekt_id(self, device_name: str) -> str:
        """
        Formats a device name from the Zaptec API into a standardized object ID that is needed for reporting.

        Args:
            device_name: Raw device name from Zaptec (format: "Plats XX")

        Returns:
            Str: Formatted object ID (format: G50XX)
        """
        # Extract the number from "Plats XX"
        number = device_name.split()[1]
        # Pad with leading zeros to ensure 2 digits
        padded_number = number.zfill(2)
        return f"G50{padded_number}"

    def _add_summary_row_for_brf_backen(
        self, df: pd.DataFrame, from_date_no_z: str, to_date_no_z: str
    ) -> pd.DataFrame:
        """
        Sums the power usage on chargers that belong to BRF Bäcken and adds a summary row for BRF Bäcken.
        Currently not used in the report, but could be used in the future.

        Args:
            df: DataFrame containing the charge report data
            from_date_no_z: Start date of the report
            to_date_no_z: End date of the report

        Returns:
            DataFrame: the original dataframe with an additional summary row (G6000) for BRF Bäcken.
        """
        filtered_df = df[df["Objekt-ID"].between("G5048", "G5062")]
        if not filtered_df.empty:
            summary_row = pd.DataFrame(
                {
                    "Objekt-ID": ["G6000"],
                    "Fr.o.m. datum": from_date_no_z.split("T")[0],
                    "T.o.m. datum": to_date_no_z.split("T")[0],
                    "Typ": "LADDPLATS",
                    "Startvärde": 0,
                    "Slutvärde": filtered_df["Slutvärde"].sum(),
                    "Förbrukning": filtered_df["Förbrukning"].sum(),
                    "Kostnad": filtered_df["Kostnad"].sum(),
                    "Tariff": df["Tariff"].iloc[0],
                    "Enhet": "kWh",
                    "Kommentar": "Summering BRF Bäcken, G5048-G5062",
                }
            )
            df = pd.concat([df, summary_row], ignore_index=True)
        return df.sort_values("Objekt-ID")
