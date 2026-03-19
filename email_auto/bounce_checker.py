"""
bounce_checker.py
-----------------
Checks the Gmail INBOX via IMAP for bounce-back / delivery-failure messages
that arrived after a given campaign start time, extracts the failed recipient
addresses, and returns them as a deduplicated list.

Usage (called from main.py after the send loop):
    from email_auto.bounce_checker import BounceChecker
    checker = BounceChecker()
    bounced = checker.get_bounced_emails(since=campaign_start_time)
"""

import imaplib
import email as email_lib
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

logger = logging.getLogger("EmailApp")

# Subjects that Gmail / mail servers use for delivery failures
BOUNCE_SUBJECT_KEYWORDS = [
    "delivery status notification",
    "mail delivery subsystem",
    "undeliverable",
    "delivery failed",
    "failure notice",
    "returned mail",
    "delivery notification",
    "non-deliverable",
    "mailer-daemon",
]

# Regex patterns to pull the failed address out of the bounce body
_FAILED_ADDR_PATTERNS = [
    # RFC 3464 DSN "Final-Recipient" header inside the body
    re.compile(r"final-recipient\s*:.*?;\s*([\w.%+\-]+@[\w.\-]+)", re.IGNORECASE),
    # Plain "failed to:" / "undeliverable to:" style lines
    re.compile(r"(?:failed|undeliverable|delivery\s+to)\s+(?:to\s+)?[:<\s]*([\w.%+\-]+@[\w.\-]+)", re.IGNORECASE),
    # Generic email-looking address anywhere in the bounce body
    re.compile(r"([\w.%+\-]+@[\w.\-]+\.[a-zA-Z]{2,})", re.IGNORECASE),
]


class BounceChecker:
    """
    Connects to Gmail via IMAP and retrieves bounced email addresses
    received after *since* datetime.
    """

    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(self):
        load_dotenv()
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_pass = os.getenv("SENDER_PASS")

        if not self.sender_email or not self.sender_pass:
            raise EnvironmentError("SENDER_EMAIL and SENDER_PASS must be set in .env")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_bounced_emails(self, since: datetime) -> list:
        """
        Return a deduplicated list of email addresses that bounced.

        :param since: Only examine bounce messages received at or after this time.
        :return: List[str] of bounced email addresses (may be empty).
        """
        try:
            mail = self._connect()
            message_ids = self._search_bounce_messages(mail, since)
            bounced = set()

            logger.info("BounceChecker: found %d potential bounce messages.", len(message_ids))

            for msg_id in message_ids:
                failed_addresses = self._extract_failed_addresses(mail, msg_id)
                bounced.update(failed_addresses)

            mail.logout()

            result = list(bounced)
            logger.info("BounceChecker: %d unique bounced address(es): %s", len(result), result)
            return result

        except Exception as e:
            logger.error("BounceChecker: error during bounce check | %s", str(e))
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> imaplib.IMAP4_SSL:
        """Authenticate to Gmail IMAP and select INBOX."""
        mail = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
        mail.login(str(self.sender_email), str(self.sender_pass))
        mail.select("INBOX")
        logger.info("BounceChecker: connected to IMAP INBOX as %s", self.sender_email)
        return mail

    def _search_bounce_messages(self, mail: imaplib.IMAP4_SSL, since: datetime) -> list:
        """
        Search INBOX for bounce messages received on or after *since*.
        Returns a list of message-id byte strings.
        """
        # IMAP date format: DD-Mon-YYYY  (e.g. 19-Mar-2026)
        since_str = since.strftime("%d-%b-%Y")
        all_ids = []

        for keyword in BOUNCE_SUBJECT_KEYWORDS:
            search_criterion = f'(SINCE "{since_str}" SUBJECT "{keyword}")'
            try:
                status, data = mail.search(None, search_criterion)
                if status == "OK" and data and data[0]:
                    ids = data[0].split()
                    all_ids.extend(ids)
            except Exception as e:
                logger.warning("BounceChecker: IMAP search error for '%s': %s", keyword, e)

        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        for mid in all_ids:
            if mid not in seen:
                seen.add(mid)
                unique_ids.append(mid)

        return unique_ids

    def _extract_failed_addresses(self, mail: imaplib.IMAP4_SSL, msg_id: bytes) -> list:
        """
        Fetch a single message and extract failed recipient email address(es).
        Skips our own sender address so we don't block ourselves.
        """
        try:
            msg_id_str = msg_id.decode() if isinstance(msg_id, bytes) else msg_id
            status, msg_data = mail.fetch(msg_id_str, "(RFC822)")
            if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                return []

            raw = msg_data[0][1]
            if not isinstance(raw, (bytes, bytearray)):
                return []
            msg = email_lib.message_from_bytes(raw)

            # Collect all text content from the message
            body_text = self._get_body_text(msg)

            found = []
            for pattern in _FAILED_ADDR_PATTERNS:
                matches = pattern.findall(body_text)
                for addr in matches:
                    addr = addr.strip().lower()
                    sender_lower = (self.sender_email or "").lower()
                    # Exclude our own address and mailer-daemon addresses
                    if addr and addr != sender_lower and "mailer-daemon" not in addr:
                        found.append(addr)
                if found:
                    break  # Stop at the most specific pattern that matched

            return list(set(found))

        except Exception as e:
            logger.warning("BounceChecker: could not parse message %s | %s", msg_id, e)
            return []

    def _get_body_text(self, msg) -> str:
        """Recursively extract plain-text parts from an email message."""
        body = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ("text/plain", "message/delivery-status"):
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body.append(payload.decode("utf-8", errors="replace"))
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body.append(payload.decode("utf-8", errors="replace"))
            except Exception:
                pass
        return "\n".join(body)


if __name__ == "__main__":
    # Quick manual test — run this file directly to check connectivity
    logging.basicConfig(level=logging.INFO)
    checker = BounceChecker()
    test_since = datetime(2026, 3, 19)
    result = checker.get_bounced_emails(since=test_since)
    print("Bounced emails found:", result)
