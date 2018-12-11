import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log(value, type, metric, tags=None):
    if tags is None:
        tags = []
    print("MONITORING|{}|{}|{}|{}|#{}".format(int(time.time()), value, type, "airqualitybot." + metric, ",".join(tags)))

def increment(metric, tags=[]):
    log(1, "count", metric, tags)
