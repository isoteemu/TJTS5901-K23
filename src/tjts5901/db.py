from os import environ
from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app):
    """
    Initialize the database connection.

    Fetches the database connection string from the environment variable `MONGO_URL`
    and, if present, sets the `MONGODB_SETTINGS` configuration variable to use it.
    """


    # To keep secrets private, we use environment variables to store the database connection string.
    # `MONGO_URL` is expected to be a valid MongoDB connection string, see: blah blah blah
    mongodb_url = environ.get("MONGO_URL")

    if mongodb_url is not None:
        app.config["MONGODB_SETTINGS"] = {
            "host": mongodb_url,
        }

    db.init_app(app)

