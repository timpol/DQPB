"""
Setup file and console logging

"""

import logging
import logging.handlers
import os

from PyQt5.QtCore import QObject, pyqtSignal


# Warnings logger:
# https://stackoverflow.com/questions/38531786/capturewarnings-set-to-true-doesnt-capture-warnings
logging.captureWarnings(True)
warnings_logger = logging.getLogger("py.warnings")


def setUpLoggers(log_file_path=None):
    """Setup the application loggers."""

    logger = logging.getLogger("dqpb")

    # Set the top level logger to debug, and refine the handlers.
    # https://stackoverflow.com/questions/17668633/what-is-the-point-of-setlevel-in-a-python-logging-handler
    logger.setLevel(logging.DEBUG)

    # Don't pass events logged by this logger to the handlers of the ancestor loggers.
    # logger.propagate = False
    logfmt = "%(asctime)s.%(msecs)03d | %(name)s | %(levelname)s | %(message)s"
    datefmt = "%Y-%m-%d | %H:%M:%S"
    formatter = logging.Formatter(logfmt, datefmt=datefmt)

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    warnings_logger.addHandler(stream_handler)

    # File handler
    log_file = os.path.join(log_file_path, 'DQPB.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=2*10**6,
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    warnings_logger.addHandler(file_handler)

    message = f"writing log to: {log_file}"
    logger.info(message)


class Handler(logging.Handler, QObject):
    """
    Base handler.
    """

    logUpdated = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        logging.Handler.__init__(self)
        # logfmt = "%(asctime)s: %(message)s"
        # datefmt = "%Y-%m-%d | %H:%M:%S"
        # formatter = logging.Formatter(logfmt, datefmt=datefmt)
        # self.setFormatter(formatter)
        # self.setLevel(logging.INFO)

    def emit(self, record):
        message = self.format(record)
        level = record.levelname
        # TODO: find a neater way of doing this...
        self.logUpdated.emit(f'{level}::{message}')


# class StatusBarHandler(Handler):
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#         logfmt = "%(message)s"
#         formatter = logging.Formatter(logfmt)
#         self.setFormatter(formatter)
#         self.setLevel(logging.INFO)


class ConsoleHandler(Handler):
    """
    Console log handler.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        logfmt = "%(asctime)s: %(message)s"
        datefmt = "%Y-%m-%d | %H:%M:%S"
        formatter = logging.Formatter(logfmt, datefmt=datefmt)
        self.setFormatter(formatter)
        self.setLevel(logging.DEBUG)
