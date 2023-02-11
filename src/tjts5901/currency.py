"""
Currency module.

This module contains the currency module, which is used to convert currencies.

Uses the ECB (European Central Bank) as the source of currency conversion rates.

To update the currency conversion rates, run the following command:
    $ flask update-currency-rates

"""

import logging
from pathlib import Path
from zipfile import ZipFile
import urllib.request
import click
from currency_converter import (
    SINGLE_DAY_ECB_URL,
    CurrencyConverter,
)

from flask import (
    Flask,
    current_app,
)


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

    app.cli.add_command(update_currency_rates)


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

    fd, _ = urllib.request.urlretrieve(SINGLE_DAY_ECB_URL)
    with ZipFile(fd) as zf:
        file_name = zf.namelist().pop()
        with open(current_app.config['CURRENCY_FILE'], 'wb') as f:
            f.write(zf.read(file_name))

    click.echo('Done.')
