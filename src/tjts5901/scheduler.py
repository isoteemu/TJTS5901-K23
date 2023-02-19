"""
This module contains the APScheduler extension.

This extension is used to schedule background tasks.
"""

import logging

from flask_apscheduler import APScheduler

logger = logging.getLogger(__name__)


def init_scheduler(app):
    """
    Initialize the APScheduler extension.

    This function is meant to be called from the create_app() function.
    """

    scheduler = APScheduler()
    scheduler.init_app(app)

    with app.app_context():
        # Start the scheduler.
        scheduler.start()

    return app
