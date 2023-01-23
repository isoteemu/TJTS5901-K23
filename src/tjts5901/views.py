"""
Basic views for Application
===========================
"""

from flask import Blueprint, render_template, send_from_directory

# Main blueprint.
bp = Blueprint('views', __name__)

# Blueprint for documentation.
docs_bp = Blueprint('docs', __name__)

@bp.route("/")
def index() -> str:
    """
    Index page.

    """

    # Render template file. Template file is using Jinja2 syntax, and can be passed an arbitrary number
    # of arguments to be used in the template. The template file is located in the templates directory.
    html = render_template("index.html.j2", title="TJTS5901 Example. I'ts changed now.")
    return html
