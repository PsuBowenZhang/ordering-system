from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def roles_required(roles):
    """
    Decorator to restrict access based on user roles.
    :param roles: A list of allowed roles.
    """
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You need to log in to access this page.", "warning")
                return redirect(url_for('index.login'))
            if current_user.role not in roles:
                flash("You do not have the necessary permissions to access this page.", "danger")
                return redirect(url_for('index.index'))
            return func(*args, **kwargs)
        return wrapped_function
    return decorator