from flask import render_template, redirect, url_for, flash, request, session, g
from extensions import db
from models import User, Notification
from forms import RegistrationForm, LoginForm
from helpers import (
    check_login_rate_limit, record_failed_login,
    clear_failed_logins, create_notification
)
from decorators import login_required
from . import auth_bp


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Public registration for Help Seekers, Volunteers, and Donors."""
    if session.get('user_id'):
        flash("You are already logged in.", "info")
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = (form.email.data or '').strip().lower()
        role = form.role.data

        # Explicit security safeguard: Public registration cannot create administrators
        if role == 'admin':
            flash("Administrator accounts cannot be created via public registration.", "danger")
            return render_template('register.html', form=form)

        new_user = User(
            full_name=(form.full_name.data or '').strip(),
            email=email,
            phone=(form.phone.data or '').strip(),
            locality=(form.locality.data or '').strip(),
            role=role,
            is_verified=True,
            is_suspended=False
        )
        new_user.set_password(form.password.data or '')

        db.session.add(new_user)
        db.session.commit()

        # Create welcome in-app notification
        create_notification(
            user_id=new_user.id,
            title="Welcome to Community Help Connect!",
            message=f"Thank you for registering as a {role.replace('_', ' ').title()}. You can now start collaborating with your neighbors.",
            link=None
        )
        db.session.commit()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Secure user login with rate-limiting throttling and role redirection."""
    if session.get('user_id'):
        return redirect(url_for('index'))

    form = LoginForm()
    ip_identifier = request.remote_addr or 'unknown-ip'

    if form.validate_on_submit():
        email = (form.email.data or '').strip().lower()
        throttle_key = f"{ip_identifier}:{email}"

        # Check rate-limit throttling
        is_allowed, minutes_left = check_login_rate_limit(throttle_key)
        if not is_allowed:
            flash(f"Too many failed login attempts. For security, please try again in {minutes_left} minutes.", "danger")
            return render_template('login.html', form=form)

        user = User.query.filter_by(email=email).first()

        # Generic failure message to prevent email enumeration
        if not user or not user.check_password(form.password.data):
            record_failed_login(throttle_key)
            flash("Invalid email address or password. Please try again.", "danger")
            return render_template('login.html', form=form)

        if user.is_suspended:
            flash("Your account has been suspended. Please contact administrator support.", "danger")
            return render_template('login.html', form=form)

        # Clear throttle record on successful authentication
        clear_failed_logins(throttle_key)

        # Establish secure session
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['role'] = user.role
        session['locality'] = user.locality
        session.permanent = True

        flash(f"Welcome back, {user.full_name}!", "success")

        # Redirect based on user role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'volunteer':
            return redirect(url_for('volunteers.volunteer_dashboard'))
        elif user.role == 'donor':
            return redirect(url_for('donations.donor_dashboard'))
        elif user.role == 'help_seeker':
            return redirect(url_for('help_requests.seeker_dashboard'))
        return redirect(url_for('index'))

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """Clear session and log user out."""
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('index'))


@auth_bp.route('/notifications')
@login_required
def notifications():
    """Display in-app notifications for the current user."""
    user_notifications = Notification.query.filter_by(user_id=g.current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    
    # Mark all unread as read upon viewing
    for n in user_notifications:
        if not n.is_read:
            n.is_read = True
    db.session.commit()

    return render_template('notifications.html', notifications=user_notifications)


@auth_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark a specific notification as read."""
    notif = Notification.query.filter_by(id=notif_id, user_id=g.current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('auth.notifications'))
