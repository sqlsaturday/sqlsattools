"""
Load 1137.json into SQL Server.
Run from the dataloader directory: python load_1137.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import SQLSatDataLoader

loader = SQLSatDataLoader()
print("Server  :", loader.server)
print("Database:", loader.database)
print("User    :", loader.username)
print()

if not loader.connect():
    print("ERROR: Connection failed. Check SQL Server is running and credentials are correct.")
    sys.exit(1)

try:
    dataloader_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(dataloader_dir, "..", "raw", "json", "sqlsat1137.json")
    json_path = os.path.abspath(json_path)
    print("File:", json_path)
    result = loader.process_file(json_path)
    print()
    if result:
        print("SUCCESS: 1137.json loaded successfully.")
    else:
        print("ERROR: Load failed - check output above for details.")
        sys.exit(1)
finally:
    loader.disconnect()
