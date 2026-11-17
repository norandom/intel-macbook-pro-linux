"""Repository-wide pyinfra logging preferences."""
import logging

from pyinfra import logger


class _BlockBetaWarningFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage() != "The `files.block` operation is currently in beta!"


logger.addFilter(_BlockBetaWarningFilter())
