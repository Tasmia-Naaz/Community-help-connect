from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, g, abort
from extensions import db
from models import User, HelpRequest, ResourceListing, EmergencyEvent, StatusHistory, Notification
from forms import EmergencyEventForm
from decorators import admin_required
from helpers import get_active_emergency, broadcast_to_volunteers, record_status_change
from . import admin_bp


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    Administrator Dashboard:
    Metrics, user management, request/resource oversight, and emergency control center.
    """
    # 1. Total KPI Metrics
    total_users = User.query.count()
    total_requests = HelpRequest.query.count()
    open_requests = HelpRequest.query.filter_by(status='Pending').count()
    in_progress_requests = HelpRequest.query.filter_by(status='In Progress').count()
    completed_requests = HelpRequest.query.filter_by(status='Completed').count()
    total_resources = ResourceListing.query.count()
    active_resources = ResourceListing.query.filter_by(status='Available').count()

    # 2. Search & Filtering for Users
    user_search = request.args.get('user_search', '').strip()
    user_query = User.query
    if user_search:
        user_query = user_query.filter(
            (User.full_name.ilike(f"%{user_search}%")) |
            (User.email.ilike(f"%{user_search}%")) |
            (User.locality.ilike(f"%{user_search}%"))
        )
    users_list = user_query.order_by(User.created_at.desc()).limit(50).all()

    # 3. Recent Requests
    recent_requests = HelpRequest.query.order_by(HelpRequest.created_at.desc()).limit(30).all()

    # 4. Recent Resources
    recent_resources = ResourceListing.query.order_by(ResourceListing.created_at.desc()).limit(30).all()

    # 5. Active Emergency & Event Logs
    active_emergency = get_active_emergency()
    past_emergencies = EmergencyEvent.query.order_by(EmergencyEvent.activated_at.desc()).limit(10).all()

    # 6. Recent Audit Status History
    recent_history = StatusHistory.query.order_by(StatusHistory.created_at.desc()).limit(20).all()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_requests=total_requests,
        open_requests=open_requests,
        in_progress_requests=in_progress_requests,
        completed_requests=completed_requests,
        total_resources=total_resources,
        active_resources=active_resources,
        users=users_list,
        requests=recent_requests,
        resources=recent_resources,
        active_emergency=active_emergency,
        past_emergencies=past_emergencies,
        recent_history=recent_history,
        user_search=user_search
    )


@admin_bp.route('/users/<int:user_id>/toggle-suspend', methods=['POST'])
@admin_required
def toggle_user_suspension(user_id):
    """Suspend or reactivate a user account."""
    user = User.query.get_or_404(user_id)
    
    # Safeguard: Prevent admin from suspending themselves
    if user.id == g.current_user.id:
        flash("You cannot suspend your own administrator account.", "warning")
        return redirect(url_for('admin.dashboard'))

    user.is_suspended = not user.is_suspended
    db.session.commit()

    action = "suspended" if user.is_suspended else "reactivated"
    flash(f"User {user.email} has been {action}.", "info")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/toggle-verify', methods=['POST'])
@admin_required
def toggle_user_verification(user_id):
    """Mark a user account as verified or unverified."""
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()

    action = "verified" if user.is_verified else "unverified"
    flash(f"User {user.email} marked as {action}.", "info")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/emergency/new', methods=['GET', 'POST'])
@admin_required
def declare_emergency():
    """
    WORKFLOW G: Emergency Mode Activation.
    Declares a community emergency, prioritizes relief in affected locality,
    and dispatches broadcast notifications to volunteers.
    """
    form = EmergencyEventForm()

    if form.validate_on_submit():
        # Deactivate any previous active emergencies
        EmergencyEvent.query.filter_by(is_active=True).update({'is_active': False, 'deactivated_at': datetime.now(timezone.utc)})

        event = EmergencyEvent(
            created_by_id=g.current_user.id,
            emergency_type=form.emergency_type.data.strip(),
            affected_locality=form.affected_locality.data.strip(),
            severity=form.severity.data,
            description=form.description.data.strip(),
            is_active=True,
            activated_at=datetime.now(timezone.utc)
        )
        db.session.add(event)
        db.session.commit()

        # Broadcast high-priority notification to all volunteers in the locality
        notif_count = broadcast_to_volunteers(
            locality=event.affected_locality,
            title=f"EMERGENCY ALERT [{event.severity.upper()}]: {event.emergency_type}",
            message=f"Community emergency declared in {event.affected_locality}. Urgent assistance required: {event.description[:120]}...",
            link=url_for('volunteers.volunteer_dashboard')
        )

        flash(f"Emergency Mode ACTIVATED for {event.affected_locality}. In-app alert dispatched to {notif_count} volunteers.", "danger")
        return redirect(url_for('admin.dashboard'))

    return render_template('emergency_form.html', form=form)


@admin_bp.route('/emergency/<int:event_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_emergency(event_id):
    """Deactivate an active emergency mode."""
    event = EmergencyEvent.query.get_or_404(event_id)
    event.is_active = False
    event.deactivated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f"Emergency '{event.emergency_type}' in {event.affected_locality} has been DEACTIVATED.", "success")
    return redirect(url_for('admin.dashboard'))
