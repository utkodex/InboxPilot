from email_auto.email_sender import EmailSender
from email_auto.bounce_checker import BounceChecker
from google_sheet.google_sheet import GoogleSheetClient
from config.config_loader import load_config

from logger import logging
from exception import MyException
import sys
import time
from datetime import datetime

def send_email(recipient_email, subject, body, cc=None, bcc=None, attachments=None):
    email_sender=EmailSender()
    email_sender.send_email(recipient_email, subject, body, cc, bcc, attachments)

def email_data():
    email_data=GoogleSheetClient().dataset_to_json()

    print("*************************************************************")

    # Record the time just before we start sending so bounce checker
    # only looks at replies that arrived after this campaign started.
    campaign_start_time = datetime.now()

    for idx, person in enumerate(email_data):

        length=len(email_data)
        idx = idx + 1
        print(f"Total Emails: {length}, Sending Email: {idx}")

        name = person["Recipient Name"]
        logging.info(f"Person: {name}")
        email = person["Recipient Email"]
        logging.info(f"Email: {email}")
        subject = person["Subject"]
        logging.info(f"Subject: {subject}")
        body = person["Body"]
        logging.info(f"{body}")
        cc = person["CC"]
        logging.info(f"CC: {cc}")
        bcc = person["BCC"]
        logging.info(f"BCC: {bcc}")
        # attachments = None
        attachments = ["./utkarsh_sinha_3yoe_2026.pdf"]
        logging.info(f"CV: {attachments}")

        print("*********************📧")

        logging.info(f"Sending email to: {email}")

        send_email(email, subject, body, cc, bcc, attachments)
        logging.info(f"Mail send To:-----------------------> {email}, Name: {name}, Subject: {subject}")
        print("*************************************************************")

    # ── Bounce Detection ──────────────────────────────────────────────
    config = load_config()
    wait_seconds = config.get("bounce_check", {}).get("wait_seconds", 30)

    print(f"\n⏳ Waiting {wait_seconds}s for bounce-back emails to arrive...")
    logging.info("Waiting %ds before checking for bounced emails.", wait_seconds)
    time.sleep(wait_seconds)

    print("🔍 Checking inbox for bounced / undeliverable emails...")
    checker = BounceChecker()
    bounced = checker.get_bounced_emails(since=campaign_start_time)

    if bounced:
        print(f"⚠️  Bounced emails detected: {bounced}")
        logging.info("Bounced emails detected: %s — adding to block_list.", bounced)
        GoogleSheetClient().add_to_block_list(bounced)
        print(f"✅ {len(bounced)} email(s) added to block_list in Google Sheet.")
    else:
        print("✅ No bounced emails detected.")
        logging.info("No bounced emails detected after campaign.")

if __name__ == "__main__":
    # send_email()
    email_data()
