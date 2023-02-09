from datetime import datetime
from .db import db

from mongoengine import (
    StringField,
    IntField,
    ReferenceField,
    DateTimeField,
    EmailField,
    BooleanField,
)

from flask_login import UserMixin
from bson import ObjectId


class User(UserMixin, db.Document):
    """
    Model representing a user of the auction site.
    """
    id: ObjectId

    email = EmailField(required=True, unique=True)
    "The user's email address."

    password = StringField(required=True)

    created_at = DateTimeField(required=True, default=datetime.utcnow)

    is_disabled = BooleanField(default=False)
    "Whether the user is disabled."

    @property
    def is_active(self) -> bool:
        """
        Return whether the user is active.

        This is used by Flask-Login to determine whether the user is
        allowed to log in.
        """
        return not self.is_disabled

    def get_id(self) -> str:
        """
        Return the user's id as a string.
        """
        return str(self.id)


class Item(db.Document):
    """
    A model for items that are listed on the auction site.
    """

    # Create index for sorting items by closing date
    meta = {"indexes": [
        {"fields": [
            "closes_at",
        ]}
    ]}

    title = StringField(max_length=100, required=True)
    description = StringField(max_length=2000, required=True)

    starting_bid = IntField(required=True, min_value=0)

    seller = ReferenceField(User, required=True)

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    closes_at = DateTimeField()
