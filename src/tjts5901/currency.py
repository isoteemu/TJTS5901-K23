"""
Currency module.

This module contains the currency module, which is used to convert currencies.

Uses the ECB (European Central Bank) as the source of currency conversion rates.

To update the currency conversion rates, run the following command:
    $ flask update-currency-rates

"""

from decimal import Decimal
import logging
import os
from pathlib import Path
from zipfile import ZipFile
import urllib.request
import click
from currency_converter import (
    SINGLE_DAY_ECB_URL,
    CurrencyConverter,
)

from flask_babel import (
    get_locale,
    format_currency,
)

from babel.numbers import get_territory_currencies, parse_decimal

from flask import (
    Flask,
    current_app,
    render_template,
)

from markupsafe import Markup

from .auth import current_user


REF_CURRENCY = 'EUR'
"Reference currency for the currency converter."


logger = logging.getLogger(__name__)


class CurrencyProxy:
    """
    Proxy for the currency converter.

    This class is used to proxy the currency converter instance. This is to
    ensure that the currency converter is only initialized when it is actually
    used, and the used conversion list is the most up-to-date.
    """

    def __init__(self, app: Flask):
        self._converter = None
        self._app = app
        self._converter_updated = 0
        self._dataset_updated = 0

    def get_currency_converter(self) -> CurrencyConverter:
        """
        Get a currency converter instance.

        Automatically updates the currency converter if the dataset has been
        updated.

        Exceptions:
            RuntimeError: If the currency file is not configured.
            FileNotFoundError: If the currency file does not exist.

        :return: A currency converter instance.
        """

        if not (conversion_file := self._app.config.get('CURRENCY_FILE')):
            raise RuntimeError('Currency file not configured.')

        # Initialize the currency converter if it has not been initialized yet,
        # or if the dataset has been updated.
        self._dataset_updated = Path(conversion_file).stat().st_mtime
        if self._converter is None or self._dataset_updated > self._converter_updated:
            logger.info("Initializing currency converter with file %s.", conversion_file)
            self._converter = CurrencyConverter(
                currency_file=conversion_file,
                ref_currency=REF_CURRENCY,
            )
            self._converter_updated = self._dataset_updated

        return self._converter

    def __getattr__(self, name):
        """
        Proxy all other attributes to the currency converter.
        """
        return getattr(self.get_currency_converter(), name)


def init_currency(app: Flask):
    """
    Initialize the currency module.

    This function initializes the currency module, and registers the currency
    converter as an extension.

    :param app: The Flask application.
    :return: None
    """

    # Set default currency file path
    app.config.setdefault('CURRENCY_FILE', app.instance_path + '/currency.csv')

    # Register the currency converter as an extension
    app.extensions['currency_converter'] = CurrencyProxy(app)

    # Register the currency converter as a template filter
    app.add_template_filter(format_converted_currency, name='localcurrency')

    app.cli.add_command(update_currency_rates)


def format_converted_currency(value, currency=None, **kwargs):
    """
    Render a currency value in the preferred currency.

    This function renders a currency value in the preferred currency for the
    current locale. If the preferred currency is not the reference currency,
    the value is converted to the preferred currency.
    """

    if currency is None:
        currency = get_preferred_currency()

    # Convert the value to the preferred currency
    local_value = convert_currency(value, currency)

    # Format the value
    html = render_template("money-tag.html",
                           base_amount=format_currency(value, currency=REF_CURRENCY, format_type='name', **kwargs),
                           local_amount=format_currency(local_value, currency=currency, **kwargs))
    return Markup(html)


def convert_currency(value, currency=None, from_currency=REF_CURRENCY):
    """
    Convert a currency value to the preferred currency.

    This function converts a currency value to the preferred currency for the
    current locale. If the preferred currency is not the reference currency,
    the value is converted to the preferred currency.
    """

    if currency != REF_CURRENCY:
        return current_app.extensions['currency_converter'].convert(value, from_currency, currency)

    return value


def convert_from_currency(value, currency) -> Decimal:
    """
    Parses the localized currency value and converts it to the reference currency.
    """

    locale = get_locale()
    amount = parse_decimal(value, locale=locale)

    if currency != REF_CURRENCY:
        amount = Decimal(current_app.extensions['currency_converter'].convert(amount, currency, REF_CURRENCY))

    return amount


def get_currencies():
    """
    Get the list of supported currencies.
    """

    return current_app.extensions['currency_converter'].currencies


def get_preferred_currency():
    """
    Get the preferred currency.

    This function returns the preferred currency for the current locale.

    :return: The preferred currency.
    """

    if current_user.is_authenticated and current_user.currency:
        return str(current_user.currency)

    # Fall back to the default currency for the locale
    if territory := get_locale().territory:
        currency = get_territory_currencies(territory)[0]
        if currency in get_currencies():
            return currency
        else:
            logger.warning("Default currency %s is not supported, falling back to %s.", currency, REF_CURRENCY)

    return REF_CURRENCY


@click.command()
def update_currency_rates():
    """
    Update currency file from the European Central Bank.

    This command is meant to be run from the command line, and is not meant to be
    used in the application:
        $ flask update-currency-rates

    :return: None
    """
    click.echo('Updating currency file from the European Central Bank...')
    fetch_currency_file()
    click.echo('Done.')


def fetch_currency_file():
    """
    Fetch the currency file from the European Central Bank.

    This function fetches the currency file from the European Central Bank, and
    stores it in the configured currency file path.
    """

    from tempfile import NamedTemporaryFile  # pylint: disable=import-outside-toplevel

    fd, _ = urllib.request.urlretrieve(SINGLE_DAY_ECB_URL)
    with ZipFile(fd) as zf:
        file_name = zf.namelist().pop()

        # Create a temporary file to store the currency file, to avoid corrupting
        # the existing file if the download fails, or while writing the file.

        file_path = os.path.dirname(current_app.config['CURRENCY_FILE'])
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        with NamedTemporaryFile(dir=file_path, delete=False) as f:
            f.write(zf.read(file_name))
            f.flush()

            # Move the temporary file to the configured currency file path
            os.rename(f.name, current_app.config['CURRENCY_FILE'])
