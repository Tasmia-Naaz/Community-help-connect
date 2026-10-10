from datetime import datetime, timezone, timedelta
from extensions import db
from models import ResourceListing
from tests.conftest import create_user


def test_create_resource_listing(client, app):
    """Test donor publishing a resource listing."""
    with app.app_context():
        donor = create_user(role='donor', email='donor1@example.com')

    with client.session_transaction() as sess:
        sess['user_id'] = donor.id
        sess['role'] = 'donor'

    response = client.post('/donations/new', data={
        'category': 'Surplus Food Sharing',
        'name': 'Lunch meeting meal boxes',
        'description': '20 meal boxes from lunch meeting',
        'quantity': '20',
        'unit': 'boxes',
        'locality': 'Koramangala',
        'contact_preference': 'share_always'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        res = ResourceListing.query.filter_by(description='20 meal boxes from lunch meeting').first()
        assert res is not None
        assert res.status == 'Available'
        assert res.quantity == 20.0
        assert res.name == 'Lunch meeting meal boxes'
        assert res.donor_id == donor.id


def test_expired_resource_auto_withdrawal(app):
    """Test that expired resources are automatically identified and marked Withdrawn."""
    with app.app_context():
        donor = create_user(role='donor', email='donor_exp@example.com')
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)

        res = ResourceListing(
            donor_id=donor.id,
            category='Surplus Food Sharing',
            description='Perishable sandwiches past best-before date',
            quantity=10,
            unit='boxes',
            locality='Koramangala',
            expiry_date=past_time,
            status='Available'
        )
        db.session.add(res)
        db.session.commit()

        # Check property
        assert res.is_expired is True

        # Trigger auto-check
        changed = res.auto_check_expiry()
        assert changed is True
        assert res.status == 'Withdrawn'


def test_withdraw_resource_action(client, app):
    """Test manual withdrawal of an available listing by its donor."""
    with app.app_context():
        donor = create_user(role='donor', email='donor_withdraw@example.com')
        res = ResourceListing(
            donor_id=donor.id,
            category='Essential Items Assistance',
            description='Warm clothing jackets',
            quantity=5,
            unit='jackets',
            locality='Indiranagar',
            status='Available'
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    with client.session_transaction() as sess:
        sess['user_id'] = donor.id
        sess['role'] = 'donor'

    resp = client.post(f'/donations/{res_id}/withdraw', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert ResourceListing.query.get(res_id).status == 'Withdrawn'
