from datetime import datetime, timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .models import Item

bp = Blueprint('items', __name__)


def get_item(id):
    try:
        item = Item.objects.get_or_404(id=id)
    except Exception as exc:
        print("Error getting item:", exc)
        abort(404)

    if item.seller == g.user:
        return item
    
    abort(403)

@bp.route("/", defaults={'page': 1})
@bp.route("/items/<int:page>")
def index(page=1):
    """
    Index page for items on sale.

    Lists only items that are currently sale, with pagination.
    """

    # Function used on propaedeutic
    # items = Item.objects.all()

    # Fetch items that are on sale currently, and paginate
    # See: http://docs.mongoengine.org/projects/flask-mongoengine/en/latest/custom_queryset.html
    items = Item.objects.filter(closes_at__gt=datetime.utcnow()) \
        .order_by('-closes_at') \
        .paginate(page=page, per_page=10)

    return render_template('items/index.html',
                           items=items)


@bp.route('/sell', methods=('GET', 'POST'))
@login_required
def sell():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        starting_bid = int(request.form['starting_bid'])
        error = None

        if not title:
            error = 'Title is required.'
        if not starting_bid or starting_bid < 1:
            error = 'Starting bid must be greater than 0.'

        if error is None:
            try:
                item = Item(
                    title=title,
                    description=description,
                    starting_bid=starting_bid,
                    seller=g.user,
                    closes_at=datetime.utcnow() + timedelta(days=1)

                )
                item.save()
            except Exception as exc:
                error = f"Error creating item: {exc!s}"
            else:
                return redirect(url_for('items.index'))

            print(error)
            flash(error)

    return render_template('items/sell.html')


@bp.route('/item/<id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    item = get_item(id)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        error = None

        if not title:
            error = 'Title is required.'

        try:
            item.title = title
            item.description = description
            item.save()
        except Exception as exc:
            error = f"Error updating item: {exc!s}"
        else:
            flash("Item updated successfully!")
            return redirect(url_for('items.index'))

        print(error)
        flash(error)

    return render_template('items/update.html', item=item)


@bp.route('/item/<id>/delete', methods=('POST',))
@login_required
def delete(id):
    item = get_item(id)
    try:
        item.delete()
    except Exception as exc:
        error = f"Error deleting item: {exc!s}"
        print(error)
        flash(error)
    else:
        flash("Item deleted successfully!")
    return redirect(url_for('items.index'))
