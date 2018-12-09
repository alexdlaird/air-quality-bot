import responses

from .testcase import TestCase
from moto import mock_dynamodb2
from lambdas.aqi_GET import lambda_function

class TestCaseAQI(TestCase):

    @mock_dynamodb2
    @responses.activate
    def test_aqi_52328(self):
        self.given_dynamo_table_exists()
        self.given_airnow_routes_mocked()

        event = {"zipCode": "52328"}

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"errorMessage": "Sorry, AirNow data is unavailable for this zip code."})

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501(self):
        self.given_dynamo_table_exists()
        self.given_airnow_routes_mocked()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("O3" in response)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("MapUrl" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")
        self.assertEqual(response["PM2.5"]["MapUrl"], "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_air_now_non_200(self):
        self.given_dynamo_table_exists()
        self.given_airnow_api_server_error()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"errorMessage": "Oops, something went wrong. AirNow seems overloaded at the moment."})

    @mock_dynamodb2
    @responses.activate
    def test_aqi_air_now_bad_response(self):
        self.given_dynamo_table_exists()
        self.given_airnow_api_bad_response()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"errorMessage": "Oops, something went wrong. AirNow seems overloaded at the moment."})

    # TODO: add additional tests for cached /failed responses

if __name__ == "__main__":
    unittest.main()
