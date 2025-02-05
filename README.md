# Zaptec Charge Report Generator

Automated tool for generating and distributing monthly charging reports from Zaptec EV chargers. 
The output data is formatted to my personal requirements, and will need to be  modified to suit other needs. 

The wrapper around the Zaptec api (in 'src/api/) is far from complete but it's pretty general and can be used for other needs. 

## Features
- Simple wrapper around some of the endpoints in the Zaptec API (see `src/api` for more details)
- Fetches charging data from Zaptec API
- Generates summarized reports per user
- Exports data to CSV in a format that is specific to the requirements I have (probably not reusable for other purposes)
- Automatically emails reports to configured recipients

## Requirements
- Python 3.10+
- Zaptec API credentials
- SMTP server credentials for email distribution

## Configuration
- Update the template file EXAMPLE.env with your personal settings. Replace the placeholders with your actual Zaptec credentials, SMTP server details, and report recipients.
- Rename `EXAMPLE.env` to `.env` when done. 

Make sure not to push the .env with your secret settings to a public repo. 

## Usage
Run the script using: `python main.py`
