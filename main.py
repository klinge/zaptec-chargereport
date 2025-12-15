import os
from src.api.zaptec_api import ZaptecApi
from src.reports.invoicing_report import InvoicingReport
from src.reports.monthly_summary_report import MonthlySummaryReport
from src.utils.logger import setup_logger
from dotenv import load_dotenv, dotenv_values


def main():
    # Load environment variables from .env file
    load_dotenv(override=True)
    # Setup logger
    logger = setup_logger()

    # Store the env variable names that is loaded so we can clean them up later
    env_vars = dotenv_values().keys()
    logger.debug(f"Loaded env vars: {env_vars}")

    with ZaptecApi() as api:
        report = MonthlySummaryReport(zaptec_api=api)
        report.generate_report()

        invoice = InvoicingReport(zaptec_api=api)
        invoice.generate_report()

    # with ZaptecApi() as api:
    #    result = api.get_installation_report("2024-11-01T00:00:00.000", "2024-11-21T23:59:59.999")
    # print(result)
    logger.info("Removing env vars")
    # Clean up the env variables
    for var in env_vars:
        os.environ.pop(var, None)
    logger.info("Done!")


if __name__ == "__main__":
    main()
