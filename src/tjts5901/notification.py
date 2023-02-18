"""
This module provides a way to send notifications to users.
"""

import dataclasses
from datetime import datetime
import logging

from flask import get_flashed_messages, Blueprint
from flask_login import current_user
from flask_babel import force_locale, lazy_gettext

from .models import Notification, User

bp = Blueprint('notification', __name__, url_prefix='/')

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class Message:
    """
    Represents a message to be displayed to the user.
    """
    message: str
    category: str

    # Additional field for the template
    title: str = lazy_gettext("Message")

    created_at: datetime = dataclasses.field(default_factory=datetime.utcnow)


def init_notification(app):
    """
    Initialize the notifications module.
    """
    app.register_blueprint(bp)
    app.jinja_env.globals.update(get_notifications=get_notifications)


def send_notification(user, message, category="message", title=None):
    """
    Send a notification to the given user.

    :param user: The user to send the message to.
    :param subject: The subject of the message.
    :param message: The message to send.
    """

    # Change the locale to the message recipient locale.
    with force_locale(user.locale):
        notification = Notification(
            user=user,
            message=str(message),
            category=category,
            title=str(title),
        )
        notification.save()


def get_notifications(user: User = current_user) -> list[Message]:
    """
    Get the messages for the given user.

    Flash messages are returned first, followed by database messages.
    Messages are marked as read when they are retrieved.

    Notice: the listing query might not return recently added messages.

    :param user: The user to get the messages for.
    :return: A list of messages.
    """

    messages = []

    # Get the flash messages first
    for category, message in get_flashed_messages(with_categories=True):
        messages.append(Message(message, category))

    if user is None or not user.is_authenticated:
        logger.debug("User is not authenticated, returning flash messages.")
        return messages

    # Get the database messages
    notifications = Notification.objects(user=user, read_at=None).order_by('-created_at').all()

    for notification in notifications:
        messages.append(Message(notification.message, notification.category, notification.title))

    # Mark the messages as read
    notifications.update(read_at=datetime.utcnow())

    return messages
