import os
import json
import random
import logging
import boto3
import time
import requests

from decimal import Decimal
from datetime import datetime, timedelta
from dateutil import parser

DYNAMODB_REGION = os.environ.get("DYNAMODB_REGION")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")
DYNAMODB_AQI_TABLE = os.environ.get("DYNAMODB_AQI_TABLE")

AIRNOW_API_KEYS = json.loads(os.environ.get("AIRNOW_API_KEYS"))
AIRNOW_API_URL = os.environ.get("AIRNOW_API_URL", "http://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode={}&distance=25&API_KEY={}")
AIRNOW_URL = os.environ.get("AIRNOW_URL", "https://airnow.gov/index.cfm?action=airnow.local_city&zipcode={}&submit=Go")
AIRNOW_MAP_URL_PREFIX = os.environ.get("AIRNOW_MAP_URL_PREFIX", "https://files.airnowtech.org/airnow/today/")

_AIRNOW_API_TIMEOUT = 2
_AIRNOW_API_RETRIES = 2
_AIRNOW_API_RETRY_DELAY = 2
_AIRNOW_TIMEOUT = 3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION, endpoint_url=DYNAMODB_ENDPOINT)
table = dynamodb.Table(DYNAMODB_AQI_TABLE)

def lambda_handler(event, context):
    logger.info("Event: {}".format(event))

    zip_code = event["zipCode"]

    utc_dt = datetime.utcnow()

    zip_code_data = _get_zip_code_data(zip_code, utc_dt)

    if zip_code_data is not None:
        parameter_name = None
        if "PM2.5" in zip_code_data:
            parameter_name = "PM2.5"
        elif "PM10" in zip_code_data:
            parameter_name = "PM10"

        if parameter_name is None:
            data = {
                "errorMessage": "Sorry, AirNow data is unavailable for this zip code."
            }
        else:
            data = zip_code_data.copy()

            reporting_area_data = _get_reporting_area_data(zip_code_data, parameter_name, utc_dt)

            if reporting_area_data is not None:
                # If the ReportingArea's CachedAQI is more recent than the ZipCode value (i.e. the cache is old and a new
                # request failed), fallback to the ReportArea's cache (assuming it isn't more than a day old)
                if parser.parse(reporting_area_data["LastUpdated"]) > parser.parse(zip_code_data["LastUpdated"]) and \
                        "CachedAQI" in reporting_area_data and \
                        parser.parse(reporting_area_data["CachedAQI"]["LastUpdated"]) < utc_dt + timedelta(hours=24):
                    data = reporting_area_data["CachedAQI"]

                data["MapUrl"] = reporting_area_data["MapUrl"]
            else:
                logger.info("ReportingArea was not cached and failed to query, no map data available")
    else:
        data = {
            "errorMessage": "Oops, something went wrong. AirNow seems overloaded at the moment."
        }

    data.pop("PartitionKey", None)
    data.pop("LastUpdated", None)
    data.pop("TTL", None)

    if "MapUrl" in data:
        for key, value in data.items():
            if key == "MapUrl":
                continue

            value["MapUrl"] = data["MapUrl"]

        data.pop("MapUrl")

    return data

def _get_zip_code_data(zip_code, utc_dt):
    db_zip_read = table.get_item(
        Key={
            "PartitionKey": "ZipCode:{}".format(zip_code)
        }
    )
    logger.info("DynamoDB ZipCode read response: {}".format(db_zip_read))

    data = None
    if "Item" not in db_zip_read or (utc_dt - parser.parse(db_zip_read["Item"]["LastUpdated"])).total_seconds() > 3600:
        if "Item" in db_zip_read:
            logger.info("Cached ZipCode value expired, requesting latest AirNow data")

            # We're still storing off the expired cached value here, in case AirNow is overloaded
            # and our request fails
            data = db_zip_read["Item"]
        else:
            logger.info("No ZipCode value found, querying AirNow for data")

        data = _airnow_api_request(zip_code, utc_dt, data)
    else:
        logger.info("Cached ZipCode value less than an hour old, using that")

        data = db_zip_read["Item"]

    return data

def _airnow_api_request(zip_code, utc_dt, data, retries=0):
    airnow_api_key = random.choice(AIRNOW_API_KEYS)

    logger.info("AirNow API URL: {}".format(AIRNOW_API_URL.format(zip_code, airnow_api_key)))

    try:
        response = requests.get(AIRNOW_API_URL.format(zip_code, airnow_api_key), timeout=_AIRNOW_API_TIMEOUT)

        logger.info("AirNow API response: {}".format(response.text))

        response_json = response.json()

        if response.status_code != 200:
            return data

        # If a cached value already exists, we want to update that instead
        if data is None:
            data = {}

        for parameter in response_json:
            parameter["DateObserved"] = parameter["DateObserved"].strip()
            parameter["Longitude"] = Decimal(str(parameter["Longitude"]))
            parameter["Latitude"] = Decimal(str(parameter["Latitude"]))

            data[parameter["ParameterName"]] = parameter

        data["PartitionKey"] = "ZipCode:{}".format(zip_code)
        data["LastUpdated"] = utc_dt.isoformat()
        data["TTL"] = int((utc_dt + timedelta(hours=24) - datetime.fromtimestamp(0)).total_seconds())

        db_zip_write = table.put_item(
            Item=data
        )
        logger.info("DynamoDB ZipCode write response: {}".format(db_zip_write))
    except requests.exceptions.ConnectionError as e:
        logger.error(e)

        if retries < _AIRNOW_API_RETRIES:
            logger.info("Retrying AirNow request ...")

            time.sleep(_AIRNOW_API_RETRY_DELAY)

            _airnow_api_request(zip_code, utc_dt, data, retries + 1)
        elif data is not None:
            logger.info("AirNow request timed out, falling back to cached value.")
    except ValueError as e:
        logger.error(e)

        logger.info("AirNow returned invalid JSON.")

    return data

def _get_reporting_area_data(zip_code_data, parameter_name, utc_dt):
    db_reporting_area_read = table.get_item(
        Key={
            "PartitionKey": "ReportingArea:{}".format(zip_code_data[parameter_name]["ReportingArea"])
        }
    )
    logger.info("DynamoDB ReportingArea read response: {}".format(db_reporting_area_read))

    data = None
    if "Item" not in db_reporting_area_read or (utc_dt - parser.parse(db_reporting_area_read["Item"]["LastUpdated"])).total_seconds() > 3600:
        if "Item" in db_reporting_area_read and parser.parse(zip_code_data["LastUpdated"]) > parser.parse(db_reporting_area_read["Item"]["LastUpdated"]):
            logger.info("Cached ReportingArea value expired, using latest ZipCode data")

            data = db_reporting_area_read["Item"]

            data["CachedAQI"] = zip_code_data.copy()

            data["LastUpdated"] = utc_dt.isoformat()

            db_reporting_area_update = table.update_item(
                Key={
                  "PartitionKey": "ReportingArea:{}".format(zip_code_data[parameter_name]["ReportingArea"])
                },
                UpdateExpression="set LastUpdated = :dt, CachedAQI = :aqi",
                ExpressionAttributeValues={
                    ":dt": data["LastUpdated"],
                    ":aqi": data["CachedAQI"]
                },
                ReturnValues="UPDATED_NEW"
            )
            logger.info("DynamoDB ReportingArea update response: {}".format(db_reporting_area_update))
        else:
            if "Item" in db_reporting_area_read:
                logger.info("Cached ReportingArea value expired, requesting latest AirNow data")
            else:
                logger.info("No ReportingArea value found, querying AirNow for data")

            try:
                response = requests.get(AIRNOW_URL.format(zip_code_data["PartitionKey"][len("ZipCode") + 1:]), timeout=_AIRNOW_TIMEOUT)

                if AIRNOW_MAP_URL_PREFIX in response.text:
                    map_url = response.text[response.text.find(AIRNOW_MAP_URL_PREFIX):]
                    map_url = map_url[0:map_url.find(".jpg") + 4]

                    data = {}
                    data["MapUrl"] = map_url
                    data["CachedAQI"] = zip_code_data.copy()

                    data["PartitionKey"] = "ReportingArea:{}".format(zip_code_data[parameter_name]["ReportingArea"])
                    data["LastUpdated"] = utc_dt.isoformat()

                    db_reporting_area_write = table.put_item(
                        Item=data
                    )
                    logger.info("DynamoDB ReportingArea write response: {}".format(db_reporting_area_write))
            except requests.exceptions.ConnectionError as e:
                logger.error(e)

                if data is not None:
                    logger.info("AirNow request timed out, falling back to cached value.")
    else:
        logger.info("Cached ReportingArea value less than an hour old, using that")

        data = db_reporting_area_read["Item"]

    logger.info("Response data: {}".format(data))

    return data
