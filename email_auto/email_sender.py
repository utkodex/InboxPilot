import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication  # ✅ for attachments
import logging
import logger
from dotenv import load_dotenv
import os

logger = logging.getLogger("EmailApp")  # pick the named logger

class EmailSender:
    def __init__(self):
        """
        Initialize the EmailSender with environment variables.
        """
        self._load_env_variables()

    def _load_env_variables(self):
        """
        Load and validate required environment variables.
        """
        load_dotenv()

        required_vars = ['SENDER_EMAIL', 'SENDER_PASS']

        missing_vars = [var for var in required_vars if os.getenv(var) is None]

        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {missing_vars}")
        
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_pass = os.getenv('SENDER_PASS')

    def send_email(self, recipient_email, subject, body, cc=None, bcc=None, attachments=None):
        """
        Send an email using the SMTP protocol.

        :param recipient_email: Email address of the recipient.
        :param subject: Subject of the email.
        :param body: Body content of the email.
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email

        # Handle single or multiple "To" (including comma-separated string from sheet)
        if isinstance(recipient_email, str):
            recipient_email = [addr.strip() for addr in recipient_email.split(",") if addr.strip()]
        msg['To'] = ", ".join(recipient_email)


        # Handle CC (including comma-separated string from sheet)
        if cc:
            if isinstance(cc, str):
                cc = [addr.strip() for addr in cc.split(",") if addr.strip()]
            msg['Cc'] = ", ".join(cc)
        else:
            cc = []

        # Handle BCC (not added to headers, including comma-separated string from sheet)
        if bcc:
            if isinstance(bcc, str):
                bcc = [addr.strip() for addr in bcc.split(",") if addr.strip()]
        else:
            bcc = []


        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # ✅ Handle attachments
        if attachments:
            if isinstance(attachments, str):
                attachments = [attachments]
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
                    logger.info("Attached file: %s", file_path)
                except Exception as e:
                    logger.error("Failed to attach file %s | Error: %s", file_path, str(e))
                    raise

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_pass)
                # Must send to all: To + CC + BCC
                all_recipients = recipient_email + cc + bcc
                server.sendmail(self.sender_email, all_recipients, msg.as_string())
            logger.info("Email sent to: %s (CC: %s, BCC: %s)", recipient_email, cc, bcc)
        except Exception as e:
            logger.error("Email not sent | Error: %s", str(e))
            raise






if __name__ == "__main__":
    a=EmailSender()
    recipient_email= "bizzboosterdata@gmail.com" 
    subject= "Subject check" 
    body= "This is a test email from the EmailSender2 class. added bcc"
    cc = ["bballb040121503516@gmail.com"]
    bcc = "bballb040121503516@gmail.com"
    attachments = ["./Utkarsh Sinha CV.pdf"]  # ✅ Path to your PDF file
    
    a.send_email(recipient_email, subject, body, cc, bcc, attachments)