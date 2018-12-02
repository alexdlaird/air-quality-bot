[![Build Status](https://travis-ci.org/alexdlaird/wildfire-bot.svg?branch=master)](https://travis-ci.org/alexdlaird/wildfire-bot)


# Wildfire Bot

The Wildfire Bot is generally available by texting a zip code (415) 212-4229. The
bot will respond with information pertaining to wildfires and air quality.

The instructions below illustrate how to similarly setup the bot in your own
AWS and Twilio environments.

## Getting Started

### AWS Initial Setup

Create a new Role from a Policy with the following permissions:

```
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
below and update the `WILDFIRE_API_URL` variable to point to the deployed endpoint.

Deploy the Lambdas to your AWS environment using the deploy script:

```
./deploy.sh
```

Optionally, TTL for `ZipCode` fields in the DynamoDB table can be enabled by going
to [the AWS console](https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:)
and enabling TTL on the `TTL` field.

### AWS API Gateway Routes

Create an [API Gateway](https://console.aws.amazon.com/apigateway/home?region=us-east-1#/apis).
In the API, do the following:

- Create a new "Resource" with a path of `/inbound`
  - Create a new "POST" method with the "Integration type" of "Lambda Function" and point it to the Lambda `Wildfire_inbound_POST`
    - Edit the "POST" method's "Integration Request"
      - Under "Mapping Templates", add a "Content-Type" of `application/x-www-form-urlencoded` using the "General template" of "Method Request Passthrough"
    - Edit the "POST" method's "Method Response"
      - Edit the `200` response so it has a "Content type" of `application/xml`

Last, under the "Integration Response" for `/inbound`, edit the `200` response. Under "Mapping Templates" of "Content-Type" of `application/xml` with the following template:

```
#set($inputRoot = $input.path('$'))
$inputRoot.body
```

Additionally, create the following "Resource" paths:

- `/aqi`
- `/fire`
- `/evacuate`

Under each of the above, do the following:

- Create a new "GET" method with the "Integration type" of "Lambda Function" and point it to the Lambda `Wildfire_<ROUTE_NAME>_GET`, where <ROUTE_NAME> corresponds to the name of the Lambda we created
to execute on this method
  - Edit the "GET" method's "Method Request"
    - Change the "Request Validator" to "Validate query string parameters and header"
    - Add a required "URL Query String Parameter" of `zipCode`

Under the "Integration Request", under "Mapping Templates" of "Content-Type" of `application/json`,
put the following template:

```
{
    "zipCode":  "$input.params('zipCode')"
}
```

Deploy the new API Gateway. Note the newly generated `Invoke URL` and update the
`WILDFIRE_API_URL` variable in `.env`, then redeploy your Lambdas by running
`./deploy.sh` again.

### Setup Twilio

In Twilio, create a phone number and set it up. Under "Messaging", select
"Webhook" for when "A Message Comes In", select "POST", and enter the deployed
API Gateway URL for `/inbound`.

That's it! Your bot is now setup and ready to respond to texts.

## Deploy Updates

After the initial installation in to your AWS environment, updates to the Lambdas
can easily be redeployed at any time by rerunning the deploy script:

```
./deploy.sh
```
