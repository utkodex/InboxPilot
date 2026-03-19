import gspread
import json
from typing import List, Dict, Any
from datetime import datetime

from logger import logging
from exception import MyException
import sys

from config.config_loader import load_config



# google_sheet_link = config["google_sheet"]["google_sheet_link"]
# credentials_json = config["google_sheet"]["credentials_json"]

# print(google_sheet_link)
# print(credentials_json)

# class GoogleSheetClient:
#     def __init__(self, credentials_json: str, google_sheet_link: str):
#         self.credentials_json = credentials_json
#         self.google_sheet_link = google_sheet_link
#         self.client = None
#         self.sheet = None

#     def authenticate(self):
#         # Authenticate using the service account credentials
#         self.client = gspread.service_account(filename=self.credentials_json)

#     def open_sheet(self):
#         if not self.client:
#             raise Exception("Client not authenticated. Call authenticate() first.")
#         # Open the Google Sheet by URL
#         self.sheet = self.client.open_by_url(self.google_sheet_link)

#     def get_worksheet(self, worksheet_name: str):
#         if not self.sheet:
#             raise Exception("Sheet not opened. Call open_sheet() first.")
#         # Get a specific worksheet by name
#         return self.sheet.worksheet(worksheet_name)

#     def get_all_records(self, worksheet_name: str):
#         worksheet = self.get_worksheet(worksheet_name)
#         return worksheet.get_all_records()
    
class GoogleSheetClient:
    def __init__(self):
        config=load_config()
        self.google_sheet_link = config["google_sheet"]["google_sheet_link"]
        self.credentials_json = config["google_sheet"]["credentials_json"]
        self.google_sheet_subsheet_name = config["google_sheet"]["google_sheet_subsheet_name"]
        self.block_list_subsheet_name = config["google_sheet"].get("block_list_subsheet_name", "block_list")
        
        logging.info("Google Sheet Client initialized with provided configuration.")

    def load_credentials(self):
        try:
            gc = gspread.service_account(filename=self.credentials_json)
            logging.info("Google Sheet credentials loaded successfully.")
            spreadsheet_url = self.google_sheet_link
            logging.info(f"Accessing Google Sheet at URL: {spreadsheet_url}")
            sh = gc.open_by_url(spreadsheet_url)
            logging.info("Google Sheet opened successfully.")
            source_subsheet_title = self.google_sheet_subsheet_name
            logging.info(f"Accessing worksheet: {source_subsheet_title}")
            worksheet = sh.worksheet(source_subsheet_title)
            logging.info("Worksheet accessed successfully.")
            return worksheet
        
        except Exception as e:
            logging.info(e)
            raise MyException(e, sys) from e
        
    def get_records(self):
        try:
            worksheet = self.load_credentials()
            logging.info("Fetching all records from the worksheet.")
            records = worksheet.get_all_values()[1:]
            logging.info(f"Fetched {len(records)} records from the worksheet.")
            return records
        
        except Exception as e:
            logging.info(e)
            raise MyException(e, sys) from e

    def dataset_to_json(self) -> List[Dict[str, Any]]:
        """
        Convert dataset records into a structured JSON-friendly format.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing record details.

        Raises:
            MyException: If an error occurs during record conversion.
        """
        try:
            records = self.get_records()
            logging.info("Starting conversion of records to JSON format.")

            # data: List[Dict[str, Any]] = []
            data = []

            for row in records:
                recipient_email=row[0]
                recipient_name=row[1]
                cc=row[2]
                bcc=row[3]
                subject=row[4]
                body=row[5]

                data.append({   
                    "Recipient Email": recipient_email, 
                    "Recipient Name": recipient_name, 
                    "CC": cc,
                    "BCC": bcc,
                    "Subject": subject, 
                    "Body": body
                    })

            logging.info("Successfully converted %d records to JSON.", len(data))
            return data
        
        except Exception as e:
                logging.error("Failed to convert records to JSON: %s", str(e), exc_info=True)
                raise MyException(e, sys) from e

    def add_to_block_list(self, emails: List[str]) -> None:
        """
        Append bounced / invalid email addresses to the block_list subsheet.
        Creates the worksheet with a header row if it does not already exist.

        :param emails: List of email address strings to block-list.
        """
        if not emails:
            logging.info("add_to_block_list: no emails to add, skipping.")
            return

        try:
            gc = gspread.service_account(filename=self.credentials_json)
            sh = gc.open_by_url(self.google_sheet_link)

            # Get or create the block_list worksheet
            try:
                worksheet = sh.worksheet(self.block_list_subsheet_name)
                logging.info("add_to_block_list: opened existing worksheet '%s'.", self.block_list_subsheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sh.add_worksheet(
                    title=self.block_list_subsheet_name, rows="1000", cols="2"
                )
                worksheet.append_row(["Email", "Blocked At"], value_input_option="RAW")
                logging.info("add_to_block_list: created new worksheet '%s'.", self.block_list_subsheet_name)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = [[email, timestamp] for email in emails]
            worksheet.append_rows(rows, value_input_option="RAW")

            logging.info("add_to_block_list: added %d email(s) to '%s': %s",
                         len(emails), self.block_list_subsheet_name, emails)

        except Exception as e:
            logging.error("add_to_block_list: failed to write block list | %s", str(e), exc_info=True)
            raise MyException(e, sys) from e

if __name__ == "__main__":
    a=GoogleSheetClient().dataset_to_json()
    # logging.info(a["Recipient Email"])

    for _ in a:
        print(_["Recipient Email"])