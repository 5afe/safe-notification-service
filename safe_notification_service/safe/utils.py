import logging
from gunicorn import glogging


class IgnoreCheckUrl(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return not ('GET /check/' in message and '200' in message)


class CustomGunicornLogger(glogging.Logger):
    def setup(self, cfg):
        super().setup(cfg)

        # Add filters to Gunicorn logger
        logger = logging.getLogger("gunicorn.access")
        logger.addFilter(IgnoreCheckUrl())

