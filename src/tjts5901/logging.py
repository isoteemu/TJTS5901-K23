"""
==============
Logging module
==============

In this module we'll create a new :class:`~Logger` interface, using pythons inbuild :module:`logging` module.
By default flask sends messages to stdout.

TODO: Integrate sentry logging
"""


import logging
from flask import Flask
from flask.logging import default_handler as flask_handler

# Setup own logger instance. Usually you'll see something like
# >>> logger = logging.getLogger(__name__)
# where `__name__` reflects the package name, which is usually `"__main__"`,
# or in this exact case `tjts5901.logging`. I'll rather define static name.
# To get access to your logger in  outside of module scope you can then
# use the same syntax as follows.
logger = logging.getLogger("tjts5901")


def init_logging(app: Flask):
    """
    Integrate our own logging interface into application.

    To bind logger into your application instance use::
        >>> init_logging(app)

    :param app: :class:`~Flask` instance to use as logging basis.
    """

    # If flask is running in debug mode, set our own handler to log also debug
    # messages.
    if app.config.get("DEBUG"):
        logger.setLevel(level=logging.DEBUG)

    # Add flask default logging handler as one of our target handlers.
    # When changes to flask logging handler is made, our logging handler
    # adapts automatically. Logging pipeline:
    # our appcode -> our logger -> flask handler -> ????
    logger.addHandler(flask_handler)

    logger.debug("TJTS5901 Logger initialised.")
