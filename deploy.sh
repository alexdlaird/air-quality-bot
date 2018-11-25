#!/bin/bash

rm Wildfire_*.zip

zip -X -r -j Wildfire_aqi_GET.zip lambdas/aqi_GET/*
aws lambda update-function-code --function-name Wildfire_aqi_GET --zip-file fileb://Wildfire_aqi_GET.zip

zip -X -r -j Wildfire_evacuation_GET.zip lambdas/evacuation_GET/*
aws lambda update-function-code --function-name Wildfire_evacuation_GET --zip-file fileb://Wildfire_evacuation_GET.zip

zip -X -r -j Wildfire_fire_GET.zip lambdas/fire_GET/*
aws lambda update-function-code --function-name Wildfire_fire_GET --zip-file fileb://Wildfire_fire_GET.zip

zip -X -r -j Wildfire_inbound_POST.zip lambdas/inbound_POST/*
aws lambda update-function-code --function-name Wildfire_inbound_POST --zip-file fileb://Wildfire_inbound_POST.zip
