from datadog import lambda_metric

__author__ = 'Alex Laird'
__copyright__ = 'Copyright 2018, Alex Laird'
__version__ = '0.1.4'


def increment(metric):
    lambda_metric("airqualitybot.{}".format(metric), 1)
