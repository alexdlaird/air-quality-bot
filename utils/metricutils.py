__copyright__ = "Copyright (c) 2018-2019 Alex Laird"
__license__ = "MIT"

from datadog import lambda_metric


def increment(metric):
    lambda_metric(f"airqualitybot.{metric}", 1)
