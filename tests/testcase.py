import unittest
import os
import boto3
import responses
import json
import urllib.parse as urlparse
import decimal

from moto import mock_dynamodb2
from lambdas.aqi_GET import lambda_function as aqi_route

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class TestCase(unittest.TestCase):

    def given_dynamo_table_exists(self):
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
                "94501": [{"DateObserved":"2018-12-02 ","HourObserved":14,"LocalTimeZone":"PST","ReportingArea":"Oakland","StateCode":"CA","Latitude":37.8,"Longitude":-122.27,"ParameterName":"O3","AQI":30,"Category":{"Number":1,"Name":"Good"}},{"DateObserved":"2018-12-02 ","HourObserved":14,"LocalTimeZone":"PST","ReportingArea":"Oakland","StateCode":"CA","Latitude":37.8,"Longitude":-122.27,"ParameterName":"PM2.5","AQI":15,"Category":{"Number":1,"Name":"Good"}}],
                "52328": []
            }[zip_code]

            return (200, {}, json.dumps(data))

        def _airnow_request_callback(request):
            parsed = urlparse.urlparse(request.url)
            zip_code = urlparse.parse_qs(parsed.query)["zipcode"][0]

            map_url = {
                "94501": "https://files.airnowtech.org/airnow/today/cur_aqi_sanfrancisco_ca.jpg"
            }[zip_code]
            data = "<html><img src=\"{}\" width=\"525\" height=\"400\" border=\"0\" style=\"position:relative\" usemap=\"#CurMap\"/></html>".format(map_url)

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

    def load_resource(self, filename):
        example_file = open(os.path.join(os.path.dirname(__file__), "resources", filename), "rb")
        json_str = example_file.read().decode("utf-8")
        event = json.loads(json_str)
        example_file.close()

        return event
