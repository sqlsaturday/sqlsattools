"""
SQL Saturday Job Loader
Loads job title attendance data from sqlsat1137_jobs.json into:
  dbo.JobTitles      - master list of distinct job titles (insert if not exists)
  dbo.EventJobTitles - per-event attendee counts by job title

Usage:
    python load_jobs.py [json_file]

    json_file defaults to ..\raw\json\sqlsat1137_jobs.json

Connection: Windows Authentication to (local)\SQL2022, database sqlsatdata
"""

import sys
import os
import json
import pyodbc

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVER      = r"(local)\SQL2022"
DATABASE    = "sqlsatdata"
EVENT_NUMBER = 1137

_script_dir  = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.abspath(
    os.path.join(_script_dir, "..", "raw", "json", "sqlsat1137_jobs.json")
)

TITLE_MAX_LEN = 100   # dbo.JobTitles.Title is NVARCHAR(100)


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def connect():
    """Return a pyodbc connection using Windows Authentication."""
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server",
    ]
    for driver in drivers_to_try:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        try:
            conn = pyodbc.connect(conn_str)
            print(f"Connected to {SERVER}/{DATABASE} using '{driver}' (Windows Auth)")
            return conn
        except pyodbc.Error:
            continue

    print("ERROR: Could not connect to the database with any available ODBC driver.")
    print(f"       Tried: {', '.join(drivers_to_try)}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Event lookup
# ---------------------------------------------------------------------------

def get_event_id(cursor):
    """Look up EventID from dbo.Events by EventNumber."""
    cursor.execute(
        "SELECT EventID, EventName FROM dbo.Events WHERE EventNumber = ?",
        EVENT_NUMBER
    )
    row = cursor.fetchone()
    if not row:
        # Fallback: try matching by SourceFile
        cursor.execute(
            "SELECT EventID, EventName FROM dbo.Events WHERE SourceFile = ?",
            f"sqlsat{EVENT_NUMBER}.json"
        )
        row = cursor.fetchone()

    if not row:
        print(f"ERROR: No event found for EventNumber {EVENT_NUMBER}.")
        print("       Make sure sqlsat1137.json has been loaded first.")
        sys.exit(1)

    print(f"Event found: [{row.EventID}] {row.EventName}")
    return row.EventID


# ---------------------------------------------------------------------------
# JobTitles helpers
# ---------------------------------------------------------------------------

def get_or_create_job_title(cursor, conn, title):
    """
    Return (JobTitleID, was_inserted) for *title*.
    Inserts into dbo.JobTitles if the title does not already exist.
    Truncates to TITLE_MAX_LEN characters if needed.
    """
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN]

    cursor.execute(
        "SELECT JobTitleID FROM dbo.JobTitles WHERE Title = ?",
        title
    )
    row = cursor.fetchone()
    if row:
        return row.JobTitleID, False

    cursor.execute(
        "INSERT INTO dbo.JobTitles (Title) OUTPUT INSERTED.JobTitleID VALUES (?)",
        title
    )
    new_id = cursor.fetchone()[0]
    conn.commit()
    return new_id, True


# ---------------------------------------------------------------------------
# EventJobTitles helpers
# ---------------------------------------------------------------------------

def insert_event_job_title(cursor, conn, event_id, job_title_id, count):
    """
    Insert a row into dbo.EventJobTitles for this event + job title.
    Skips (returns False) if the combination already exists.
    """
    cursor.execute(
        """
        SELECT 1
        FROM   dbo.EventJobTitles
        WHERE  EventID = ? AND JobTitleID = ?
        """,
        event_id, job_title_id
    )
    if cursor.fetchone():
        return False

    cursor.execute(
        """
        INSERT INTO dbo.EventJobTitles (EventID, JobTitleID, AttendanceCount)
        VALUES (?, ?, ?)
        """,
        event_id, job_title_id, count
    )
    conn.commit()
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_jobs(json_path):
    print("=" * 60)
    print("SQL Saturday Job Loader")
    print("=" * 60)
    print(f"File: {json_path}")
    print()

    if not os.path.exists(json_path):
        print(f"ERROR: File not found:\n       {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    if not jobs:
        print("ERROR: No 'jobs' array found in the JSON file.")
        sys.exit(1)

    print(f"Found {len(jobs)} job entries.")
    print()

    conn   = connect()
    cursor = conn.cursor()

    event_id = get_event_id(cursor)
    print()

    titles_inserted = 0
    titles_existing = 0
    events_inserted = 0
    events_skipped  = 0

    for entry in jobs:
        title = entry.get("title", "").strip()
        count = entry.get("count", 0)

        if not title:
            continue

        # Step 1: ensure the job title exists in the master table
        job_title_id, was_inserted = get_or_create_job_title(cursor, conn, title)
        if was_inserted:
            titles_inserted += 1
            print(f"  [NEW]    '{title}'  →  JobTitleID {job_title_id}")
        else:
            titles_existing += 1
            print(f"  [EXISTS] '{title}'  →  JobTitleID {job_title_id}")

        # Step 2: record the count against this event
        inserted = insert_event_job_title(cursor, conn, event_id, job_title_id, count)
        if inserted:
            events_inserted += 1
            print(f"           EventJobTitle inserted  (count={count})")
        else:
            events_skipped += 1
            print(f"           EventJobTitle already exists, skipped.")

    print()
    print("=" * 60)
    print("Done!")
    print(f"  Job titles inserted  : {titles_inserted}")
    print(f"  Job titles existing  : {titles_existing}")
    print(f"  Event rows inserted  : {events_inserted}")
    print(f"  Event rows skipped   : {events_skipped}")
    print("=" * 60)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    load_jobs(os.path.abspath(path))
