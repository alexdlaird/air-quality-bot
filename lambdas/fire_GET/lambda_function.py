import logging
import os
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event: {}".format(event))

    # TODO implement
    # https://maps.googleapis.com/maps/api/staticmap?center=94530&zoom=9&size=500x500&maptype=terrain&key=API_KEY
    # https://blog.mapbox.com/mapping-u-s-wildfire-data-from-public-feeds-e0691596a82

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
