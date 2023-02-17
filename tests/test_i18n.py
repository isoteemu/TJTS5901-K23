"""
Translation tests
=================
"""

import os
from typing import List

import pytest
from flask import Flask
from flask_babel import (
    Babel,
    Locale,
    force_locale,
    gettext,
    get_translations,
)
from babel.messages.extract import extract_from_dir

from tjts5901.i18n import SupportedLocales
from tjts5901 import __file__ as pkg_file

@pytest.fixture
def babel(app: Flask):
    """
    Babel translation fixture.

    Returns babel tranlaslation fixture registered in flask app
    """
    with app.app_context():
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


def test_babel_translations(app: Flask, babel: Babel):
    """
    Test that translations exists for test string "Hello, world!". This test
    will fail if the translation is missing for any language.

    This test is not intended to test the translation itself, but rather to
    ensure that the translation exists.

    And if the actual translation for "Hello, world!" is "Hello, world!", then
    the test needs to be updated to use a different test string.
    """

    # For flask_babel to work, we need to run in app context
    with app.app_context():

        # Iterate through all of the languages available.
        languages: List[Locale] = babel.list_translations()
        for locale in languages:
            if locale.language == "en":
                # By default everything should be in english
                continue

            with force_locale(locale):
                assert gettext("Hello, World!") != "Hello, World!", f"Message is not translated for language {locale.language}"


def test_app_language_detection(client, babel):
    """
    Similar to :func:`test_babel_translations`, but uses e2e test client
    to test translations.

    Uses the Accept-Language header to set the language for the request.

    TODO: Write variation that includes the territory code in the Accept-Language header.
    """

    # Iterate through all of the languages available.
    with client.application.app_context():
        languages: List[Locale] = babel.list_translations()

    for locale in languages:
        if locale.language == "en":
            # By default everything should be in english
            continue

        response = client.get('/hello', headers={'Accept-Language': locale.language})
        resp_as_string = response.data.decode('utf-8')
        assert gettext("Hello, World!") == resp_as_string, f"Message is not translated for language {locale.language}"


@pytest.fixture(scope="session")
def app_strings():
    """
    Fixture for extracting strings from the application source code.
    """

    # TODO: Read method_map from config file
    method_map = [
        ('**.py', 'python'),
        ('**/templates/**.html', 'jinja2'),
    ]

    # Collect all of the messages from the source code
    dir_path = os.path.dirname(pkg_file)
    messages = set()
    for msg in extract_from_dir(dir_path, method_map):
        messages.add(msg[2])

    return messages


@pytest.mark.parametrize("locale", SupportedLocales)
def test_app_translation_status(locale, app, babel, app_strings, fail_treshold=0.15):
    """
    Check that the majority of strings in application are translated.

    This test will fail if the percentage of untranslated strings is greater
    than the :param:`fail_treshold`.

    :param fail_treshold:  Acceptable percentile for untraslated strings.
    """
    unique_messages = len(app_strings)

    with app.app_context():
        locale = Locale.parse(locale.value)

        if locale.language == "en":
            # By default everything should be in english
            return

        with force_locale(locale):
            untranslated_messages = 0
            # Get the catalog for the current locale, and check if the extracted message
            # is in the catalog
            catalog = get_translations()._catalog  # pylint: disable=protected-access
            for msg in app_strings:
                # If the message is not in the catalog, then it is untranslated
                if catalog.get(msg, "") == "":
                    untranslated_messages += 1

            # Calculate the percentage of untranslated messages
            untranslated_percent = untranslated_messages / unique_messages

            assert untranslated_percent < fail_treshold, f"Too many untranslated strings for language {locale.language} ({untranslated_percent:.2%})"
