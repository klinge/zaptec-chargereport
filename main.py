from src.reports.invoicing_report import InvoicingReport
from src.reports.monthly_summary_report import MonthlySummaryReport
from dotenv import load_dotenv

def main():
    load_dotenv()

    report = MonthlySummaryReport()
    report.generate_report()

    #report = InvoicingReport()
    #report.generate_report()

    #with ZaptecApi() as api:
    #    result = api.get_installation_report("2024-11-01T00:00:00.000", "2024-11-21T23:59:59.999")
    #print(result)

if __name__ == "__main__":
    main()
