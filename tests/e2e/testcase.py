import logging
import unittest
import os
import time

from twilio.rest import Client

logger = logging.getLogger()

class TestCase(unittest.TestCase):

    def setUp(self):
        self.client = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))

    def await_reply_message(self, now, text, retries = 0):
        if retries >= 5:
            raise TimeoutError("A response from the Air Quality Bot for \"{}\" was not seen after {} retries.".format(text, retries))

        time.sleep(retries * 3 if retries > 0 else 2)

        latest_message = None
        for message in self.client.messages.list(to=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"), date_sent=now.date()):
            if message.direction != "outbound-reply" or  message.date_created <= now:
                continue

            latest_message = message

        if latest_message is None:
            logger.info("Reply message not seen yet, retrying ...")

            self.await_reply_message(now, text, retries + 1)

        return latest_message
