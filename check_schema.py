#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect('postgresql://dwh:DBTTEST@localhost:5432/dwh')
cur = conn.cursor()

# Check if schema exists
cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='RACINGAPP');")
schema_exists = cur.fetchone()[0]
print(f"RACINGAPP schema exists: {schema_exists}")

if schema_exists:
    # List tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='RACINGAPP' ORDER BY table_name;")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables ({len(tables)}):")
    for t in tables:
        print(f"  - {t}")

conn.close()
