from .db import db

from mongoengine import (
    StringField,
)



class User(db.Document):
    ...


class Item(db.Document):
    """
    A model for items that are listed on the auction site.
    """

    title = StringField(max_length=200, required=True)

    