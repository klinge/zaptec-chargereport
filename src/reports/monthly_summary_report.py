from src.api.zaptec_api import ZaptecApi
from src.models.zaptec_models import InstallationReport
from src.services.email_service import EmailService
from src.utils.logger import setup_logger
from src.utils.dateutils import get_previous_month_range
import pandas as pd
from typing import NoReturn, Optional

class MonthlySummaryReport:
    def __init__(self):
        self.logger = setup_logger()
        self.email_service = EmailService()
        self.month_name: Optional[str] = None
    
    def generate_report(self) -> None:
        data = self.get_data_for_report()
        df = self.generate_summary_report(data)
        self.send_report(df)

    def get_data_for_report(self) -> InstallationReport:
        from_date, to_date, self.month_name = get_previous_month_range(include_z=False)
        self.logger.info(f"---Started generating summary report for period: {from_date} - {to_date}")
        
        #Get data from the zaptec API
        with ZaptecApi() as api:
            report: InstallationReport = api.get_installation_report(from_date=from_date, to_date=to_date)
        
        return report
    
    def generate_summary_report(self, data: InstallationReport) -> pd.DataFrame:     
        df = pd.DataFrame([{
            'user_name': report.GroupAsString,
            'email': report.UserDetails.Email if report.UserDetails else None,
            'energy': round(number=report.TotalChargeSessionEnergy, ndigits=2),
            'duration': round(number=report.TotalChargeSessionDuration, ndigits=2),
            'sessions': report.TotalChargeSessionCount
        } for report in data.totalUserChargerReportModel])
        
        # Strip whitespace from user_name column
        df['user_name'] = df['user_name'].str.strip()

        # Add a row for the totals
        totals = {
            'user_name': 'TOTAL',
            'email': '-',
            'energy': df['energy'].sum(),
            'duration': df['duration'].sum(),
            'sessions': df['sessions'].sum()
        }

        # Add the totals row to the DataFrame
        df.loc[len(df)] = totals
        self.logger.info(f"Generated summary report for month: {self.month_name}")

        return df

    def send_report(self, df: pd.DataFrame):
        body = f"<h3>Summering av laddel för {self.month_name}</h3><br/>"
        body += df.to_html(index=False)
        
        self.email_service.send_summary_report(body, self.month_name)

        self.logger.info(f"Emailed summary report for month: {self.month_name}")


        