__copyright__ = "Copyright (c) 2018-2019 Alex Laird"
__license__ = "MIT"

import unittest

import responses
from moto import mock_dynamodb

from lambdas.inbound_POST import lambda_function
from .testcase import TestCase


class TestCaseInbound(TestCase):
    @mock_dynamodb
    @responses.activate
    def test_inbound_94501(self):
        zip_code = "94501"
        self.given_dynamo_table_exists()
        self.given_api_routes_mocked()
        self.given_airnow_routes_mocked()

        event = self.load_resource(f"inbound_{zip_code}.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" not in response["body"])

    @mock_dynamodb
    @responses.activate
    def test_inbound_94501_map(self):
        zip_code = "94501"
        self.given_dynamo_table_exists()
        self.given_api_routes_mocked()
        self.given_airnow_routes_mocked()

        event = self.load_resource(f"inbound_{zip_code}_map.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("body" in response)
        self.assertTrue("<Response><Message><Body>" in response["body"])
        self.assertTrue("AQI of" in response["body"])
        self.assertTrue("<Media>" in response["body"])

    def test_inbound_text(self):
        event = self.load_resource("inbound_text.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {
            "body": "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.</Body></Message></Response>"})

    @mock_dynamodb
    @responses.activate
    def test_inbound_52328(self):
        zip_code = "52328"
        self.given_dynamo_table_exists()
        self.given_api_routes_mocked()
        self.given_airnow_routes_mocked()

        event = self.load_resource(f"inbound_{zip_code}.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {
            "body": "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>Sorry, AirNow data is unavailable for this zip code.</Body></Message></Response>"})

    @mock_dynamodb
    @responses.activate
    def test_error_message_response(self):
        zip_code = "94501"
        self.given_dynamo_table_exists()

        event = self.load_resource(f"inbound_{zip_code}.json")

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {
            "body": "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>Oops, an unknown error occurred. AirNow may be overloaded at the moment.</Body></Message></Response>"})


if __name__ == "__main__":
    unittest.main()
