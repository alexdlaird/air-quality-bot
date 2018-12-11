import logging
import time

from datadog import lambda_metric

def increment(metric):
    lambda_metric("airqualitybot.{}".format(metric), 1)
