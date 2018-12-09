import unittest
import responses
import lambdas.inbound_POST

from .testcase import TestCase
from moto import mock_dynamodb2
from lambdas.inbound_POST import lambda_function

class TestCaseInbound(TestCase):

    @mock_dynamodb2
    @responses.activate
    def test_inbound_94501(self):
        zip_code = "94501"
        self.given_dynamo_table_exists()
        self.given_api_routes_mocked()
        self.given_airnow_routes_mocked()

        event = self.load_resource("inbound_{}.json".format(zip_code))

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" not in response["body"])

    @mock_dynamodb2
    @responses.activate
    def test_inbound_94501_map(self):
        zip_code = "94501"
        self.given_dynamo_table_exists()
        self.given_api_routes_mocked()
        self.given_airnow_routes_mocked()

        event = self.load_resource("inbound_{}_map.json".format(zip_code))

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" in response["body"])

    def test_inbound_text(self):
        event = self.load_resource("inbound_text.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"body": "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.</Body></Message></Response>"})

if __name__ == "__main__":
    unittest.main()
