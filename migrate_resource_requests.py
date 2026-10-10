"""Add volunteer resource requests and optional names to existing listings."""

from sqlalchemy import inspect, text

from app import create_app
from extensions import db
from models import ResourceRequest


def migrate_resource_requests():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        if 'name' not in {column['name'] for column in inspector.get_columns('resource_listings')}:
            with db.engine.begin() as connection:
                connection.execute(text('ALTER TABLE resource_listings ADD COLUMN name VARCHAR(150) NULL'))

        db.metadata.create_all(bind=db.engine, tables=[ResourceRequest.__table__])
        print('Resource request schema is ready. Existing resource listings were preserved.')


if __name__ == '__main__':
    migrate_resource_requests()