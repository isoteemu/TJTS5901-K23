"""
Currency module.

This module contains the currency module, which is used to convert currencies.

Uses the ECB (European Central Bank) as the source of currency conversion rates.

To update the currency conversion rates, run the following command:
    $ flask update-currency-rates

"""

from zipfile import ZipFile
import urllib.request
import click
from currency_converter import (
    SINGLE_DAY_ECB_URL,
)

from flask import (
    Flask,
    current_app,
)


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
