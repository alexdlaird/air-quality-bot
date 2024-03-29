__copyright__ = "Copyright (c) 2018-2019 Alex Laird"
__license__ = "MIT"

import logging
import os
import re
from urllib import parse

import requests
from datadog import datadog_lambda_wrapper

from utils import metricutils
from utils.decoratorutils import conditional_decorator

AIR_QUALITY_API_URL = os.environ.get("AIR_QUALITY_API_URL").lower()

_AQI_MESSAGES = {
    "Good": "Air quality is considered satisfactory, and air pollution poses little or no risk.",
    "Moderate": "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people. For example, people who are unusually sensitive to ozone may experience respiratory symptoms.",
    "Unhealthy for Sensitive Groups": "Although general public is not likely to be affected at this AQI range, people with lung disease, older adults and children are at a greater risk from exposure to ozone, whereas persons with heart and lung disease, older adults and children are at greater risk from the presence of particles in the air.",
    "Unhealthy": "Everyone may begin to experience some adverse health effects, and members of the sensitive groups may experience more serious effects.",
    "Very Unhealthy": "This would trigger a health alert signifying that everyone may experience more serious health effects.",
    "Hazardous": "This would trigger a health warnings of emergency conditions. The entire population is more likely to be affected."
}
_AIR_QUALITY_API_TIMEOUT = 10

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@conditional_decorator(datadog_lambda_wrapper, not os.environ.get("FLASK_APP", None))
def lambda_handler(event, context):
    logger.info(f"Event: {event}")

    query_string = event["params"]["querystring"]
    logger.info(f"Query String: {query_string}")

    metricutils.increment("inbound_POST.request")

    data = parse.parse_qs(event["body-json"])
    phone_number = data["From"][0]
    body = data["Body"][0]

    logger.info(f"Received \"{body}\" from {phone_number}")

    zip_code = body.lower().strip()
    include_map = "map" in zip_code

    # Check to ensure the message is valid (a zip code with an optional "map" at the end)
    if not re.match(r"^\d+(( )?map)?$", zip_code):
        metricutils.increment("inbound_POST.help-response")

        return _get_response(
            "Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.")

    if include_map:
        metricutils.increment("inbound_POST.map-requested")
        logger.info("Map requested")

        zip_code = zip_code.split("map")[0].strip()

    try:
        response = requests.get(f"{AIR_QUALITY_API_URL}/aqi?zipCode={zip_code}",
                                timeout=_AIR_QUALITY_API_TIMEOUT).json()
    except requests.exceptions.RequestException as e:
        metricutils.increment("inbound_POST.error.aqi-request-failed")
        logger.error(e)

        response = {
            "errorMessage": "Oops, an unknown error occurred. AirNow may be overloaded at the moment."
        }

    logger.info(f"Response from `/aqi`: {response}")

    if "errorMessage" in response:
        return _get_response(response["errorMessage"])

    parameter_name = None
    if "PM2.5" in response:
        parameter_name = "PM2.5"
    elif "PM10" in response:
        parameter_name = "PM10"
    elif "O3" in response:
        parameter_name = "O3"

    if parameter_name is None:
        metricutils.increment("inbound_POST.error.no-pm")

        return _get_response("Oops, something went wrong. AirNow seems overloaded at the moment.")
    else:
        # Clean up the time format
        suffix = "PM" if response[parameter_name]["HourObserved"] >= 12 else "AM"
        time = response[parameter_name]["HourObserved"] - 12 if response[parameter_name]["HourObserved"] > 12 else \
            response[parameter_name]["HourObserved"]
        time = str(int(12 if time == "00" else time)) + suffix + " " + response[parameter_name]["LocalTimeZone"]

        msg = "{category_name} AQI of {aqi} {param_name} for {reporting_area} at {time}. {category_name}\nSource: AirNow".format(
            category_name=response[parameter_name]["Category"]["Name"],
            aqi=int(response[parameter_name]["AQI"]),
            param_name=parameter_name,
            reporting_area=response[parameter_name]["ReportingArea"],
            time=time)

        media = None
        if include_map:
            # if "MapUrl" in response[parameter_name]:
            media = "https://gispub.epa.gov/airnow/images/current-pm-ozone.jpg"  # response[parameter_name]["MapUrl"]
            # else:
            #     metricutils.increment("inbound_POST.warn.map-request-failed")
            #     logger.info("Map requested but not included, no MapUrl provided from AirNow")

        return _get_response(msg, media)


def _get_response(msg, media=None):
    media_block = ""
    if media is not None:
        media_block = f"<Media>{media}</Media>"

    xml_response = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>{msg}</Body>{media_block}</Message></Response>"
    logger.info(f"XML response: {xml_response}")

    return {"body": xml_response}
