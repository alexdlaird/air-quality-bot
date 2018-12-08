import unittest
import os
import time
import datetime
import pytz

from dotenv import load_dotenv
from twilio.rest import Client

class TestCaseE2E(unittest.TestCase):

    def setUp(self):
        load_dotenv()

        self.client = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))

    def test_text(self):
        now = datetime.datetime.now(pytz.utc)

        self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body="text")

        time.sleep(10)

        latest_message = None
        for message in self.client.messages.list(to=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"), date_sent=now.date()):
            if message.date_sent < now:
                continue

            latest_message = message

        self.assertEqual(latest_message.body, "Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.")

    def test_52328(self):
        now = datetime.datetime.now(pytz.utc)

        self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body="52328")

        time.sleep(10)

        latest_message = None
        for message in self.client.messages.list(to=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"), date_sent=now.date()):
            if message.date_sent < now:
                continue

            latest_message = message

        self.assertEqual(latest_message.body, "Sorry, AirNow data is unavailable for this zip code.")

    def test_94501(self):
        now = datetime.datetime.now(pytz.utc)

        self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body="94501")

        time.sleep(10)

        latest_message = None
        for message in self.client.messages.list(to=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"), date_sent=now.date()):
            if message.date_sent < now:
                continue

            latest_message = message

        self.assertTrue(len(latest_message.media.list()), 0)
        self.assertIn(" AQI of ", latest_message.body)
        self.assertIn(" for Oakland at ", latest_message.body)
        self.assertIn("Source: AirNow", latest_message.body)

    def test_94501_map(self):
        now = datetime.datetime.now(pytz.utc)

        self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body="94501 map")

        time.sleep(10)

        latest_message = None
        for message in self.client.messages.list(to=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"), date_sent=now.date()):
            if message.date_sent < now:
                continue

            latest_message = message

        self.assertTrue(len(latest_message.media.list()), 1)
        self.assertIn(" AQI of ", latest_message.body)
        self.assertIn(" for Oakland at ", latest_message.body)
        self.assertIn("Source: AirNow", latest_message.body)

if __name__ == "__main__":
    unittest.main()
