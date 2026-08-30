from database.database import get_connection

c = get_connection()

print("=" * 50)
print("VINYLVAULT DATABASE CONTROLE")
print("=" * 50)

# Totalen
total = c.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
checked1 = c.execute("SELECT COUNT(*) FROM releases WHERE checked = 1").fetchone()[0]
checked0 = c.execute("SELECT COUNT(*) FROM releases WHERE checked = 0 OR checked IS NULL").fetchone()[0]
tracks = c.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
mp3s = c.execute("SELECT COUNT(*) FROM mp3_files").fetchone()[0]

print(f"Totaal releases     : {total}")
print(f"Checked = 1 (KLAAR) : {checked1}")
print(f"Checked = 0         : {checked0}")
print(f"Totaal tracks       : {tracks}")
print(f"Totaal mp3 bestanden: {mp3s}")
print()

# Laatste 10 met checked=1
print("Laatste 10 KLAAR-releases (hoogste id):")
print("-" * 50)
rows = c.execute("""
    SELECT id, artist, title, checked
    FROM releases
    WHERE checked = 1
    ORDER BY id DESC
    LIMIT 10
""").fetchall()

for r in rows:
    print(f"  id={r[0]:<6}  {r[1]} - {r[2]}")

print()
print("Laatste 10 releases in database (alle status):")
print("-" * 50)
rows = c.execute("""
    SELECT id, artist, title, checked
    FROM releases
    ORDER BY id DESC
    LIMIT 10
""").fetchall()

for r in rows:
    status = "KLAAR" if r[3] == 1 else "todo"
    print(f"  id={r[0]:<6}  [{status}]  {r[1]} - {r[2]}")

c.close()
print("=" * 50)
