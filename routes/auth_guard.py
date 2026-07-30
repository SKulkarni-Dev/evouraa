from functools import wraps

from flask import session, redirect, url_for, jsonify


def login_required(view):
    """For normal page routes — redirects an anonymous visitor to /login."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            return redirect(url_for("login_page"))

        return view(*args, **kwargs)

    return wrapped_view


def api_login_required(view):
    """For fetch/AJAX endpoints — returns JSON 401 instead of a redirect,
    since a redirect would just be silently followed by fetch()."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            return jsonify(success=False, message="Please log in first."), 401

        return view(*args, **kwargs)

    return wrapped_view