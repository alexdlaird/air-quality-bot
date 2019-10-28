import json
import os
import unittest
import urllib.parse as urlparse

import boto3
import responses

from lambdas.aqi_GET import lambda_function as aqi_route
from utils.jsonutils import decimal_default

__author__ = "Alex Laird"
__copyright__ = "Copyright 2018, Alex Laird"
__version__ = "0.1.7"


class TestCase(unittest.TestCase):
    def given_dynamo_table_exists(self):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))

        dynamodb.create_table(
            TableName=os.environ.get("DYNAMODB_AQI_TABLE"),
            KeySchema=[
                {
                    "AttributeName": "PartitionKey",
                    "KeyType": "HASH"
                },
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "PartitionKey",
                    "AttributeType": "S"
                },

            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 1,
                "WriteCapacityUnits": 1
            }
        )

    def given_zip_code_cached(self, last_updated):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))
        table = dynamodb.Table(os.environ.get("DYNAMODB_AQI_TABLE"))

        data = {
            "PartitionKey": "ZipCode:94501",
            "LastUpdated": last_updated,
            "PM2.5": {
                "AQI": 25,
                "Category": {
                    "Name": "Moderate"
                },
                "DateObserved": "2018-11-17",
                "HourObserved": 10,
                "LocalTimeZone": "PST",
                "ParameterName": "PM2.5",
                "ReportingArea": "Oakland",
                "StateCode": "CA"
            },
            "PM10": {
                "AQI": 26,
                "Category": {
                    "Name": "Moderate"
                },
                "DateObserved": "2018-11-17",
                "HourObserved": 10,
                "LocalTimeZone": "PST",
                "ParameterName": "PM10",
                "ReportingArea": "Oakland",
                "StateCode": "CA"
            }
        }

        table.put_item(
            Item=data
        )

        return data

    def given_reporting_area_cached(self, last_updated, zip_code_data=None):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))
        table = dynamodb.Table(os.environ.get("DYNAMODB_AQI_TABLE"))

        data = {
            "PartitionKey": "ReportingArea:Oakland|CA",
            "LastUpdated": last_updated,
            "MapUrl": "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg"
        }
        if zip_code_data is not None:
            data["CachedAQI"] = zip_code_data

        table.put_item(
            Item=data
        )

        return data

    def given_api_routes_mocked(self):
        def _aqi_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            event = {
                "params": {
                    "querystring": {"zipCode": urlparse.parse_qs(parsed.query)["zipCode"][0]},
                },
            }

            return (200, {}, json.dumps(aqi_route.lambda_handler(event, {}), default=decimal_default))

        responses.add_callback(
            responses.GET, "{}/aqi".format(os.environ.get("AIR_QUALITY_API_URL").lower()),
            callback=_aqi_request_callback
        )

    def given_airnow_routes_mocked(self):
        def _airnow_api_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            zip_code = urlparse.parse_qs(parsed.query)["zipCode"][0]

            data = {
                "94501": [{"DateObserved": "2018-12-02 ", "HourObserved": 14, "LocalTimeZone": "PST",
                           "ReportingArea": "Oakland", "StateCode": "CA", "Latitude": 37.8, "Longitude": -122.27,
                           "ParameterName": "PM2.5", "AQI": 15, "Category": {"Number": 1, "Name": "Good"}}],
                "52328": []
            }[zip_code]

            return (200, {}, json.dumps(data))

        def _airnow_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            zip_code = urlparse.parse_qs(parsed.query)["zipcode"][0]

            map_url = {
                "94501": "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg"
            }[zip_code]
            data = "<html><img src=\"{}\" width=\"525\" height=\"400\" border=\"0\" style=\"position:relative\" usemap=\"#CurMap\"/></html>".format(
                map_url)

            return (200, {}, data)

        responses.add_callback(
            responses.GET, "http://www.airnowapi.org/aq/observation/zipCode/current/",
            callback=_airnow_api_request_callback
        )

        responses.add_callback(
            responses.GET, "https://airnow.gov/index.cfm",
            callback=_airnow_request_callback
        )

    def given_airnow_api_server_error(self):
        def _airnow_api_request_callback(request):
            return (500, {}, "Internal Server Error")

        responses.add_callback(
            responses.GET, "http://www.airnowapi.org/aq/observation/zipCode/current/",
            callback=_airnow_api_request_callback
        )

    def given_airnow_api_bad_response(self):
        def _airnow_api_request_callback(request):
            return (200, {}, "<WebServiceError><Message>Invalid API key</Message></WebServiceError>")

        responses.add_callback(
            responses.GET, "http://www.airnowapi.org/aq/observation/zipCode/current/",
            callback=_airnow_api_request_callback
        )

    def verify_dynamo_key_exists(self, key, last_updated=None, changed=False):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))
        table = dynamodb.Table(os.environ.get("DYNAMODB_AQI_TABLE"))
        dynamo_response = table.get_item(
            Key={
                "PartitionKey": key
            }
        )

        self.assertTrue("Item" in dynamo_response)
        if last_updated is not None:
            if changed:
                self.assertNotEqual(last_updated, dynamo_response["Item"]["LastUpdated"])
            else:
                self.assertEqual(last_updated, dynamo_response["Item"]["LastUpdated"])

    def verify_dynamo_key_not_exists(self, key):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))
        table = dynamodb.Table(os.environ.get("DYNAMODB_AQI_TABLE"))
        dynamo_response = table.get_item(
            Key={
                "PartitionKey": key
            }
        )

        self.assertTrue("Item" not in dynamo_response)

    def load_resource(self, filename):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", filename), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        return event
