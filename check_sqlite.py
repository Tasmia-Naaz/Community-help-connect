
import sqlite3
from pathlib import Path

db_path = Path("instance/community_help.db")

print("SQLite file exists:", db_path.exists())

if db_path.exists():
    con = sqlite3.connect(str(db_path))

    tables = con.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    print("\nTables in SQLite:")
    for table in tables:
        print("-", table[0])

    print("\nRecord counts:")
    for table in tables:
        table_name = table[0]
        count = con.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
        print(f"- {table_name}: {count}")

    con.close()
else:
    print("Database file not found. Check the file path.")
