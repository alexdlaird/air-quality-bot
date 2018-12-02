#!/bin/bash

read_var() {
   VAR=$(grep $1 $2 | xargs)
   IFS="=" read -ra VAR <<< "$VAR"
   echo ${VAR[1]} | sed 's/"/\\"/g'
}

###########################################################
# Initialize environment
###########################################################

AIRNOW_API_KEYS=$(read_var AIRNOW_API_KEYS .env)
WILDFIRE_API_URL=$(read_var WILDFIRE_API_URL .env)
DYNAMODB_ENDPOINT=$(read_var DYNAMODB_ENDPOINT .env)
DYNAMODB_REGION=$(read_var DYNAMODB_REGION .env)
DYNAMODB_AQI_TABLE=$(read_var DYNAMODB_AQI_TABLE .env)

###########################################################
# Cleanup and rebuild artifacts past builds
###########################################################

rm Wildfire_*.zip
zip -X -r -j Wildfire_aqi_GET.zip lambdas/aqi_GET/*
zip -X -r -j Wildfire_evacuation_GET.zip lambdas/evacuation_GET/*
zip -X -r -j Wildfire_fire_GET.zip lambdas/fire_GET/*
zip -X -r -j Wildfire_inbound_POST.zip lambdas/inbound_POST/*

###########################################################
# Deploy
###########################################################

LAMBDA_NAME=Wildfire_aqi_GET
LAMBDA_TIMEOUT=10
ENV_VARS='{"Variables":{"AIRNOW_API_KEYS":"'$AIRNOW_API_KEYS'","DYNAMODB_ENDPOINT":"'$DYNAMODB_ENDPOINT'","DYNAMODB_REGION":"'$DYNAMODB_REGION'","DYNAMODB_AQI_TABLE":"'$DYNAMODB_AQI_TABLE'"}}'
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_NAME.zip
aws lambda update-function-configuration --function-name $LAMBDA_NAME --timeout $LAMBDA_TIMEOUT --environment $ENV_VARS

LAMBDA_NAME=Wildfire_evacuation_GET
LAMBDA_TIMEOUT=10
ENV_VARS='{"Variables":{}}'
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_NAME.zip
aws lambda update-function-configuration --function-name $LAMBDA_NAME --timeout $LAMBDA_TIMEOUT --environment $ENV_VARS

LAMBDA_NAME=Wildfire_fire_GET
LAMBDA_TIMEOUT=10
ENV_VARS='{"Variables":{}}'
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_NAME.zip
aws lambda update-function-configuration --function-name $LAMBDA_NAME --timeout $LAMBDA_TIMEOUT --environment $ENV_VARS

LAMBDA_NAME=Wildfire_inbound_POST
LAMBDA_TIMEOUT=15
ENV_VARS='{"Variables":{"WILDFIRE_API_URL":"'$WILDFIRE_API_URL'"}}'
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_NAME.zip
aws lambda update-function-configuration --function-name $LAMBDA_NAME --timeout $LAMBDA_TIMEOUT --environment $ENV_VARS
