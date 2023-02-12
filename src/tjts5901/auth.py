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

from werkzeug.security import check_password_hash, generate_password_hash
from sentry_sdk import set_user

from .models import User, Item

from mongoengine import DoesNotExist

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

    login_manager.init_app(app)

    logger.debug("Initialized authentication")


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

    return render_template('auth/profile.html', user=user, items=items)
