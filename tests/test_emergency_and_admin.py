from extensions import db
from models import EmergencyEvent, Notification, User
from tests.conftest import create_user


def test_unauthorized_user_blocked_from_admin(client, app):
    """Test that non-admin users cannot access administrative endpoints."""
    with app.app_context():
        user = create_user(role='help_seeker', email='nonadmin@example.com')

    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['role'] = 'help_seeker'

    response = client.get('/admin/dashboard', follow_redirects=True)
    # Must deny access and redirect
    assert b"Access denied" in response.data or response.status_code == 403


def test_emergency_mode_activation_and_notifications(client, app):
    """
    WORKFLOW G: Test Administrator Emergency Mode declaration and
    instant in-app notification dispatch to active locality volunteers.
    """
    with app.app_context():
        admin = create_user(role='admin', email='masteradmin@example.com')
        # Create a volunteer in the affected area
        vol = create_user(role='volunteer', email='vol_flood@example.com', locality='Sector 4')

    with client.session_transaction() as sess:
        sess['user_id'] = admin.id
        sess['role'] = 'admin'

    response = client.post('/admin/emergency/new', data={
        'emergency_type': 'Monsoon Waterlogging',
        'affected_locality': 'Sector 4',
        'severity': 'Severe',
        'description': 'Storm drain water backup. Need drinking water distribution and basic pumps.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        # Check active event exists
        event = EmergencyEvent.query.filter_by(is_active=True).first()
        assert event is not None
        assert event.emergency_type == 'Monsoon Waterlogging'
        assert event.affected_locality == 'Sector 4'

        # Check volunteer received broadcast in-app notification
        notif = Notification.query.filter_by(user_id=vol.id).first()
        assert notif is not None
        assert "EMERGENCY ALERT" in notif.title


def test_user_suspension_toggle(client, app):
    """Test administrator suspending and reactivating a user account."""
    with app.app_context():
        admin = create_user(role='admin', email='superadmin@example.com')
        regular_user = create_user(role='help_seeker', email='baduser@example.com')
        user_id = regular_user.id

    with client.session_transaction() as sess:
        sess['user_id'] = admin.id
        sess['role'] = 'admin'

    # Suspend user
    resp = client.post(f'/admin/users/{user_id}/toggle-suspend', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.get(user_id).is_suspended is True

    # Reactivate user
    resp2 = client.post(f'/admin/users/{user_id}/toggle-suspend', follow_redirects=True)
    assert resp2.status_code == 200
    with app.app_context():
        assert User.query.get(user_id).is_suspended is False
