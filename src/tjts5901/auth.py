import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from sentry_sdk import set_user

from .models import User

from mongoengine import DoesNotExist

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
    """
    If a user id is stored in the session, load the user object from
    """

    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
        set_user(None)

    else:
        g.user = User.objects.get(id=user_id)
        set_user({"id": str(g.user.id), "email": g.user.email})


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

