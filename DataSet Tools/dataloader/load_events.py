"""
SQL Saturday - Load specific event JSON files into SQL Server.
Edit the FILES list below to control which events are loaded.

Usage:
    python load_events.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import SQLSatDataLoader

# ---------------------------------------------------------------------------
# Files to load  (relative to raw/json/)
# ---------------------------------------------------------------------------
FILES = [
    "sqlsat1128.json",
    "sqlsat1135.json",
    "sqlsat1139.json",
    "sqlsat1140.json",
    "sqlsat1145.json",
    "sqlsat1147.json",
]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
JSON_DIR    = os.path.abspath(os.path.join(_script_dir, "..", "raw", "json"))

print("=" * 60)
print("SQL Saturday Event Loader")
print("=" * 60)

loader = SQLSatDataLoader()
if not loader.connect():
    print("ERROR: Could not connect to database.")
    sys.exit(1)

success = 0
errors  = 0
missing = 0

try:
    for filename in FILES:
        path = os.path.join(JSON_DIR, filename)
        if not os.path.exists(path):
            print(f"\nSKIPPED (file not found): {filename}")
            missing += 1
            continue
        if loader.process_file(path):
            success += 1
        else:
            errors += 1
finally:
    loader.disconnect()

print()
print("=" * 60)
print(f"Complete — Loaded: {success}  Errors: {errors}  Missing: {missing}")
print("=" * 60)
