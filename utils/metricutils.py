import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log(value, type, metric, tags=[]):
    logger.info("MONITORING|{}|{}|{}|airqualitybot.{}|#{}".format(int(time.time()), value, type, metric, ",".join(tags)))

def increment(metric, tags=[]):
    log(1, "count", metric, tags)
