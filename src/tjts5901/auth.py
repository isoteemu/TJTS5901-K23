from datetime import datetime
import functools
import logging

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for, abort
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_babel import _
from werkzeug.security import check_password_hash, generate_password_hash
from sentry_sdk import set_user

from .models import AccessToken, Bid, User, Item

from mongoengine import DoesNotExist
from mongoengine.queryset.visitor import Q

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


def init_auth(app):
    """
    Integrate authentication into the application.
    """
    app.register_blueprint(bp)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.user_loader(load_logged_in_user)

    app.config['AUTH_HEADER_NAME'] = 'Authorization'
    login_manager.request_loader(load_user_from_request)

    login_manager.init_app(app)

    logger.debug("Initialized authentication")


def load_user_from_request(request):
    """
    Load a user from the request.

    This function is used by Flask-Login to load a user from the request.
    """
    api_key = request.headers.get("Authorization")

    if api_key:
        api_key = api_key.replace("Bearer ", "", 1)
        try:
            token = AccessToken.objects.get(token=api_key)
            if token.expires and token.expires < datetime.utcnow():
                logger.warning("Token expired: %s", api_key)
                return None
            # User is authenticated

            token.last_used_at = datetime.utcnow()
            token.save()
            logger.debug("User authenticated via token: %r", token.user.email, extra={
                "user": token.user.email,
                "user_id": str(token.user.id),
                "token": token.token,
            })
            return token.user
        except DoesNotExist:
            logger.error("Token not found: %s", api_key)

    return None


def load_logged_in_user(user_id):
    """
    Load a user from the database, given the user's id.
    """
    try:
        user = User.objects.get(id=user_id)
        set_user({"id": str(user.id), "email": user.email})
    except DoesNotExist:
        logger.error("User not found: %s", user_id)
        return None

    return user


def get_user_by_email(email: str) -> User:
    """
    Get a user from the database, given the user's email.

    If the email is 'me', then the current user is returned.

    :param email: The email of the user to get.
    """

    if email is None:
        abort(404)

    if email == "me" and current_user.is_authenticated:
        email = current_user.email

    try:
        user = User.objects.get_or_404(email=email)
    except DoesNotExist:
        logger.error("User not found: %s", email)
        abort(404)

    return user


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        print("Registering user...")
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        terms = request.form.get('terms', False)
        error = None

        if not email:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif not terms:
            error = 'You must agree to the terms.'

        if error is None:
            try:
                user = User(
                    email=email,
                    password=generate_password_hash(password)
                )
                user.save()
                flash("You have been registered. Please log in.")

            except Exception as exc:
                error = f"Error creating user: {exc!s}"
            else:
                return redirect(url_for("auth.login"))

        print("Could not register user:", error)
        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        error = None
        try:
            user = User.objects.get(email=email)
        except DoesNotExist:
            error = 'Incorrect username.'

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            remember_me = bool(request.form.get("remember-me", False))
            if login_user(user, remember=remember_me):

                flash(f"Hello {email}, You have been logged in.")

                next = request.args.get('next')
                # Better check that the user actually clicked on a relative link
                # or else they could redirect you to a malicious website!
                if next is None or not next.startswith('/'):
                    next = url_for('index')

                return redirect(next)
            else:
                error = "Error logging in."

        logger.info("Error logging user in: %r: Error: %s", email, error)
        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user.

    Also removes the "remember me" cookie.
    """
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('index'))


@bp.route('/profile', defaults={'email': 'me'})
@bp.route('/profile/<email>')
@login_required
def profile(email):
    """
    Show the user's profile page for the given email.

    If the email is 'me', then the current user's profile is shown.
    """

    user: User = get_user_by_email(email)

    # List the items user has created
    items = Item.objects(seller=user).all()

    # List the items user has won
    # TODO: Could be done smarter with a join
    bids = Bid.objects(bidder=user).only("id").all()
    won_items = Item.objects(winning_bid__in=bids).all()

    return render_template('auth/profile.html', user=user, items=items, won_items=won_items)


@bp.route('/profile/<email>/token', methods=('GET', 'POST'))
@login_required
def user_access_tokens(email):
    """
    Show the user's tokens page for the given email.
    """

    user: User = get_user_by_email(email)
    # Fetch all the user tokens that are active or have no expire date
    tokens = AccessToken.objects(Q(expires__gte=datetime.now()) | Q(expires=None), user=user).all()

    token = None
    if request.method == 'POST':
        try:
            name = request.form['name']

            if expires := request.form.get('expires'):
                expires = datetime.fromisoformat(expires)
            else:
                expires = None

            token = AccessToken(
                user=user,
                name=name,
                expires=expires,
            )
            token.save()
        except KeyError as exc:
            logger.debug("Missing required field: %s", exc)
            flash(_("Required field missing"))
        except Exception as exc:
            logger.exception("Error creating token: %s", exc)
            flash(_("Error creating token: %s") % exc)
        else:
            flash(_("Created token: %s") % token.name)

    return render_template('auth/tokens.html', user=user, tokens=tokens, token=token)


@bp.route('/profile/<email>/token/<id>', methods=('POST',))
def delete_user_access_token(email, id):
    """
    Delete an access token.
    """
    user = get_user_by_email(email)
    token = AccessToken.objects.get_or_404(id=id)

    if token.user != user:
        logger.warning("User %s tried to delete token %s", user.email, token.name, extra={
            "user": user.email,
            "token": str(token.id),
            "token_user": token.user.email,
        })
        abort(403)

    token.delete()

    flash(f"Deleted token {token.name}")
    return redirect(url_for('auth.user_access_tokens', email=token.user.email))
