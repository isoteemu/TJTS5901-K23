from datetime import datetime
from .db import db

from mongoengine import (
    StringField,
    IntField,
    ReferenceField,
    DateTimeField,
    EmailField,
)


class User(db.Document):
    """
    Model representing a user of the auction site.
    """

    email = EmailField(required=True, unique=True)
    "The user's email address."

    password = StringField(required=True)

    created_at = DateTimeField(required=True, default=datetime.utcnow)


class Item(db.Document):
    """
    A model for items that are listed on the auction site.
    """

    title = StringField(max_length=100, required=True)
    description = StringField(max_length=2000, required=True)

    starting_bid = IntField(required=True, min_value=0)

    seller = ReferenceField(User, required=True)

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    closes_at = DateTimeField()
