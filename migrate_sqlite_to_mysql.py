import sqlite3
from pathlib import Path

from sqlalchemy import inspect
from app import create_app
from models import db

SQLITE_PATH = Path("instance/community_help.db")

# Copy tables in foreign-key dependency order.
TABLE_ORDER = [
    "users",
    "help_requests",
    "resource_listings",
    "resource_requests",
    "notifications",
    "emergency_events",
    "status_history",
]


def main():
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_PATH.resolve()}"
        )

    # Open the existing SQLite database as read-only.
    source = sqlite3.connect(
        f"file:{SQLITE_PATH.resolve().as_posix()}?mode=ro",
        uri=True,
    )
    source.row_factory = sqlite3.Row

    app = create_app()

    try:
        with app.app_context():
            engine = db.engine
            inspector = inspect(engine)

            existing_tables = set(inspector.get_table_names())
            if existing_tables:
                raise RuntimeError(
                    "MySQL already contains tables: "
                    + ", ".join(sorted(existing_tables))
                    + ". Stopping without changing anything."
                )

            source_tables = {
                row["name"]
                for row in source.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type = 'table'
                    AND name NOT LIKE 'sqlite_%'
                    """
                )
            }

            missing = set(TABLE_ORDER) - source_tables
            if missing:
                raise RuntimeError(
                    f"SQLite is missing expected tables: {sorted(missing)}"
                )

            print("Creating MySQL tables...")
            db.create_all()

            target_tables = set(inspect(engine).get_table_names())
            missing_targets = set(TABLE_ORDER) - target_tables
            if missing_targets:
                raise RuntimeError(
                    f"Some MySQL tables were not created: {sorted(missing_targets)}"
                )

            counts = {}
            with engine.begin() as destination:
                for table in TABLE_ORDER:
                    rows = source.execute(
                        f'SELECT * FROM "{table}"'
                    ).fetchall()

                    counts[table] = len(rows)
                    if not rows:
                        print(f"{table}: 0 records")
                        continue

                    column_names = rows[0].keys()
                    records = [
                        {column: row[column] for column in column_names}
                        for row in rows
                    ]

                    destination.execute(
                        db.metadata.tables[table].insert(),
                        records,
                    )
                    print(f"{table}: copied {len(records)} records")

            print("\nVerifying record counts...")
            with engine.connect() as destination:
                for table in TABLE_ORDER:
                    target_count = destination.execute(
                        db.select(db.func.count()).select_from(
                            db.metadata.tables[table]
                        )
                    ).scalar_one()

                    print(
                        f"{table}: SQLite={counts[table]}, "
                        f"MySQL={target_count}"
                    )

                    if counts[table] != target_count:
                        raise RuntimeError(
                            f"Record count mismatch in {table}!"
                        )

            print("\nMigration completed and record counts match.")

    finally:
        source.close()


if __name__ == "__main__":
    main()
