#!/usr/bin/env python3
import psycopg2
import sys

conn = psycopg2.connect('postgresql://dwh:DBTTEST@localhost:5432/dwh')
cur = conn.cursor()

# Read and execute init.sql
try:
    with open('init.d/init.sql', 'r') as f:
        sql = f.read()
    # Split by semicolons and execute each statement
    statements = sql.split(';')
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit()
    print("✓ Schema initialized")
except Exception as e:
    print(f"✗ Error initializing schema: {e}")
    conn.rollback()
finally:
    cur.close()

# Seed test data
try:
    with open('minimal_test_data.sql', 'r') as f:
        sql = f.read()
    statements = sql.split(';')
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit()
    print("✓ Test data seeded")
except Exception as e:
    print(f"✗ Error seeding test data: {e}")
    conn.rollback()
finally:
    conn.close()
