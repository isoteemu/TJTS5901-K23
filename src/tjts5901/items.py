from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .models import Item

bp = Blueprint('items', __name__)

@bp.route('/')
def index():
    items = Item.objects.all()
    return render_template('items/index.html',
        items=items
    )


@bp.route('/update')
def update():
    ...