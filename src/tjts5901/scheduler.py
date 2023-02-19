"""
This module contains the APScheduler extension.

This extension is used to schedule background tasks.
"""

from datetime import timedelta
import logging

from flask_apscheduler import APScheduler
from mongoengine import signals

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
