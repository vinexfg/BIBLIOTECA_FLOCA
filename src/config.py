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
EXP_DAYS = 15
