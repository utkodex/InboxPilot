from email_auto.email_sender import EmailSender
from google_sheet.google_sheet import GoogleSheetClient


def send_email():
    email_sender=EmailSender()
    recipient_email= "bizzboosterdata@gmail.com" 
    subject= "Subject check" 
    body= "This is a test email from the EmailSender2 class."

    email_sender.send_email(recipient_email, subject, body)

a=GoogleSheetClient().dataset_to_json()
# logging.info(a["Recipient Email"])

for _ in a:
    print(f'ewp: {_["Recipient Email"]}')