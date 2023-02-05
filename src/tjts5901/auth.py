import functools
import logging

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import LoginManager

from werkzeug.security import check_password_hash, generate_password_hash
from sentry_sdk import set_user

from .models import User

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
        user = User.get(id=user_id)
        set_user({"id": str(g.user.id), "email": g.user.email})
    except DoesNotExist:
        logger.error("User not found: %s", user_id)
        return None

    return user


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


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
            session.clear()
            session['user_id'] = str(user['id'])
            flash(f"Hello {email}, You have been logged in.")
            return redirect(url_for('items.index'))

        print("Error logging in:", error)
        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

