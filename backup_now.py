import shutil, datetime, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "daily_backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

files_to_backup = ["vinylvault.db", "livesets.json"]

for fname in files_to_backup:
    source = os.path.join(DATA_DIR, fname)
    if os.path.exists(source):
        name, ext = os.path.splitext(fname)
        dest = os.path.join(BACKUP_DIR, f"{name}_{timestamp}{ext}")
        shutil.copy2(source, dest)
        print(f"Backup gemaakt: {dest}")
    else:
        print(f"Waarschuwing: {source} bestaat niet, overgeslagen.")

# Oude backups opruimen: bewaar alleen de laatste 30 per bestand
for fname in files_to_backup:
    name, ext = os.path.splitext(fname)
    matching = sorted([
        f for f in os.listdir(BACKUP_DIR) if f.startswith(name + "_") and f.endswith(ext)
    ])
    if len(matching) > 30:
        for old in matching[:-30]:
            os.remove(os.path.join(BACKUP_DIR, old))
            print(f"Oude backup verwijderd: {old}")

print("Klaar.")
