from src.api.zaptec_api import ZaptecApi
from src.models.zaptec_models import ChargingSessionResponse
from src.services.email_service import EmailService
from src.utils.logger import setup_logger
from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import os
import traceback

class ChargeReport:
    def __init__(self):
        load_dotenv()
        self.logger = setup_logger()
        self.api = ZaptecApi()
        self.report_file = "data/reports/" + self._generate_report_filename()
        self.email_service = EmailService()
        
    def generate_report(self):
        """Main method to generate and send the charge report"""
        try:
            # Set report date to first and last day of previous month
            from_date, to_date = self._get_date_range()
            from_date_no_z, to_date_no_z = self._get_date_range(include_z=False)
            self.logger.info(f"Started generating monthly charge report for period: {from_date} - {to_date}")
            #Get data from the zaptec API
            sessions = self.api.get_charging_sessions(from_date, to_date)
            #Put all sessions in a dataframe and sum them per user
            summary_df = self.process_charging_data(sessions, from_date_no_z, to_date_no_z)
            #Export the summary to csv files
            self.export_to_csv(summary_df, filename=self.report_file)
            #Send the csv files as email attachments
            self.email_service.send_charge_report(self.report_file, from_date_no_z.split('T')[0], to_date_no_z.split('T')[0])
    
        except Exception as e:
            self._handle_error(e)
            raise

    def process_charging_data(self, sessions: ChargingSessionResponse, from_date_no_z: str, to_date_no_z: str) -> pd.DataFrame:
        ''' Takes data from the API and converts it to a properly formatted DataFrame'''
        df = pd.DataFrame([{
            'user_email': session.UserEmail,
            'user_name': session.UserFullName,
            'user_id': session.UserId,
            'device_name': session.DeviceName,
            'energy': session.Energy,
            'duration': self._calculate_duration_hours(session.StartDateTime, session.EndDateTime)
        } for session in sessions.Data])
        
        # Group and aggregate data
        summary_df = df.groupby('user_email').agg({
            'energy': 'sum',
            'duration': 'sum',
            'user_name': 'first',
            'user_id': 'first',
            'device_name': lambda x: list(set(x))
        }).reset_index()
        
        # Format final output
        TARIFF = float(os.getenv('CHARGING_TARIFF'))
        if TARIFF is None:
            raise ValueError("CHARGING_TARIFF environment variable is not set")
        
        result_df = pd.DataFrame({
            'Objekt-ID': summary_df['device_name'].apply(lambda x: self._format_objekt_id(x[0])),
            'Fr.o.m. datum': from_date_no_z.split('T')[0],
            'T.o.m. datum': to_date_no_z.split('T')[0],
            'Typ': 'LADDPLATS',
            'Startvärde': 0,
            'Slutvärde': summary_df['energy'],
            'Förbrukning': summary_df['energy'],
            'Kostnad': summary_df['energy'] * TARIFF,
            'Tariff': TARIFF,
            'Enhet': 'kWh',
            'Kommentar': summary_df.apply(lambda row: f"{row['user_name']}({row['user_email']}), Total laddtid: {row['duration']}", axis=1)
        })
        self.logger.info(f"Generated dataframe with {len(df)} rows")
        return result_df.sort_values('Objekt-ID')

    def export_to_csv(self, df: pd.DataFrame, filename="charge-report.csv") -> None:        
        # Format numeric columns
        df[['Slutvärde', 'Förbrukning', 'Kostnad', 'Tariff']] = df[['Slutvärde', 'Förbrukning', 'Kostnad', 'Tariff']].round(2)
        try: 
            # Make sure the reports directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            # Filter out rows for BRF Signalen and export to csv
            df_signalen = df[~df['Objekt-ID'].between('G5048', 'G5062')]
            df_signalen.to_csv(filename, sep=';', index=False, encoding='utf-8')
            self.logger.info(f"Exported csv file: {filename}")
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to write CSV file {filename}: {str(e)}")
            raise

        #Filter out rows for BRF Bäcken and export to csv
        df_backen = df[df['Objekt-ID'].between('G5048', 'G5062')]
        try:
            filename_backen = f"data/reports/laddstolpar_backen_{datetime.now().strftime('%Y%m%d')}.csv"
            df_backen.to_csv(filename_backen, sep=';', index=False, encoding='utf-8')
            self.logger.info(f"Exported csv file: {filename_backen}")
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to write CSV file {filename}: {str(e)}")
            raise

    def _generate_report_filename(self):
        return f"{os.getenv('REPORT_FILE', 'charge_report')}_{datetime.now().strftime('%Y%m%d')}.csv"

    def _get_date_range(self, include_z=True):
        # Gets the first and last day of last month
        today = datetime.now()
        first_of_current = today.replace(day=1)
        last_of_previous = first_of_current - timedelta(days=1)
        first_of_previous = last_of_previous.replace(day=1)
        
        suffix = "Z" if include_z else ""
        from_date = first_of_previous.strftime(f"%Y-%m-%dT00:00:00.001{suffix}")
        to_date = last_of_previous.strftime(f"%Y-%m-%dT23:59:59.999{suffix}")
        
        return from_date, to_date

    def _calculate_duration_hours(self, start, end):
        duration = end - start
        return duration.total_seconds() / 3600

    def _format_objekt_id(self, device_name: str) -> str:
        # Extract the number from "Plats XX"
        number = device_name.split()[1]
        # Pad with leading zeros to ensure 2 digits
        padded_number = number.zfill(2)
        return f"G50{padded_number}"

    def _add_summary_row_for_brf_backen(self, df: pd.DataFrame, from_date_no_z: str, to_date_no_z: str) -> pd.DataFrame: 
        ''' NOT USED: Adds a summary row for BRF Bäcken'''
        filtered_df = df[df['Objekt-ID'].between('G5048', 'G5062')]
        if not filtered_df.empty:
            summary_row = pd.DataFrame({
                'Objekt-ID': ['G6000'],
                'Fr.o.m. datum': from_date_no_z.split('T')[0],
                'T.o.m. datum': to_date_no_z.split('T')[0],
                'Typ': 'LADDPLATS',
                'Startvärde': 0,
                'Slutvärde': filtered_df['Slutvärde'].sum(),
                'Förbrukning': filtered_df['Förbrukning'].sum(),
                'Kostnad': filtered_df['Kostnad'].sum(),
                'Tariff': df['Tariff'].iloc[0],
                'Enhet': 'kWh',
                'Kommentar': 'Summering BRF Bäcken, G5048-G5062'
            })
            df = pd.concat([df, summary_row], ignore_index=True)
        return df.sort_values('Objekt-ID')

    def _handle_error(self, error: Exception):
        """Handle any errors that occur during report generation"""
        error_message = f"Error details:\n{str(error)}\n\nTraceback:\n{traceback.format_exc()}"
        try: 
            self.email_service.send_error(error_message)
        except Exception as email_error:
            self.logger.error(f"Failed to send error email: {str(email_error)}")
            self.logger.debug(f"Original error: {error_message}")
