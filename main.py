from email_auto.email_sender import EmailSender
from google_sheet.google_sheet import GoogleSheetClient

from logger import logging
from exception import MyException
import sys

def send_email(recipient_email, subject, body, cc=None, bcc=None):
    email_sender=EmailSender()
    email_sender.send_email(recipient_email, subject, body, cc, bcc)

def email_data():
    email_data=GoogleSheetClient().dataset_to_json()

    for person in email_data:
        print("\n")
        name = person["Recipient Name"]
        logging.info(f"Person: {name}")
        email = person["Recipient Email"]
        logging.info(f"Email: {email}")
        subject = person["Subject"]
        logging.info(f"Subject: {subject}")
        body = person["Body"]
        logging.info(f"Body:----->.....")
        cc = person["CC"]
        logging.info(f"CC: {cc}")
        bcc = person["BCC"]
        logging.info(f"BCC: {bcc}")

        print("📧")

        logging.info(f"Sending email to: {email}")

        # send_email(email, subject, body, cc, bcc)
        logging.info(f"Mail send To:-----------------------> {email}, Name: {name}, Subject: {subject}")

        print("\n")
        print("*************************************************************")

if __name__ == "__main__":
    # send_email()
    email_data()