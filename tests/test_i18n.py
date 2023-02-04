"""
Translation tests
=================
"""

from typing import List

import pytest
from flask import Flask
from flask_babel import (
    Babel,
    Locale,
)

from tjts5901.i18n import SupportedLocales


@pytest.fixture
def babel(app: Flask) -> Babel:
    """
    Babel translation fixture.

    Returns babel tranlaslation fixture registered in flask app
    """
    yield app.extensions['babel'].instance


def test_for_supported_locales(app: Flask, babel: Babel):
    """
    Compare supported locales with locales with translations available.
    """
    with app.app_context():
        languages: List[Locale] = babel.list_translations()

        # Using list comprehension to convert Enum to list of Locales
        # required_languages = [Locale.parse(locale.value) for locale in SupportedLocales]
        required_languages: List[Locale] = list()
        for locale in SupportedLocales:
            required_languages.append(Locale.parse(locale.value))

        for required in required_languages:

            # Skip English, as it is the default language of the application.
            if required.language == 'en':
                continue

            assert required in languages, f"Missing translation for language {required.language}"
