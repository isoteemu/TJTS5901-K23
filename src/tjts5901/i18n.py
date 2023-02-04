"""
Internationalisation and localisation support for the application.
"""
from flask_babel import Babel
from babel import Locale
from babel import __version__ as babel_version
from flask import Flask

import logging

logger = logging.getLogger(__name__)


def init_babel(flask_app: Flask):
    """
    Initialize the Flask-Babel extension.
    """

    # Configure the Flask-Babel extension.
    # Try setting the default locale from underlying OS. Falls back into English.
    system_language = Locale.default().language
    flask_app.config.setdefault("BABEL_DEFAULT_LOCALE", system_language)

    # TODO: Set the default timezone from underlying OS.

    babel = Babel(flask_app)

    logger.info("Initialized Flask-Babel extension %s.", babel_version,
                extra=flask_app.config.get_namespace("BABEL_"))
    return babel
