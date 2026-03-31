import psycopg2
conn = psycopg2.connect("postgresql://dwh:DBTTEST@localhost:5432/dwh")
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='RACINGAPP' ORDER BY table_name")
print('\n'.join(row[0] for row in cur.fetchall()))
cur.execute('SELECT COUNT(*) FROM "RACINGAPP"."SERIESCONTROL"')
print(f'SERIESCONTROL rows: {cur.fetchone()[0]}')
cur.close()
conn.close()
