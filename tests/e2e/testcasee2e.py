import unittest
import os

from testcase import TestCase

class TestCaseE2E(TestCase):

    def test_text(self):
        text = "text"

        message = self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body=text)

        message = self.await_reply_message(message.date_created, text)

        self.assertEqual(message.body, "Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.")

    def test_52328(self):
        text = "52328"

        message = self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body=text)

        message = self.await_reply_message(message.date_created, text)

        self.assertEqual(message.body, "Sorry, AirNow data is unavailable for this zip code.")

    def test_94501(self):
        text = "94501"

        message = self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body=text)

        message = self.await_reply_message(message.date_created, text)

        self.assertEqual(message.num_media, '0')
        self.assertIn(" AQI of ", message.body)
        self.assertIn(" for Oakland at ", message.body)
        self.assertIn("Source: AirNow", message.body)

    def test_94501_map(self):
        text = "94501 map"

        message = self.client.messages.create(
            to=os.environ.get("TWILIO_AIR_QUALITY_PHONE_NUMBER"),
            from_=os.environ.get("TWILIO_E2E_FROM_PHONE_NUMBER"),
            body=text)

        message = self.await_reply_message(message.date_created, text)

        self.assertEqual(message.num_media, '1')
        self.assertIn(" AQI of ", message.body)
        self.assertIn(" for Oakland at ", message.body)
        self.assertIn("Source: AirNow", message.body)

if __name__ == "__main__":
    unittest.main()
