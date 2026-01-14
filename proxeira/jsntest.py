import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # project root
CONFIG_PATH = os.path.join(BASE_DIR, "../assets", "cfg.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

print(cfg["UPLOAD_URL_TESTING"])
print(CONFIG_PATH)
