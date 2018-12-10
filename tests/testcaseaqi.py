import responses

from .testcase import TestCase
from datetime import datetime, timedelta
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

        self.verify_dynamo_key_not_exists("ZipCode:52328")
        self.assertEqual(response, {"errorMessage": "Sorry, AirNow data is unavailable for this zip code."})

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501(self):
        self.given_dynamo_table_exists()
        self.given_airnow_routes_mocked()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501")
        self.verify_dynamo_key_exists("ReportingArea:Oakland|CA")
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("MapUrl" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 15)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")
        self.assertEqual(response["PM2.5"]["MapUrl"], "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501_cached(self):
        self.given_dynamo_table_exists()
        last_updated = datetime.utcnow().isoformat()
        zip_code_data = self.given_zip_code_cached(last_updated)
        self.given_reporting_area_cached(last_updated, zip_code_data)

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501", last_updated)
        self.verify_dynamo_key_exists("ReportingArea:Oakland|CA", last_updated)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("MapUrl" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 25)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")
        self.assertEqual(response["PM2.5"]["MapUrl"], "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501_zip_code_cached_no_map(self):
        self.given_dynamo_table_exists()
        last_updated = datetime.utcnow().isoformat()
        zip_code_data = self.given_zip_code_cached(last_updated)

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501", last_updated)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("MapUrl" not in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 25)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501_zip_code_cache_expired(self):
        self.given_dynamo_table_exists()
        self.given_airnow_routes_mocked()
        last_updated = (datetime.utcnow() - timedelta(hours=1, minutes=1)).isoformat()
        zip_code_data = self.given_zip_code_cached(last_updated)

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501", last_updated, True)
        self.verify_dynamo_key_exists("ReportingArea:Oakland|CA")
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 15)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501_zip_code_cache_expired_request_fails_cache_fallback(self):
        self.given_dynamo_table_exists()
        last_updated = (datetime.utcnow() - timedelta(hours=1, minutes=1)).isoformat()
        zip_code_data = self.given_zip_code_cached(last_updated)

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501", last_updated)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 25)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_94501_zip_code_cache_expired_request_fails_reporting_area_fallback(self):
        self.given_dynamo_table_exists()
        zip_code_last_updated = (datetime.utcnow() - timedelta(hours=1, minutes=1)).isoformat()
        reporting_area_last_updated = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        zip_code_data = self.given_zip_code_cached(zip_code_last_updated)
        zip_code_data["PM2.5"]["AQI"] = 100
        zip_code_data["LastUpdated"] = reporting_area_last_updated
        self.given_reporting_area_cached(reporting_area_last_updated, zip_code_data)

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_exists("ZipCode:94501", zip_code_last_updated)
        self.verify_dynamo_key_exists("ReportingArea:Oakland|CA", reporting_area_last_updated)
        self.assertTrue("PM2.5" in response)
        self.assertTrue("AQI" in response["PM2.5"])
        self.assertTrue("ReportingArea" in response["PM2.5"])
        self.assertEqual(response["PM2.5"]["AQI"], 100)
        self.assertEqual(response["PM2.5"]["ReportingArea"], "Oakland")

    @mock_dynamodb2
    @responses.activate
    def test_aqi_air_now_non_200(self):
        self.given_dynamo_table_exists()
        self.given_airnow_api_server_error()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_not_exists("ZipCode:94501")
        self.assertEqual(response, {"errorMessage": "Oops, something went wrong. AirNow seems overloaded at the moment."})

    @mock_dynamodb2
    @responses.activate
    def test_aqi_air_now_bad_response(self):
        self.given_dynamo_table_exists()
        self.given_airnow_api_bad_response()

        event = {"zipCode": "94501"}

        response = lambda_function.lambda_handler(event, {})

        self.verify_dynamo_key_not_exists("ZipCode:94501")
        self.assertEqual(response, {"errorMessage": "Oops, something went wrong. AirNow seems overloaded at the moment."})

if __name__ == "__main__":
    unittest.main()
