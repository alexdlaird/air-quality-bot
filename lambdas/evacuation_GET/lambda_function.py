import logging
import os
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event: {}".format(event))

    # TODO implement

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
