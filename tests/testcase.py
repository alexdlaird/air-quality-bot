import unittest
import os
import boto3
import responses
import json
import urllib.parse as urlparse
import decimal

from moto import mock_dynamodb2
from lambdas.aqi_GET import lambda_function as aqi_route
from lambdas.fire_GET import lambda_function as fire_route
from lambdas.evacuation_GET import lambda_function as evacuation_route

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class TestCase(unittest.TestCase):

    def given_dyanmo_table_exists(self):
        dynamodb = boto3.resource("dynamodb", os.environ.get("DYNAMODB_REGION"))

        table = dynamodb.create_table(
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

    def given_api_routes_mocked(self):
        def _aqi_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            event = {
                "zipCode": urlparse.parse_qs(parsed.query)["zipCode"][0]
            }

            print(aqi_route.lambda_handler(event, {}))
            return (200, {}, json.dumps(aqi_route.lambda_handler(event, {}), default=decimal_default))

        def _fire_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            event = {
                "zipCode": urlparse.parse_qs(parsed.query)["zipCode"][0]
            }

            return (200, {}, json.dumps(fire_route.lambda_handler(event, {}), default=decimal_default))

        def _evacuation_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            event = {
                "zipCode": urlparse.parse_qs(parsed.query)["zipCode"][0]
            }

            return (200, {}, json.dumps(evacuation_route.lambda_handler(event, {}), default=decimal_default))

        # TODO: these don't seem to be properly applying yet

        responses.add_passthru("www.airnowapi.org")

        responses.add_callback(
            responses.GET, "{}/aqi".format(os.environ.get("WILDFIRE_API_URL")),
            callback=_aqi_request_callback
        )
        responses.add_callback(
            responses.GET, "{}/fire".format(os.environ.get("WILDFIRE_API_URL")),
            callback=_fire_request_callback
        )
        responses.add_callback(
            responses.GET, "{}/evacuation".format(os.environ.get("WILDFIRE_API_URL")),
            callback=_evacuation_request_callback
        )

    def load_resource(self, filename):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", filename), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        return event
