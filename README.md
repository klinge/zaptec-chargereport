# Zaptec Charge Report Generator

Automated tool for generating and distributing charging reports from Zaptec EV chargers.

## Features
- Fetches charging data from Zaptec API
- Generates summarized reports per user
- Exports data to CSV in a format that is specific to my personal needs
- Automatically emails reports to configured recipients

## Requirements
- Python 3.10+
- Zaptec API credentials
- SMTP server for email distribution

## Configuration
Create a `.env` file with the following variables:
```env
ZAPTEC_USERNAME=your_username
ZAPTEC_PASSWORD=your_password
ZAPTEC_INSTALLATION_ID=your_installation_id
CHARGING_TARIFF=your_charging_tariff(in monetary unit/kWh)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
REPORT_RECIPIENTS=recipient1@example.com,recipient2@example.com
```
Please replace the placeholders with your actual Zaptec credentials, SMTP server details, and report recipients.
The file config.txt contains all the needed settings and can be edited and renamed to .env

## Usage
Run the script using: `python main.py`
