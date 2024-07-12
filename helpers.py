import os
from flask import redirect, render_template, request, session, send_file, url_for
from functools import wraps

# ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_USERNAME = "admin"

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", error_code=code, error_message=escape(message)), code


def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("admin") != ADMIN_USERNAME:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function