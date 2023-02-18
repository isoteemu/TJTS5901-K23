from datetime import datetime
from secrets import token_urlsafe

from .db import db

from mongoengine import (
    StringField,
    IntField,
    ReferenceField,
    DateTimeField,
    EmailField,
    BooleanField,
    EnumField,
)

from flask_login import UserMixin
from bson import ObjectId

from .i18n import SupportedLocales


class User(UserMixin, db.Document):
    """
    Model representing a user of the auction site.
    """
    id: ObjectId

    email = EmailField(required=True, unique=True)
    "The user's email address."

    password = StringField(required=True)

    locale = EnumField(SupportedLocales)
    currency = StringField(max_length=3)
    "The user's preferred currency."

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

    meta = {"indexes": [
        {"fields": [
            "amount",
            "item",
            "created_at",
        ]}
    ]}

    amount = IntField(required=True, min_value=0)
    "Indicates the value of the bid."

    bidder = ReferenceField(User, required=True)
    "User who placed the bid."

    item = ReferenceField(Item, required=True)
    "Item that the bid is for."

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    "Date and time that the bid was placed."


class AccessToken(db.Document):
    """
    Access token for a user.

    This is used to authenticate API requests.
    """

    meta = {"indexes": [
        {"fields": [
            "token",
            "user",
            "expires",
        ]}
    ]}

    name = StringField(max_length=100, required=True)
    "Human-readable name for the token."

    user = ReferenceField(User, required=True)
    "User that the token is for."

    token = StringField(required=True, unique=True, default=token_urlsafe)
    "The token string."

    last_used_at = DateTimeField(required=False)
    "Date and time that the token was last used."

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    "Date and time that the token was created."

    expires = DateTimeField(required=False)
    "Date and time that the token expires."


class Notification(db.Document):
    """
    Represents a message between two users, or a message to a user from
    the system.
    """

    meta = {"indexes": [
        {"fields": [
            "user",
            "read_at",
            "created_at",
        ]}
    ]}

    id: ObjectId

    user = ReferenceField(User, required=True)

    category = StringField(max_length=100, default="message")
    message = StringField(required=True)
    title = StringField(max_length=120)

    created_at = DateTimeField(required=True, default=datetime.utcnow)
    read_at = DateTimeField(required=False)
