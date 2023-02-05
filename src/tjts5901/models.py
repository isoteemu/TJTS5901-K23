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

    @property
    def is_open(self) -> bool:
        """
        Return whether the item is open for bidding.
        """
        return self.closes_at > datetime.utcnow()


class Bid(db.Document):
    """
    A model for bids on items.
    """

    amount = IntField(required=True, min_value=0)
    "Indicates the value of the bid."

    bidder = ReferenceField(User, required=True)
    "User who placed the bid."

    item = ReferenceField(Item, required=True)
    "Item that the bid is for."

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    "Date and time that the bid was placed."
