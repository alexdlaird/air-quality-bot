# Wildfire Bot

The Wilfire Bot is generally available by texting a zip code (415) 212-4229. The bot will respond with information pertaining to wildfires and air quality.

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

### AWS Lambdas

Create the following Python 3.6 Lambdas using the Role created above:

- `Wildfire_aqi_GET`
- `Wildfire_evacuation_GET`
- `Wildfire_fire_GET`
- `Wildfire_inbound_POST`

Deploy the Lambdas to your AWS environment using the deploy script:

```
./deploy.sh
```

Once deployed, navigate to [the Lambda console](https://console.aws.amazon.com/lambda/home).

For the `Wildfire_aqi_GET` Lambda, add the following environment variables:

- `DYNAMODB_REGION` (like `us-east-1`)
- `DYNAMODB_ENDPOINT` (like `https://dynamodb.us-east-1.amazonaws.com`)
- `DYNAMODB_TABLE`
- `AIRNOW_API_KEYS` (JSON list of API keys formatted `["0c498778-b1be-4fdd-b25e-3a2b96b04769","d9313cb1-35e5-4aa7-a7d6-6d155ecebb7e"]`)

For the `Wildfire_inbound_POST` Lambda, add the following environment variables:

- `WILDFIRE_AQI_API_URL` (this is the `/aqi` endpoint from the API Gateway you'll create below)
- `WILDFIRE_EVACUATION_API_URL` (this is the `/evacuation` endpoint from the API Gateway you'll create below)
- `WILDFIRE_FIRE_API_URL` (this is the `/fire` endpoint from the API Gateway you'll create below)

### AWS API Gateways

Create a new API Gateway in AWS. In the API, do the following:

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
