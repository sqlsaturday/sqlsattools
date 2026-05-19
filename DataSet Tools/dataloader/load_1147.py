"""
Loader for sqlsat1147.json — which is actually a plain-text schedule, not JSON.

Parses the text format:
    SQL Saturday Arequipa 2026 (#1147)
    Apr 25, 2026
    Arequipa, Peru

    8:30 am
    Auditorio
    8:30 am → 30 min
    Session Title

        Speaker Name

and loads it into SQL Server using the same connection as the main loader.
"""

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import SQLSatDataLoader

# ---------------------------------------------------------------------------
# File path
# ---------------------------------------------------------------------------
_script_dir  = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE  = os.path.abspath(
    os.path.join(_script_dir, "..", "raw", "json", "sqlsat1147.json")
)
SOURCE_NAME  = "sqlsat1147.json"

# Titles that should be flagged as service sessions
SERVICE_TITLES = {"keynote", "break", "lunch", "registration", "cierre", "almuerzo", "apertura"}

# Regex patterns
TIME_ONLY     = re.compile(r'^\d{1,2}:\d{2}\s*(am|pm)$',    re.IGNORECASE)
TIME_DURATION = re.compile(r'^\d{1,2}:\d{2}\s*(am|pm)\s*→', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_text_schedule(filepath):
    """Parse the plain-text schedule into the dict format load_data.py expects."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        lines = [l.rstrip("\r\n") for l in f.readlines()]

    # --- Header (first 3 lines) ---
    event_name = lines[0].strip()
    date_str   = lines[1].strip()   # e.g. "Apr 25, 2026"
    location   = lines[2].strip()

    try:
        event_date = datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        event_date = "1900-01-01"
        print(f"  Warning: could not parse date '{date_str}', defaulting to 1900-01-01")

    # --- Sessions ---
    sessions = []
    i = 3   # start after header; non-time lines (e.g. stray "Auditorio") are skipped

    while i < len(lines):
        line = lines[i].strip()

        # Only start a block on a bare time line ("8:30 am"), not "8:30 am → 30 min"
        if TIME_ONLY.match(line) and not TIME_DURATION.match(line):
            time_str = line
            i += 1

            # Room name
            room = lines[i].strip() if i < len(lines) else ""
            i += 1

            # "time → duration" line — skip it
            if i < len(lines) and TIME_DURATION.match(lines[i].strip()):
                i += 1

            # Session title
            title = lines[i].strip() if i < len(lines) else ""
            i += 1

            # Optional speaker: blank line then indented name then blank line
            speaker = None
            if i < len(lines) and lines[i].strip() == "":
                i += 1
                if i < len(lines) and lines[i] and lines[i][0] in (" ", "\t"):
                    speaker = lines[i].strip()
                    i += 1
                    if i < len(lines) and lines[i].strip() == "":
                        i += 1

            is_service = title.lower() in SERVICE_TITLES

            sessions.append({
                "time":     time_str,
                "title":    title,
                "type":     "break" if is_service else "session",
                "speakers": [speaker] if speaker else [],
            })
        else:
            i += 1

    return {
        "eventName": event_name,
        "eventDate": event_date,
        "location":  location,
        "sessions":  sessions,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("SQL Saturday Loader — sqlsat1147 (plain-text format)")
    print("=" * 60)
    print(f"File: {SOURCE_FILE}")
    print()

    if not os.path.exists(SOURCE_FILE):
        print(f"ERROR: File not found:\n       {SOURCE_FILE}")
        sys.exit(1)

    data = parse_text_schedule(SOURCE_FILE)
    print(f"Parsed event : {data['eventName']}")
    print(f"Date         : {data['eventDate']}")
    print(f"Location     : {data['location']}")
    print(f"Sessions     : {len(data['sessions'])}")
    print()

    loader = SQLSatDataLoader()
    if not loader.connect():
        print("ERROR: Could not connect to database.")
        sys.exit(1)

    try:
        event_id = loader.insert_event(data, SOURCE_NAME)
        if not event_id:
            print("ERROR: Failed to insert event.")
            sys.exit(1)

        loader.insert_sessions(data["sessions"], event_id)

    finally:
        loader.disconnect()

    print()
    print("SUCCESS: sqlsat1147 loaded.")


if __name__ == "__main__":
    main()
