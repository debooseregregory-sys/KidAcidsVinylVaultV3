import json
with open("data/livesets.json", encoding="utf-8") as f:
    d = json.load(f)
old = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3"
new = r"C:\Users\andyb\Desktop\My Vinyl & MusicVault\KidAcidsVinylVaultV3"
count = 0
for item in d:
    cov = item.get("cover", "")
    if cov.startswith(old):
        item["cover"] = cov.replace(old, new, 1)
        count += 1
with open("data/livesets.json", "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print("Aangepast:", count)
