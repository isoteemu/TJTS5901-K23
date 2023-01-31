"""
Flask based tests
=================

Uses the flask testclient to retrieve and post pages in application.
"""

import pytest
from flask.testing import FlaskClient


# This is the string we are looking for in the frontpage.
IN_TITLE = "DMC"

def test_fetch_mainpage(client: FlaskClient):
    """
    Fetch frontpage and check that it has <title>.

    :param client: Flask test client. See conftest.py for more info how it is
        created.
    """

    # Request frontpage
    page = client.get('/')

    # Check that page contains something.
    # Note about assert; assert is special kind of keyword. By default
    # assert statements are run, but if they are deemed too costly, python
    # interepter can be defined to pass them with `python -O` flag.
    # If assert statement return False, new assert exception is raised, and
    # and test is deemed to fail. After first statement - condition - human
    # readable reason for failure can be provided.
    # >>> assert (condition-for-failure, "human readable reason")
    assert page, "Did not get anything"
    assert IN_TITLE.encode() in page.data, f"Page didn't have {IN_TITLE}"
