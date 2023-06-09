"""
Internationalisation and localisation support for the application.
"""
from enum import Enum
import os
from typing import List
from flask_babel import Babel, get_locale as get_babel_locale
from babel import Locale
from babel import __version__ as babel_version
from flask import (
    Flask,
    g,
    request,
    session,
)

from werkzeug.datastructures import LanguageAccept

from flask_login import current_user

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

    TLH = "tlh"
    "Klingon"


TIMEZONES = {
    """
    Timezones for supported locales.

    The values are the timezone identifiers used by the Babel library.
    This approach doesnt work for countries that have multiple timezones, like
    the US.
    """
    "fi_FI": "Europe/Helsinki",
    "sv_SE": "Europe/Stockholm",
    "en_GB": "Europe/London",
    "tlh": "America/New_York",
}

def init_babel(flask_app: Flask):
    """
    Initialize the Flask-Babel extension.
    """

    # Monkeypatch klingon support into babel
    # Klingon reverts to English
    hack_babel_core_to_support_custom_locales({"tlh": "en"})

    # Configure the Flask-Babel extension.
    # Try setting the default locale from underlying OS. Falls back into English.
    system_language = Locale.default().language
    translation_dir = os.path.join(os.path.dirname(__file__), "translations")
    flask_app.config.setdefault("BABEL_TRANSLATION_DIRECTORIES", translation_dir)
    flask_app.config.setdefault("BABEL_DEFAULT_LOCALE", system_language)

    babel = Babel(flask_app, locale_selector=get_locale, timezone_selector=get_timezone)

    # Register `locales` as jinja variable to be used in templates. Uses the
    # `Locale` class from the Babel library, so that the locale names can be
    # translated.
    locales = {}
    for locale in SupportedLocales:
        locales[locale.value] = Locale.parse(locale.value)

    flask_app.jinja_env.globals.update(locales=locales)
    # Register `get_locale` as jinja function to be used in templates
    flask_app.jinja_env.globals.update(get_locale=get_babel_locale)

    # If url contains locale parameter, set it as default in session
    @flask_app.before_request
    def set_locale():
        if request.endpoint != "static":
            if locale := request.args.get('locale'):
                if locale in (str(l) for l in locales.values()):
                    logger.debug("Setting locale %s from URL.", locale)
                    session['locale'] = locale
                else:
                    logger.warning("Locale %s not supported.", locale)

    logger.info("Initialized Flask-Babel extension %s.", babel_version,
                extra=flask_app.config.get_namespace("BABEL_"))

    return babel


def hack_babel_core_to_support_custom_locales(custom_locales: dict):
    """ Hack Babel core to make it support custom locale names

    Based on : https://github.com/python-babel/babel/issues/454

    Patch mechanism provided by @kolypto

    Args:
        custom_locales: Mapping from { custom name => ordinary name }
    """
    from babel.core import get_global

    # In order for Babel to know "en_CUSTOM", we have to hack its database and put our custom
    # locale names there.
    # This database is pickle-loaded from a .dat file and cached, so we only have to do it once.
    db = get_global('likely_subtags')
    for custom_name in custom_locales:
        db[custom_name] = custom_name

    # Also, monkey-patch the exists() and load() functions that load locale data from 'babel/locale-data'
    import babel.localedata

    # Originals
    o_exists, o_load, o_parse_locale = babel.localedata.exists, babel.localedata.load, babel.core.parse_locale

    # Definitions
    def exists(name):
        # Convert custom names to normalized names
        name = custom_locales.get(name, name)
        return o_exists(name)

    def load(name, merge_inherited=True):
        # Convert custom names to normalized names
        original_name = custom_locales.get(name, name)
        l_data = o_load(original_name, merge_inherited)
        l_data['languages']['tlh'] = 'Klingon'

        l_data.update({
            'locale_id': name,
        })
        return l_data

    # Definitions
    def parse_locale(name, sep='_'):
        # Convert custom names to normalized names
        name = custom_locales.get(name, name)
        l_data = o_parse_locale(name, sep)
        return l_data

    # Make sure we do not patch twice
    if o_exists.__module__ != __name__:
        babel.localedata.exists = exists
        babel.localedata.load = load

    # if o_parse_locale.__module__ != __name__:
    #    babel.core.parse_locale = parse_locale

    # See that they actually exist
    for normalized_name in custom_locales.values():
        assert o_exists(normalized_name)


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

    # if a locale was stored in the session, use that
    if locale := session.get('locale'):
        logger.debug("Setting locale %s from session.", locale)
        return locale

    # if a user is logged in, use the locale from the user settings
    if current_user.is_authenticated and current_user.locale:
        logger.debug("Using locale %s from user settings.", current_user.locale)
        return current_user.locale

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


def get_timezone():
    """
    Get the timezone for user.

    Looks at the user model for the user's preferred timezone. If the user has
    not set a preferred timezone, use the default timezone.
    """

    # if a user is logged in, use the timezone from the user settings
    if current_user.is_authenticated and current_user.timezone:
        logger.debug("Using locale %s from user settings.", current_user.timezone)
        return current_user.timezone

    # Try detecting the timezone from the user's locale.
    locale = get_locale()
    choises = [(k, 1) for k in TIMEZONES.keys()]

    # Use the best_match method from the LanguageAccept class to get the best
    # match for the user's locale.
    best_match = LanguageAccept(choises).best_match([locale])
    if best_match:
        logger.debug("Guessing timezone %s from locale %s.", TIMEZONES[best_match], locale)
        return TIMEZONES[best_match]
