"""
Load a single SQL Saturday JSON file into the database.
Usage:  python load_single.py [filename]
Default file: sqlsat1142.json

Run this from the dataloader directory:
    cd "DataSet Tools\dataloader"
    python load_single.py
"""

import os
import sys

# Allow importing from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import SQLSatDataLoader

def main():
    # Which file to load — default to sqlsat1142.json
    target_file = sys.argv[1] if len(sys.argv) > 1 else "sqlsat1142.json"

    # Resolve path relative to the raw/json directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir    = os.path.join(os.path.dirname(current_dir), 'raw', 'json')
    file_path   = os.path.join(json_dir, target_file)

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"SQL Saturday Data Loader — single file")
    print(f"Target: {target_file}")
    print("=" * 60)

    loader = SQLSatDataLoader()

    if not loader.connect():
        print("Failed to connect to database. Exiting.")
        sys.exit(1)

    try:
        success = loader.process_file(file_path)
        print("\n" + "=" * 60)
        print("Done!" if success else "Finished with errors — check output above.")
        print("=" * 60)
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()
