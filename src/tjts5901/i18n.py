"""
Internationalisation and localisation support for the application.
"""
from enum import Enum
from typing import List
from flask_babel import Babel
from babel import Locale
from babel import __version__ as babel_version
from flask import (
    Flask,
    g,
    request,
)

import logging

logger = logging.getLogger(__name__)


class SupportedLocales(Enum):
    """
    Supported locales for the application.

    The values are the locale identifiers used by the Babel library.
    Order here determines the order in which the locales are presented to the
    user, and the order in which the locales are tried when the user does not
    specify a preferred locale.
    """

    FI = "fi_FI.UTF-8"
    "Finnish (Finland)"

    SV = "sv_SE.UTF-8"
    "Swedish (Sweden)"

    EN = "en_GB.UTF-8"
    "English (United Kingdom)"

    # EN_US = "en_US.UTF-8"
    # "English (United States)"


def init_babel(flask_app: Flask):
    """
    Initialize the Flask-Babel extension.
    """

    # Configure the Flask-Babel extension.
    # Try setting the default locale from underlying OS. Falls back into English.
    system_language = Locale.default().language
    flask_app.config.setdefault("BABEL_DEFAULT_LOCALE", system_language)

    # TODO: Set the default timezone from underlying OS.

    babel = Babel(flask_app, locale_selector=get_locale)

    logger.info("Initialized Flask-Babel extension %s.", babel_version,
                extra=flask_app.config.get_namespace("BABEL_"))

    return babel


def get_locale():
    """
    Get the locale for user.

    Looks at the user model for the user's preferred locale. If the user has not
    set a preferred locale, check the browser's Accept-Language header. If the
    browser does not specify a preferred locale, use the default locale.

    todo: What happens if the user's preferred locale support is dropped from
    todo: the application?

    :return: Suitable locale for the user.
    """

    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        logger.debug("Using locale %s from user settings.", user.locale)
        return user.locale

    # otherwise try to guess the language from the user accept header the
    # browser transmits.

    # The Accept-Language header is a list of languages the user prefers,
    # ordered by preference. The first language is the most preferred.
    # The language is specified as a language tag, which is a combination of
    # a language code and a country code, separated by a hyphen.
    # For example, en-GB is English (United Kingdom).
    # The language code is a two-letter code, and the country code is a
    # two-letter code, or a three-digit number. The country code is optional.
    # For example, en is English (no country specified), and en-US is English

    # Convert the Enum of supported locales into a list of language tags.
    # Fancy way: locales_to_try = [locale.value for locale in SupportedLocales]
    locales_to_try: List[str] = list()
    for locale in SupportedLocales:
        locales_to_try.append(str(locale.value))

    # Get the best match for the Accept-Language header.
    locale = request.accept_languages.best_match(locales_to_try)

    logger.debug("Best match for Accept-Language header (%s) is %s.",
                 request.accept_languages, locale)

    return locale
