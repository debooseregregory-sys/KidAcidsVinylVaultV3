from database.database import get_connection
conn = get_connection()
rows = conn.execute('SELECT id, artist, title, checked FROM releases ORDER BY id DESC LIMIT 15').fetchall()
for r in rows:
    print(f'id={r[0]}  checked={r[3]}  {r[1]} - {r[2]}')
conn.close()
