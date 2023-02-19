"""
This module contains the APScheduler extension.

This extension is used to schedule background tasks.
"""

from datetime import datetime, timedelta
import logging
from random import randint

from flask_apscheduler import APScheduler
from mongoengine import signals, Q

from .models import Item
from .items import handle_item_closing

logger = logging.getLogger(__name__)

# Having the scheduler as a global variable is not ideal, but it's the easiest
# way to make it accessible.
scheduler = APScheduler()


def init_scheduler(app):
    """
    Initialize the APScheduler extension.

    This function is meant to be called from the create_app() function.
    """

    scheduler.init_app(app)

    # Add a signal handler to schedule a task to close the item when the auction
    # ends.
    signals.post_save.connect(_schedule_item_closing_task, sender=Item)

    # Add a batch task to close expired bids every 15 minutes. This is to ensure
    # that the bids are closed even if the server is restarted.
    scheduler.add_job(trigger='interval', minutes=15,
                      func=_close_items,
                      id='close-items')

    # Add a task to update the currency rates from the European Central Bank every
    # day at random time between 5:00 and 5:59.
    scheduler.add_job(trigger='cron', hour=5, minute=randint(0, 59),
                      func=_update_currency_rates,
                      id='update-currency-rates')

    with app.app_context():
        # Start the scheduler.
        scheduler.start()
        logger.debug('APScheduler started')


    return app


def _handle_item_closing(item_id):
    """
    Handle the closing of an item.

    This function is meant to be run by the APScheduler, and is not meant to be
    called directly.
    """

    with scheduler.app.app_context():
        item = Item.objects.get(id=item_id)
        handle_item_closing(item)


# Even as this is named function, it's used as a closure, so it can access
# the scheduler variable.
def _schedule_item_closing_task(sender, document, **kwargs):  # pylint: disable=unused-argument
    """
    Schedule a task to close the item when the auction ends.

    This function is meant to be connected to the post_save signal of the Item
    model.
    """

    if not document.closes_at:
        # The item does not have an auction end time, so there is no need to
        # schedule a task to close it.
        logger.debug("Not scheduling closing, as item %s does not have an auction end time", document.id)
        return

    if document.closed:
        # The item is already closed, so there is no need to schedule a task to
        # close it.
        return

    logger.debug('Scheduling task to close item %s', document.id)
    scheduler.add_job(
        func=_handle_item_closing,
        args=(document.id,),
        trigger='date',
        run_date=document.closes_at + timedelta(seconds=1),
        id=f'close-item-{document.id}',
    )


def _close_items():
    """
    Close expired bids.

    This function is meant to be run by the APScheduler, and is not meant to be
    called directly.
    """
    with scheduler.app.app_context():
        logger.info("Running scheduled task 'close-items'")

        # Get items that are past the closing date, and are not already closed
        closes_before = datetime.utcnow() + timedelta(seconds=2)
        items = Item.objects(Q(closed=None) | Q(closed=False), closes_at__lt=closes_before).all()
        logger.debug("Closing %d items", len(items))

        # Close each item
        for item in items:
            try:
                # Make sure item is not already closed
                if item.closed:
                    continue

                handle_item_closing(item)

            except Exception as exc:
                logger.error("Error closing items: %s", exc, exc_info=True, extra={
                    'item_id': item.id,
                })


def _update_currency_rates():
    """
    Update the currency rates from the European Central Bank.

    This function is meant to be run by the APScheduler, and is not meant to be
    called directly.
    """
    from .currency import fetch_currency_file
    with scheduler.app.app_context():
        logger.debug("Running scheduled task 'update-currency-rates'")
        fetch_currency_file()
