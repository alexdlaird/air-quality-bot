import logging
import os
import re
import requests

from urllib import parse

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

def lambda_handler(event, context):
    logger.info("Event: {}".format(event))

    data = parse.parse_qs(event["body-json"])
    phone_number = data["From"][0]
    body = data["Body"][0]

    logger.info("Received '{}' from {}".format(body, phone_number))

    zip_code = body.lower().strip()
    include_map = "map" in zip_code

	# Check to ensure the message is valid (a zip code with an optional "map" at the end)
    if not re.match(r"^\d+(( )?map)?$", zip_code):
        return _get_response("Send us a zip code and we'll reply with the area's Air Quality Index (AQI). Put \"map\" at the end and we'll include the regional map too.")

    if include_map:
        logger.info("Map requested")

        zip_code = zip_code.split("map")[0].strip()

    try:
        response = requests.get("{}/aqi?zipCode={}".format(AIR_QUALITY_API_URL, zip_code, timeout=_AIR_QUALITY_API_TIMEOUT)).json()
    except requests.exceptions.ConnectionError as e:
        logger.error(e)

        response = {
            "errorMessage": "Oops, an unknown error occurred. AirNow may be overloaded at the moment."
        }

    logger.info("Response from `/aqi`: {}".format(response))

    if "errorMessage" in response:
        return _get_response(response["errorMessage"])

    parameter_name = None
    if "PM2.5" in response:
        parameter_name = "PM2.5"
    elif "PM10" in response:
        parameter_name = "PM10"

    if parameter_name is None:
        return _get_response("Oops, something went wrong. AirNow seems overloaded at the moment.")
    else:
        # Clean up the time format
        suffix = "PM" if response[parameter_name]["HourObserved"] >= 12 else "AM"
        time = response[parameter_name]["HourObserved"] - 12 if response[parameter_name]["HourObserved"] > 12 else response[parameter_name]["HourObserved"]
        time = str(int(12 if time == "00" else time)) + suffix + " " + response[parameter_name]["LocalTimeZone"]

        msg = "{} AQI of {} {} for {} at {}. {}\nSource: AirNow".format(response[parameter_name]["Category"]["Name"], int(response[parameter_name]["AQI"]), parameter_name, response[parameter_name]["ReportingArea"], time, _AQI_MESSAGES[response[parameter_name]["Category"]["Name"]])

        media = None
        if include_map:
            if "MapUrl" in response[parameter_name]:
                media = response[parameter_name]["MapUrl"]
            else:
                logger.info("Map requested but not included, no MapUrl provided from AirNow")

        return _get_response(msg, media)

def _get_response(msg, media=None):
    media_block = ""
    if media is not None:
        media_block = "<Media>{}</Media>".format(media)

    xml_response = "<?xml version='1.0' encoding='UTF-8'?><Response><Message><Body>{}</Body>{}</Message></Response>".format(msg, media_block)
    logger.info("XML response: {}".format(xml_response))

    return {"body": xml_response}
