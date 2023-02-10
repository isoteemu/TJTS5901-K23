"""
==============
Logging module
==============

In this module we'll create a new :class:`~Logger` interface, using pythons inbuild :module:`logging` module.
By default flask sends messages to stdout.

To use this module, import it into your application and call :func:`~init_logging` function:
    >>> from tjts5901.logging import init_logging
    >>> init_logging(app)

To use logging in your application, import the logger instance, and use it as follows:
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> logger.info("Hello world!")

"""


import logging
from os import environ

import sentry_sdk
from flask import Flask
from flask.logging import default_handler as flask_handler
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration

from .utils import get_version

def init_logging(app: Flask):
    """
    Integrate our own logging interface into application.

    To bind logger into your application instance use::
        >>> init_logging(app)

    :param app: :class:`~Flask` instance to use as logging basis.
    """

    # Setup own logger instance. Usually you'll see something like
    # >>> logger = logging.getLogger(__name__)
    # where `__name__` reflects the package name, which is usually `"__main__"`,
    # or in this exact case `tjts5901.logging`. I'll rather define static name.
    # To get access to your logger in outside of module scope you can then
    # use the same syntax as follows.
    logger = logging.getLogger("tjts5901")

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

    # Try to get enviroment name from different sources
    if enviroment := environ.get('CI_ENVIRONMENT_NAME'):
        enviroment = enviroment.lower()
    elif app.testing:
        enviroment = "testing"
    elif app.debug:
        enviroment = "development"

    # Populate config with environment variables for sentry logging
    app.config.setdefault('SENTRY_DSN', environ.get('SENTRY_DSN'))
    app.config.setdefault('SENTRY_ENVIRONMENT', enviroment)
    app.config.setdefault('CI_COMMIT_SHA', environ.get('CI_COMMIT_SHA'))

    # Setup sentry logging
    sentry_dsn = app.config.get("SENTRY_DSN")
    release = app.config.get("CI_COMMIT_SHA", get_version() or "dev")
    enviroment = app.config.get("SENTRY_ENVIRONMENT", "production")

    if sentry_dsn:
        sentry = sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                # Flask integration
                FlaskIntegration(),

                # Mongo integration. Mongoengine uses pymongo, so we need to
                # integrate pymongo.
                PyMongoIntegration(),

                # Sentry will automatically pick up the logging module.
                #LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0,

            # Set sentry debug mode to true if flask is running in debug mode.
            #debug=bool(app.debug),

            # By default the SDK will try to use the SENTRY_RELEASE
            # environment variable, or infer a git commit
            # SHA as release, however you may want to set
            # something more human-readable.
            release=release,
            environment=enviroment,
        )

        app.config.setdefault("SENTRY_RELEASE", sentry._client.options["release"])
        logger.info("Sentry logging enabled.", extra={"SENTRY_DSN": sentry_dsn})

    else:
        logger.warning("Sentry DSN not found. Sentry logging disabled.")
