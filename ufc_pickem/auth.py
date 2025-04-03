from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from .models import User
from .forms import LoginForm
from .extensions import db


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Login using email or username
        user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.email.data)
        ).first()

        if user:
            # Check if account is verified
            if not user.is_verified:
                # Delete if unverified and older than 24 hours
                if user.created_at < datetime.utcnow() - timedelta(hours=24):
                    db.session.delete(user)
                    db.session.commit()
                    flash("Account was unverified and expired. Please register again.", "warning")
                else:
                    flash("Please verify your email before logging in.", "warning")
                return redirect(url_for('auth.login'))

            # Password check
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('main.dashboard'))

        flash('Invalid login credentials.', 'danger')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
