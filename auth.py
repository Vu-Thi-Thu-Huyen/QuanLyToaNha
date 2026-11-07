from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            flash('Vui lòng đăng nhập để tiếp tục!')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped