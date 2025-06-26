import json

path = "pipeline_1_product_to_stories/generated_stories.json"

with open(path, "rb") as f:
    raw = f.read()
    print("First 20 bytes:", raw[:20])  # Show if BOM or non-printables exist

try:
    text = raw.decode("utf-8")
    data = json.loads(text)
    print("✅ JSON successfully loaded. Top-level keys:", list(data.keys()))
except UnicodeDecodeError as e:
    print("❌ Unicode decode error:", e)
except json.JSONDecodeError as e:
    print("❌ JSON decode error:", e)