# app/utils.py
from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(roles):
    """Dekorator untuk membatasi akses berdasarkan peran."""
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session or session.get('peran') not in roles:
                flash("Anda tidak memiliki izin untuk mengakses halaman ini.", "error")
                return redirect(url_for('admin.admin_dashboard'))
            return func(*args, **kwargs)
        return decorated_view
    return wrapper


