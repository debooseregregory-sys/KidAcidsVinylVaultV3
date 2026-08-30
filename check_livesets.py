import json

p = r".\data\livesets.json"

with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

print("BESTAND:", p)
print("TYPE:", type(data).__name__)

if isinstance(data, list):
    print("AANTAL LIVESETS:", len(data))
elif isinstance(data, dict):
    print("SLEUTELS:", list(data.keys()))
    for k, v in data.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)}")
