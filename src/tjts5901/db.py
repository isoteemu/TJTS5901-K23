import logging
from os import environ

from flask_mongoengine import MongoEngine

db = MongoEngine()
logger = logging.getLogger(__name__)


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
        logger.info("Database connection string found, using it.",
                    # You can use the `extra` parameter to add extra information to the log message.
                    # This is useful for debugging, but should be removed in production.
                    extra={"MONGO_URL": mongodb_url} if app.debug else {})

    else:
        logger.warning("No database connection string found in env, using defaults.",
                       extra={"MONGODB_SETTINGS": app.config.get("MONGODB_SETTINGS")} if app.debug else {})

    db.init_app(app)

