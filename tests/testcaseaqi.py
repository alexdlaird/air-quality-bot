from .testcase import TestCase
from moto import mock_dynamodb2
from lambdas.aqi_GET import lambda_function

class TestCaseAQI(TestCase):

    def test_aqi_52328(self):
        event = {"zipCode": "52328"}

        response = lambda_function.lambda_handler(event, {})

        self.assertEqual(response, {"errorMessage": "Sorry, AirNow data is unavailable for this zip code."})

    @mock_dynamodb2
    def test_aqi_94501(self):
        self.given_dyanmo_table_exists()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.assertTrue("O3" in response)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("MapUrl" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")
        self.assertEqual(response["PM2.5"]["MapUrl"], "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg")

    # TODO: add additional tests for cached responses

if __name__ == "__main__":
    unittest.main()
