# Wildfire Bot

The Wildfire Bot is generally available by texting a zip code (415) 212-4229. The bot will respond with information pertaining to wildfires and air quality.

The instructions below illustrate how to similarly setup the bot in your own AWS and Twilio environments.

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

Create a DynamoDB table with a partition key of `PartitionKey`. Optionally, enable
TTL on the table and tell it to use the `TTL` field.

Install and configure the [AWS CLI](https://docs.aws.amazon.com/lambda/latest/dg/setup-awscli.html).

### AWS API Gateway URL

Create an empty [API Gateway](https://console.aws.amazon.com/apigateway/home?region=us-east-1#/apis)
and deploy it. Note the `Invoke URL` generated for the stage.

### AWS Lambdas

Initialize the deployment environment by running `make` locally, then edit the
`.env` file's `WILDFIRE_API_URL` variable to have the `Invoke URL` from the
API Gateway created above. Also fill in the `AIRNOW_API_KEYS` list with one or
more [AirNow API keys](https://docs.airnowapi.org/).

Create the following Python 3.6 Lambdas using the Role created above:

- `Wildfire_aqi_GET`
- `Wildfire_evacuation_GET`
- `Wildfire_fire_GET`
- `Wildfire_inbound_POST`

Deploy the Lambdas to your AWS environment using the deploy script:

```
./deploy.sh
```

### AWS API Gateway Routes

Navigate back to [the API Gateway](https://console.aws.amazon.com/apigateway/home?region=us-east-1#/apis)
created above. In the API, do the following:

- Create a new "Resource" with a path of `/aqi`
  - Create a new "GET" method with the "Integration type" of "Lambda Function" and point it to the Lambda `Wildfire_aqi_GET`
    - Edit the "GET" method's "Method Request"
      - Change the "Request Validator" to "Validate query string parameters and header"
      - Add a required "URL Query String Parameter" of `zipCode`

Under the "Integration Request" for `/aqi`, under "Mapping Templates" of "Content-Type" of `application/json` with the following template:

```
{
    "zipCode":  "$input.params('zipCode')"
}
```

- Create a new "Resource" with a path of `/evacuation`
  - Create a new "GET" method with the "Integration type" of "Lambda Function" and point it to the Lambda `Wildfire_evacuation_GET`
    - Edit the "GET" method's "Method Request"
      - Change the "Request Validator" to "Validate query string parameters and header"
      - Add a required "URL Query String Parameter" of `zipCode`

Under the "Integration Request" for `/evacuation`, under "Mapping Templates" of "Content-Type" of `application/json` with the following template:

```
{
    "zipCode":  "$input.params('zipCode')"
}
```

- Create a new "Resource" with a path of `/fire`
  - Create a new "GET" method with the "Integration type" of "Lambda Function" and point it to the Lambda `Wildfire_fire_GET`
    - Edit the "GET" method's "Method Request"
      - Change the "Request Validator" to "Validate query string parameters and header"
      - Add a required "URL Query String Parameter" of `zipCode`

Under the "Integration Request" for `/fire`, under "Mapping Templates" of "Content-Type" of `application/json` with the following template:

```
{
    "zipCode":  "$input.params('zipCode')"
}
```

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

Deploy the new API Gateway.

### Setup Twilio

In Twilio, create a phone number and set it up. Under "Messaging", select
"Webhook" for when "A Message Comes In", select "POST", and enter the deployed
API Gateway URL for `/inbound`.

## Deploy Updates

After the initial installation in to your AWS environment, updates to the Lambdas
can easily be redeployed at any time by rerunning the deploy script:

```
./deploy.sh
```
