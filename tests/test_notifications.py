"""
Test the notifications module.
"""
import pytest

from flask import Flask, flash, url_for
from flask.testing import FlaskClient
from tjts5901.models import Notification, User
from tjts5901.notification import send_notification, get_notifications


def test_send_notification(user: User):
    """
    Test that a notification can be sent to a user.
    """

    send_notification(user, "Test message", "message", "Test title")

    # Check that the notification was saved to the database.
    notifications = Notification.objects(user=user)
    assert len(notifications) == 1, "Notification was not saved to the database."

    # Check that the notification has the correct values.
    notification = notifications.first()
    assert notification.message == "Test message"
    assert notification.category == "message"
    assert notification.title == "Test title"


def test_flash_messages(user: User, app: Flask):
    """
    Test that flask.flash() can be used to send notifications.
    """

    with app.test_request_context():
        flash("Test message", "message")

        notifications = get_notifications(user)
        assert len(notifications) == 1, "Flash message was returned."

        notification = notifications.pop()
        assert notification.message == "Test message"
        assert notification.category == "message"

def test_notifications_view(client: FlaskClient, user: User):
    """
    Test that the notifications view works.
    """

    # Send a notification to the user.

    db_notification = {
        "message": "This is a database message",
        "category": "message",
    }

    send_notification(user, **db_notification)

    with client:
        # Log in as the user.
        client.post(
            url_for("auth.login"),
            data={"email": user.email, "password": user._plaintext_password},
            follow_redirects=False,
        )

        # Check that the notification is shown on the page.
        response = client.get(url_for('notification.user_notifications'))
        
        assert response.status_code == 200
        assert response.is_json

        assert db_notification['message'] in [msg['message'] for msg in response.json['notifications']], \
            "Database message was not returned."
