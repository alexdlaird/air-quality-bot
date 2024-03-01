<p align="center"><img alt="Air Quality Bot - Text (415) 212-4229" src="https://raw.githubusercontent.com/alexdlaird/air-quality-bot/main/logo.png" /></p>

![Python Versions](https://img.shields.io/badge/python-%203.8%20|%203.9%20|%203.10%20|%203.11%20-blue)
[![Coverage](https://img.shields.io/codecov/c/github/alexdlaird/air-quality-bot)](https://codecov.io/gh/alexdlaird/air-quality-bot)
[![Build](https://img.shields.io/github/actions/workflow/status/alexdlaird/air-quality-bot/build.yml)](https://github.com/alexdlaird/air-quality-bot/actions/workflows/build.yml)
[![GitHub License](https://img.shields.io/github/license/alexdlaird/air-quality-bot)](https://github.com/alexdlaird/air-quality-bot/blob/main/LICENSE)

The Air Quality Bot is generally available by texting a zip code (and optionally
the word "map") to (415) 212-4229. The bot will respond with the latest air
quality report for your region.

The instructions below illustrate how to similarly setup the bot in your own
AWS and Twilio environments.

## Getting Started

### AWS Initial Setup

Create a new Role from a Policy with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "cloudwatch:PutMetricData",
                "dynamodb:CreateTable",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DescribeTable",
                "dynamodb:GetShardIterator",
                "dynamodb:GetRecords",
                "dynamodb:ListStreams",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "*"
        }
    ]
}
```

Install and configure the [AWS CLI](https://docs.aws.amazon.com/lambda/latest/dg/setup-awscli.html)
for the same account for which the Role was created.

### AWS Lambdas

Initialize the deployment environment by running `make install` locally, then
edit the `.env` file's `AWS_ROLE` with the ID of the Role created above and the
`AIRNOW_API_KEYS` list with one or more [AirNow API keys](https://docs.airnowapi.org/).

Note that, on initial deploy, your Lambdas will be pointing to the an endpoint
that does not exist until you complete the `AWS API Gateway Routes` section
below and update the `AIR_QUALITY_API_URL` variable to point to the deployed endpoint.

Deploy the Lambdas to your AWS environment using the deploy script:

```sh
./deploy.sh
```

Optionally, TTL for `ZipCode` fields in the DynamoDB table can be enabled by going
to [the AWS console](https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:)
and enabling TTL on the `TTL` field.

### AWS API Gateway Routes

Create an [API Gateway](https://console.aws.amazon.com/apigateway/home?region=us-east-1#/apis).
In the API, do the following:

- Create a new "Resource" with a path of `/inbound`
  - Create a new "POST" method with the "Integration type" of "Lambda Function" and point it to the Lambda `AirQuality_inbound_POST`
    - Edit the "POST" method's "Integration Request"
      - Under "Mapping Templates", add a "Content-Type" of `application/x-www-form-urlencoded` using the "General template" of "Method Request Passthrough"
    - Edit the "POST" method's "Method Response"
    - Edit the `200` response so it has a "Content type" of `application/xml`

Last, under the "Integration Response" for `/inbound`, edit the `200` response. Under "Mapping Templates" of "Content-Type" of `application/xml` with the following template:

```js
#set($inputRoot = $input.path('$'))
$inputRoot.body
```

Additionally, create the following "Resource" paths:

- `/aqi`

Under each of the above, do the following:

- Create a new "GET" method with the "Integration type" of "Lambda Function" and point it to the Lambda `AirQuality_<ROUTE_NAME>_GET`, where <ROUTE_NAME> corresponds to the name of the Lambda we created
to execute on this method
  - Edit the "GET" method's "Method Request"
    - Change the "Request Validator" to "Validate query string parameters and header"
    - Add a required "URL Query String Parameter" of `zipCode`
    - Edit the "GET" method's "Integration Request"
          - Under "Mapping Templates", add a "Content-Type" of `application/json` using the "General template" of "Method Request Passthrough"

Deploy the new API Gateway. Note the newly generated `Invoke URL` and update the
`AIR_QUALITY_API_URL` variable in `.env`, then redeploy your Lambdas by running
`./deploy.sh` again.

### Setup Twilio

In Twilio, create a phone number and set it up. Under "Messaging", select
"Webhook" for when "A Message Comes In", select "POST", and enter the deployed
API Gateway URL for `/inbound`.

That's it! Your bot is now setup and ready to respond to texts.

## Local Development

To test the bot locally, simple [Flask](https://flask.palletsprojects.com/en/1.1.x) server is included in
`devserver.py`. Ensure proper `dev` values are in `.env.dev`, then execute:

```sh
make run-devserver
```

This will start a server with the appropriate routes and in-memory datastores,
and it will also start a [ngrok](https://ngrok.com/) tunnel using
[pyngrok](https://github.com/alexdlaird/pyngrok) so the bot can be fully tested
end-to-end.

## CI Build

If you would like the project to build for you in a CI system, you may
need to add the following environment variables to the CI's console. Their
actual values do not matter (use dummy values, not real), but certain versions
of the `boto` dependency need them to be present when initializing its
configuration.

- `AWS_ACCESS_KEY_ID`
- `AWS_DEFAULT_REGION`
- `AWS_SECRET_ACCESS_KEY`

## Deploy Updates

After the initial installation in to your AWS environment, updates to the Lambdas
can easily be redeployed at any time by rerunning the deploy script:

```sh
./deploy.sh
```

## Contributing

If you would like to get involved, be sure to review the [Contribution Guide](https://github.com/alexdlaird/air-quality-bot/blob/main/CONTRIBUTING.rst).

Want to contribute financially? If you've found Air Quality Bot useful, [sponsorship](https://github.com/sponsors/alexdlaird) would
also be greatly appreciated!

