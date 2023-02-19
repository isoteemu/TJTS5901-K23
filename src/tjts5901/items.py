from datetime import datetime, timedelta
import logging
from typing import Optional
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, jsonify
)
from flask_babel import _, get_locale, lazy_gettext
from werkzeug.exceptions import abort

from markupsafe import Markup

from .auth import login_required, current_user
from .models import Bid, Item
from .currency import (
    convert_currency,
    format_converted_currency,
    convert_from_currency,
    get_currencies,
    get_preferred_currency,
    REF_CURRENCY,
)
from .notification import send_notification

bp = Blueprint('items', __name__)
api = Blueprint('api_items', __name__, url_prefix='/api/items')

logger = logging.getLogger(__name__)

MIN_BID_INCREMENT = 1


def get_item(id):
    try:
        item = Item.objects.get_or_404(id=id)
    except Exception as exc:
        print("Error getting item:", exc)
        abort(404)

    if item.seller == current_user:
        return item
    
    abort(403)


def get_winning_bid(item: Item) -> Optional[Bid]:
    """
    Return the (currently) winning bid for the given item.

    If there are no bids, or the item is not yet closed, return None.

    :param item: The item to get the winning bid for.
    :return: The winning bid, or None.
    """

    winning_bid = None

    # If the item is closed, return the winning bid
    if item.closed and item.winning_bid:
        return item.winning_bid

    # Sanity check: if the item is not closed, it should not have a winning bid
    assert not item.closed or not (not item.closed and winning_bid), "Item is not closed, but has a winning bid"

    try:
        # Get the highest bid that was placed before the item closed
        winning_bid = Bid.objects(item=item) \
            .filter(created_at__lt=item.closes_at) \
            .order_by('-amount') \
            .first()
    except Exception as exc:
        logger.warning("Error getting winning bid: %s", exc, exc_info=True, extra={
            'item_id': item.id,
        })

    return winning_bid


def get_item_price(item: Item) -> int:
    """
    Return the current price of the given item.

    If there are no bids, return the starting bid.

    :param item: The item to get the price for.
    :return: The current price.
    """

    winning_bid = get_winning_bid(item)
    if winning_bid:
        return winning_bid.amount + MIN_BID_INCREMENT
    else:
        return item.starting_bid


def handle_item_closing(item):
    """
    Handle the closing of an item.

    Checks if the item is not closed yet, but should be closed now. If so, 
    closes the item, and send notifications to the seller and the buyer.

    :param item: The item to handle.
    """
    # Handle the closing of an item
    if not item.is_open and not item.closed:
        logger.info("Closing item %r (%s)", item.title, item.id, extra={
            'item_id': item.id,
            'item_title': item.title,
            'item_closes_at': item.closes_at,
        })

        # Get the winning bid
        winning_bid = get_winning_bid(item)
        if winning_bid:
            item.winning_bid = winning_bid

            # Send a notifications to the seller and the buyer
            # lazy_gettext() is used to delay the translation until the message is sent
            # Markup.escape() is used to escape strings, to prevent XSS attacks
            send_notification(
                item.seller,
                title=lazy_gettext("Your item was sold"),
                message=lazy_gettext("Your item <em>%(title)s</em> was sold to %(buyer)s for %(price)s.",
                                     title=Markup.escape(item.title),
                                     buyer=Markup.escape(winning_bid.bidder.email),
                                     price=Markup.escape(winning_bid.amount)),
            )
            send_notification(
                winning_bid.bidder,
                title=lazy_gettext("You won an item"),
                message=lazy_gettext("You won the item <em>%(title)s</em> for %(price)s.",
                                     title=Markup.escape(item.title),
                                     price=Markup.escape(winning_bid.amount)),
            )

        else:
            # If there is no winning bid, send a notification to the seller
            send_notification(
                item.seller,
                title=lazy_gettext("Your item was not sold"),
                message=lazy_gettext("Your item <em>%(title)s</em> was not sold.",
                                     title=Markup.escape(item.title)),
            )

        # Close the item
        item.closed = True
        item.save()


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
        
        currency = request.form.get('currency', REF_CURRENCY)
        starting_bid = convert_from_currency(request.form['starting_bid'], currency)

        error = None

        if not title:
            error = 'Title is required.'
        if not starting_bid or starting_bid < 1:
            error = Markup(_("Starting bid must be greater than %(amount)s.", amount=format_converted_currency(1, currency)))

        if error is None:
            try:
                item = Item(
                    title=title,
                    description=description,
                    starting_bid=starting_bid,
                    seller=current_user,
                    closes_at=datetime.utcnow() + timedelta(days=1)

                )
                item.save()
                flash(_('Item listed successfully!'))

            except Exception as exc:
                error = _("Error creating item: %(exc)s", exc=exc)
                logger.warning("Error creating item: %s", exc, exc_info=True, extra={
                    'title': title,
                    'description': description,
                    'starting_bid': starting_bid,
                })
            else:
                return redirect(url_for('items.index'))

        print(error)
        flash(error, category='error')

    # Get the list of currencies, and map them to their localized names
    currencies = {}
    names = get_locale().currencies
    for currency in get_currencies():
        currencies[currency] = names.get(currency, currency)

    return render_template('items/sell.html', currencies=currencies, default_currency=get_preferred_currency())


@bp.route('/item/<id>')
def view(id):
    """
    Item view page.

    Displays the item details, and a form to place a bid.
    """

    item = Item.objects.get_or_404(id=id)

    # !!! This is disabled as it might cause race conditions
    # !!! if multiple users are accessing the same item at the same time
    # Check if the item is closed, and handle it if so.
    #handle_item_closing(item)

    # Set the minumum price for the bid form from the current winning bid
    winning_bid = get_winning_bid(item)
    min_bid = get_item_price(item)

    local_currency = get_preferred_currency()
    local_min_bid = convert_currency(min_bid, local_currency)

    if item.closes_at < datetime.utcnow():
        if winning_bid and winning_bid.bidder == current_user:
            flash(_("Congratulations! You won the auction!"), "success")
        else:
            flash(_("This item is no longer on sale."))
    elif item.closes_at < datetime.utcnow() + timedelta(hours=1):
        # Dark pattern to show enticing message to user
        flash(_("This item is closing soon! Act now! Now! Now!"))

    return render_template('items/view.html',
                           item=item, min_bid=min_bid,
                           local_min_bid=local_min_bid,
                           local_currency=local_currency)


@bp.route('/item/<id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    item = get_item(id)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        error = None

        if not title:
            error = _('Title is required.')

        try:
            item.title = title
            item.description = description
            item.save()
        except Exception as exc:
            error = _("Error updating item: %(exc)s", exc=exc)
            logger.warning("Error updating item: %s", exc, exc_info=True, extra={
                'item_id': item.id,
            })
        else:
            flash(_("Item updated successfully!"))
            return redirect(url_for('items.index'))

        print(error)
        flash(error, category='error')

    return render_template('items/update.html', item=item)


@bp.route('/item/<id>/delete', methods=('POST',))
@login_required
def delete(id):
    item = get_item(id)
    try:
        item.delete()
    except Exception as exc:
        logger.warning("Error deleting item: %s", exc, exc_info=True, extra={
            'item_id': item.id,
        })
        flash(_("Error deleting item: %(exc)s", exc=exc), category='error')
    else:
        flash(_("Item deleted successfully!"))
    return redirect(url_for('items.index'))


@bp.route('/item/<id>/bid', methods=('POST',))
@login_required
def bid(id):
    """
    Bid on an item.

    If the bid is valid, create a new bid and redirect to the item view page.
    Otherwise, display an error message and redirect back to the item view page.

    :param id: The id of the item to bid on.
    :return: A redirect to the item view page.
    """

    item = Item.objects.get_or_404(id=id)
    min_amount = get_item_price(item)

    local_amount = request.form['amount']
    currency = request.form.get('currency', REF_CURRENCY)

    amount = convert_from_currency(local_amount, currency)

    if amount < min_amount:
        flash(_("Bid must be at least %(min_amount)s", min_amount=format_converted_currency(min_amount)))
        return redirect(url_for('items.view', id=id))

    if item.closes_at < datetime.utcnow():
        flash("This item is no longer on sale.")
        return redirect(url_for('items.view', id=id))

    try:
        # Notice: if you have integrated the flask-login extension, use current_user
        # instead of g.user
        bid = Bid(
            item=item,
            bidder=current_user,
            amount=amount,
        )
        bid.save()
    except Exception as exc:
        flash(_("Error placing bid: %(exc)s", exc=exc))
    else:
        flash(_("Bid placed successfully!"))

    return redirect(url_for('items.view', id=id))


@api.route('<id>/bids', methods=('GET',))
@login_required
def api_item_bids(id):
    """
    Get the bids for an item.

    :param id: The id of the item to get bids for.
    :return: A JSON response containing the bids.
    """

    item = Item.objects.get_or_404(id=id)
    bids = []
    for bid in Bid.objects(item=item).order_by('-amount'):
        bids.append(bid.to_json())

    return jsonify({
        'success': True,
        'bids': bids
    })

@api.route('<id>/bids', methods=('POST',))
@login_required
def api_item_place_bid(id):
    """
    Place a bid on an item.

    If the bid is valid, create a new bid and return the bid.
    Otherwise, return an error message.
    
    Only accepts `REF_CURRENCY` bids.

    :param id: The id of the item to bid on.
    :return: A JSON response containing the bid.
    """

    item = Item.objects.get_or_404(id=id)
    min_amount = get_item_price(item)

    try:
        amount = int(request.form['amount'])
    except KeyError:
        return jsonify({
            'success': False,
            'error': _("Missing required argument %(argname)s", argname='amount')
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': _("Invalid value for argument %(argname)s", argname='amount')
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': _("Error parsing argument %(argname)s: %(exc)s", argname='amount', exc=exc)
        })

    if amount < min_amount:
        return jsonify({
            'success': False,
            'error': _("Bid must be at least %(min_amount)s", min_amount=min_amount)
        })

    if item.closes_at < datetime.utcnow():
        return jsonify({
            'success': False,
            'error': _("This item is no longer on sale.")
        })

    try:
        bid = Bid(
            item=item,
            bidder=current_user,
            amount=amount,
        )
        bid.save()
    except Exception as exc:
        logger.error("Error placing bid: %s", exc, exc_info=True, extra={
            'item_id': item.id,
            'bidder_id': current_user.id,
            'amount': amount,
        })

        return jsonify({
            'success': False,
            'error': _("Error placing bid: %(exc)s", exc=exc)
        })

    return jsonify({
        'success': True,
        'bid': bid.to_mongo().to_dict()
    })
