from datetime import datetime, timezone

from extensions import db
from models import ResourceListing, ResourceRequest, StatusHistory
from tests.conftest import create_user


def create_resource(donor, quantity=8, category='Essential Items Assistance', locality='Indiranagar'):
    resource = ResourceListing(
        donor_id=donor.id,
        category=category,
        description='Winter blankets and sweaters for neighborhood residents',
        quantity=quantity,
        unit='sets',
        locality=locality,
        pickup_instructions='PRIVATE PICKUP CODE: 4312',
        available_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
        status='Available'
    )
    db.session.add(resource)
    db.session.commit()
    return resource


def login_as(client, user):
    with client.session_transaction() as session:
        session['user_id'] = user.id
        session['role'] = user.role


def test_volunteer_dashboard_shows_filtered_resources_without_private_instructions(client, app):
    with app.app_context():
        donor = create_user(role='donor', email='resource_donor@example.com')
        create_resource(donor)
        create_resource(donor, category='Medical Assistance', locality='Koramangala')
        volunteer = create_user(role='volunteer', email='resource_volunteer@example.com')

    login_as(client, volunteer)
    response = client.get('/volunteers/dashboard?resource_category=Essential%20Items%20Assistance&resource_locality=Indiranagar')

    assert response.status_code == 200
    assert b'Winter blankets and sweaters' in response.data
    assert b'PRIVATE PICKUP CODE' not in response.data
    assert b'Koramangala' not in response.data
    assert b'Request Items' in response.data


def test_volunteer_donor_approval_collection_delivery_workflow(client, app):
    with app.app_context():
        donor = create_user(role='donor', email='workflow_donor@example.com')
        volunteer = create_user(role='volunteer', email='workflow_volunteer@example.com')
        resource = create_resource(donor, quantity=8)
        resource_id = resource.id

    login_as(client, volunteer)
    response = client.post(f'/volunteers/resources/{resource_id}/request', data={'quantity': '3'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'item request was sent' in response.data

    with app.app_context():
        item_request = ResourceRequest.query.one()
        request_id = item_request.id
        assert item_request.status == 'Pending'
        assert ResourceListing.query.get(resource_id).quantity == 8

    login_as(client, donor)
    donor_page = client.get('/donations/dashboard')
    assert donor_page.status_code == 200
    assert b'Pending Item Requests' in donor_page.data
    assert b'workflow_volunteer' not in donor_page.data
    response = client.post(
        f'/donations/resource-requests/{request_id}/decision',
        data={'decision': 'approve'},
        follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        assert ResourceRequest.query.get(request_id).status == 'Approved'
        assert ResourceListing.query.get(resource_id).quantity == 5

    login_as(client, volunteer)
    response = client.post(
        f'/volunteers/resource-requests/{request_id}/status',
        data={'new_status': 'Collected'},
        follow_redirects=True
    )
    assert response.status_code == 200
    response = client.post(
        f'/volunteers/resource-requests/{request_id}/status',
        data={'new_status': 'Delivered'},
        follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        assert ResourceRequest.query.get(request_id).status == 'Delivered'
        history = StatusHistory.query.filter_by(entity_type='ResourceRequest', entity_id=request_id).all()
        assert [entry.new_status for entry in history] == ['Pending', 'Approved', 'Collected', 'Delivered']


def test_oversized_duplicate_and_conflicting_approvals_do_not_overdraw_stock(client, app):
    with app.app_context():
        donor = create_user(role='donor', email='stock_donor@example.com')
        volunteer_one = create_user(role='volunteer', email='stock_volunteer1@example.com')
        volunteer_two = create_user(role='volunteer', email='stock_volunteer2@example.com')
        resource = create_resource(donor, quantity=5)
        resource_id = resource.id

    login_as(client, volunteer_one)
    response = client.post(f'/volunteers/resources/{resource_id}/request', data={'quantity': '6'}, follow_redirects=True)
    assert b'exceeds the available stock' in response.data
    with app.app_context():
        assert ResourceRequest.query.count() == 0

    client.post(f'/volunteers/resources/{resource_id}/request', data={'quantity': '4'})
    duplicate = client.post(f'/volunteers/resources/{resource_id}/request', data={'quantity': '1'}, follow_redirects=True)
    assert b'already have an active request' in duplicate.data

    login_as(client, volunteer_two)
    client.post(f'/volunteers/resources/{resource_id}/request', data={'quantity': '4'})
    with app.app_context():
        request_ids = [item.id for item in ResourceRequest.query.order_by(ResourceRequest.id).all()]

    login_as(client, donor)
    client.post(f'/donations/resource-requests/{request_ids[0]}/decision', data={'decision': 'approve'})
    conflict = client.post(
        f'/donations/resource-requests/{request_ids[1]}/decision',
        data={'decision': 'approve'},
        follow_redirects=True
    )
    assert b'not enough stock' in conflict.data
    with app.app_context():
        assert ResourceListing.query.get(resource_id).quantity == 1
        assert ResourceRequest.query.get(request_ids[0]).status == 'Approved'
        assert ResourceRequest.query.get(request_ids[1]).status == 'Pending'


def test_only_listing_donor_can_decide_and_only_requesting_volunteer_can_update(client, app):
    with app.app_context():
        donor = create_user(role='donor', email='owner_donor@example.com')
        other_donor = create_user(role='donor', email='other_donor@example.com')
        volunteer = create_user(role='volunteer', email='owner_volunteer@example.com')
        other_volunteer = create_user(role='volunteer', email='other_volunteer@example.com')
        resource = create_resource(donor)
        item_request = ResourceRequest(resource_id=resource.id, volunteer_id=volunteer.id, quantity=2)
        db.session.add(item_request)
        db.session.commit()
        resource_id = resource.id
        request_id = item_request.id

    login_as(client, other_donor)
    denied = client.post(f'/donations/resource-requests/{request_id}/decision', data={'decision': 'approve'}, follow_redirects=True)
    assert b'Only the listing donor' in denied.data
    with app.app_context():
        assert ResourceListing.query.get(resource_id).quantity == 8

    login_as(client, volunteer)
    client.post(f'/donations/resource-requests/{request_id}/decision', data={'decision': 'approve'})
    with app.app_context():
        assert ResourceRequest.query.get(request_id).status == 'Pending'

    login_as(client, other_volunteer)
    denied = client.post(
        f'/volunteers/resource-requests/{request_id}/status',
        data={'new_status': 'Collected'},
        follow_redirects=True
    )
    assert b'only update your own item requests' in denied.data
    with app.app_context():
        assert ResourceRequest.query.get(request_id).status == 'Pending'


def test_rejection_does_not_reserve_stock(client, app):
    with app.app_context():
        donor = create_user(role='donor', email='reject_donor@example.com')
        volunteer = create_user(role='volunteer', email='reject_volunteer@example.com')
        resource = create_resource(donor, quantity=5)
        item_request = ResourceRequest(resource_id=resource.id, volunteer_id=volunteer.id, quantity=3)
        db.session.add(item_request)
        db.session.commit()
        resource_id = resource.id
        request_id = item_request.id

    login_as(client, donor)
    response = client.post(
        f'/donations/resource-requests/{request_id}/decision',
        data={'decision': 'reject'},
        follow_redirects=True
    )
    assert response.status_code == 200
    with app.app_context():
        assert ResourceRequest.query.get(request_id).status == 'Rejected'
        assert ResourceListing.query.get(resource_id).quantity == 5