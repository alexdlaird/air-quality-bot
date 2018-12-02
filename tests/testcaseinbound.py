import unittest
import os
import json
from lambdas.inbound_POST import lambda_function

class TestCaseInbound(unittest.TestCase):

    def test_inbound_94501(self):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", "inbound_94501.json"), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" not in response["body"])

    def test_inbound_94501_map(self):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", "inbound_94501_map.json"), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" in response["body"])

    def test_inbound_text(self):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", "inbound_text.json"), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"body": "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.</Body></Message></Response>"})

if __name__ == "__main__":
    unittest.main()
