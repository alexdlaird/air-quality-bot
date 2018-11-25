#!/bin/bash

rm Wildfire*.zip

cd lambda/aqi_GET
zip –X –r ../../Wildfire_aqi_GET.zip *
cd ../..
aws lambda update-function-code --function-name Wildfire_aqi_GET --zip-file fileb://Wildfire_aqi_GET.zip

cd lambda/fire_GET
zip –X –r ../../Wildfire_fire_GET.zip *
cd ../..
aws lambda update-function-code --function-name Wildfire_fire_GET --zip-file fileb://Wildfire_fire_GET.zip

cd lambda/inbound_POST
zip –X –r ../../Wildfire_inbound_POST.zip *
cd ../..
aws lambda update-function-code --function-name Wildfire_inbound_POST --zip-file fileb://Wildfire_inbound_POST.zip
