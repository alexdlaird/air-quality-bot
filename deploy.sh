#!/bin/bash

read_var() {
   VAR=$(grep $1 $2 | xargs)
   IFS="=" read -ra VAR <<< "$VAR"
   echo ${VAR[1]} | sed 's/"/\\"/g'
}

build() {
  LAMBDA_FOLDER=$1
  LAMBDA_NAME=$2

  mkdir build
  cp -R lambdas/$LAMBDA_FOLDER/* build
  cp -R lib/* build
  cp -R utils build
  cd build
  zip -X -r ../$LAMBDA_NAME.zip *
  cd ..
  rm -rf build
}

deploy() {
  LAMBDA_NAME=$1
  LAMBDA_TIMEOUT=$2
  ENV_VARS=$3

  if aws lambda get-function --function-name $LAMBDA_NAME 2>&1 | grep -q "Function not found"
  then
    aws lambda create-function --function-name $LAMBDA_NAME --runtime python3.6 --role $AWS_ROLE --handler lambda_function.lambda_handler --zip-file fileb://$LAMBDA_NAME.zip
  else
    aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_NAME.zip
  fi
  aws lambda update-function-configuration --function-name $LAMBDA_NAME --timeout $LAMBDA_TIMEOUT --environment $ENV_VARS --layers "arn:aws:lambda:$DYNAMODB_REGION:464622532012:layer:Datadog-Python36-metric:1"
}

###########################################################
# Initialize environment
###########################################################

AWS_ROLE=$(read_var AWS_ROLE .env)
AIRNOW_API_KEYS=$(read_var AIRNOW_API_KEYS .env)
AIR_QUALITY_API_URL=$(read_var AIR_QUALITY_API_URL .env)
DYNAMODB_ENDPOINT=$(read_var DYNAMODB_ENDPOINT .env)
DYNAMODB_REGION=$(read_var DYNAMODB_REGION .env)
DYNAMODB_AQI_TABLE=$(read_var DYNAMODB_AQI_TABLE .env)
DATADOG_API_KEY=$(read_var DATADOG_API_KEY .env)
DATADOG_APP_KEY=$(read_var DATADOG_APP_KEY .env)
TRAVIS_E2E_REPO=$(read_var TRAVIS_E2E_REPO .env)
TRAVIS_ACCESS_TOKEN=$(read_var TRAVIS_ACCESS_TOKEN .env)

###########################################################
# Initialize AWS environment
###########################################################

if ! aws dynamodb list-tables 2>&1 | grep -q "$DYNAMODB_AQI_TABLE"
then
  aws dynamodb create-table --table-name $DYNAMODB_AQI_TABLE --attribute-definitions AttributeName=PartitionKey,AttributeType=S --key-schema AttributeName=PartitionKey,KeyType=HASH --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
  aws dynamodb wait table-exists --table-name $DYNAMODB_AQI_TABLE
fi

###########################################################
# Cleanup and rebuild artifacts past builds
###########################################################

rm AirQuality_*.zip
rm -rf build

LAMBDA_FOLDER=aqi_GET
LAMBDA_NAME=AirQuality_aqi_GET
build $LAMBDA_FOLDER $LAMBDA_NAME

LAMBDA_FOLDER=inbound_POST
LAMBDA_NAME=AirQuality_inbound_POST
build $LAMBDA_FOLDER $LAMBDA_NAME

###########################################################
# Deploy Lambdas
###########################################################

LAMBDA_NAME=AirQuality_aqi_GET
LAMBDA_TIMEOUT=15
ENV_VARS='{"Variables":{"AIRNOW_API_KEYS":"'$AIRNOW_API_KEYS'","DYNAMODB_ENDPOINT":"'$DYNAMODB_ENDPOINT'","DYNAMODB_REGION":"'$DYNAMODB_REGION'","DYNAMODB_AQI_TABLE":"'$DYNAMODB_AQI_TABLE'","DATADOG_API_KEY":"'$DATADOG_API_KEY'","DATADOG_APP_KEY":"'$DATADOG_APP_KEY'"}}'
deploy $LAMBDA_NAME $LAMBDA_TIMEOUT $ENV_VARS

LAMBDA_NAME=AirQuality_inbound_POST
LAMBDA_TIMEOUT=20
ENV_VARS='{"Variables":{"AIR_QUALITY_API_URL":"'$AIR_QUALITY_API_URL'","DATADOG_API_KEY":"'$DATADOG_API_KEY'","DATADOG_APP_KEY":"'$DATADOG_APP_KEY'"}}'
deploy $LAMBDA_NAME $LAMBDA_TIMEOUT $ENV_VARS

###########################################################
# Trigger E2E Tests
###########################################################

if [ ! -z "$TRAVIS_ACCESS_TOKEN" ] && [ ! -z "$TRAVIS_E2E_REPO" ];
then
  body='{
  "request": {
  "branch":"master"
  }}'

  curl -s -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "Travis-API-Version: 3" \
     -H "Authorization: token $TRAVIS_ACCESS_TOKEN" \
     -d "$body" \
     https://api.travis-ci.org/repo/$TRAVIS_E2E_REPO/requests
fi
