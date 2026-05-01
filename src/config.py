import json
import os
import sys


def get_data_dir():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        return os.path.join(base_dir, "data")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, "..", "data"))


DATA_DIR = get_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "emprestimos.csv")
DATE_FORMAT = "%d/%m/%Y"
DATE_FORMAT_ALT = "%Y-%m-%d"
_CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def _load_settings():
    try:
        with open(_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_settings = _load_settings()
EXP_DAYS = int(_settings.get("exp_days", 15))


def save_settings(exp_days):
    global EXP_DAYS
    EXP_DAYS = int(exp_days)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"exp_days": EXP_DAYS}, f)
