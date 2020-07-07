import json
import os
import sys
from logging.config import dictConfig
from urllib.parse import urlencode

import boto3
import responses
from dotenv import load_dotenv
from flask import Flask
from flask import request
from moto import mock_dynamodb2
from pyngrok import ngrok
from twilio.rest import Client

from utils.jsonutils import decimal_default

load_dotenv(dotenv_path=".env.dev")

# Mock DynamoDB calls with an in-memory datastore before importing the handlers
mock = mock_dynamodb2()
mock.start()

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

from lambdas.aqi_GET import lambda_function as aqi_route
from lambdas.inbound_POST import lambda_function as inbound_route

__author__ = "Alex Laird"
__copyright__ = "Copyright 2019, Alex Laird"
__version__ = "0.1.8"

LOGGING = {
    "version": 1,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s:%(lineno)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
dictConfig(LOGGING)

USE_NGROK = os.environ.get("WERKZEUG_RUN_MAIN") != "true"

# Initialize the Flask app for a simple web server
app = Flask(__name__)

# Calling mock_dynamodb2() above hijacked the requests library, so using the responses
# library (that moto also used), add passthrus for HTTP requests that should still
# succeed in dev
responses.add_passthru("http://127.0.0.1")
responses.add_passthru("https://api.twilio.com")
responses.add_passthru("http://www.airnowapi.org")
responses.add_passthru("https://airnow.gov")

if USE_NGROK:
    # Get the dev server port (defaults to 5000 for Flask, can be overridden with `--port`
    # when starting the server
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 5000

    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(port)
    print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}/\"".format(public_url, port))

    TWILIO_ACCOUNT_SID = os.environ.get("AIR_QUALITY_DEV_TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN = os.environ.get("AIR_QUALITY_DEV_TWILIO_AUTH_TOKEN", None)
    TWILIO_SMS_NUMBER = os.environ.get("AIR_QUALITY_DEV_TWILIO_SMS_NUMBER", None)

    # Update any base URLs or webhooks to use the public ngrok URL
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_SMS_NUMBER:
        callback_url = "{}/inbound".format(public_url)

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        phone_number_sid = client.incoming_phone_numbers.list(phone_number=TWILIO_SMS_NUMBER)[0].sid
        client.incoming_phone_numbers(phone_number_sid).update(sms_url=callback_url)


###################################################################################
# Above has been initialization of the dev environment, ensuring we have everything
# we need mocked out, in memory, and configured to run the service locally.
#
# Below are our Flask routes, which simply emulate the AWS API Gateway behavior
# of taking a request, parsing it, and passing it as the context to the right
# Lambda function.
###################################################################################


@app.route("/aqi")
def route_aqi():
    event = {
        "zipCode": request.args.get("zipCode")
    }

    return json.dumps(aqi_route.lambda_handler(event, {}), default=decimal_default)


@app.route("/inbound", methods=["POST"])
def route_inbound():
    event = {
        "body-json": urlencode(request.form),
        "params": {
            "path": {},
            "querystring": {},
            "header": {
                "Accept": "*/*",
                "Cache-Control": "max-age=259200",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "127.0.0.1",
                "User-Agent": "TwilioProxy/1.1",
                "X-Amzn-Trace-Id": "Root=XXX",
                "X-Forwarded-For": "10.10.10.10",
                "X-Forwarded-Port": "443",
                "X-Forwarded-Proto": "https",
                "X-Twilio-Signature": "XXX="
            }
        },
        "stage-variables": {},
        "context": {
            "account-id": "",
            "api-id": "XXX",
            "api-key": "",
            "authorizer-principal-id": "",
            "caller": "",
            "cognito-authentication-provider": "",
            "cognito-authentication-type": "",
            "cognito-identity-id": "",
            "cognito-identity-pool-id": "",
            "http-method": "POST",
            "stage": "prod",
            "source-ip": "10.10.10.10",
            "user": "",
            "user-agent": "TwilioProxy/1.1",
            "user-arn": "",
            "request-id": "XXX",
            "resource-id": "XXX",
            "resource-path": "/inbound"
        }
    }

    return inbound_route.lambda_handler(event, {})["body"]
