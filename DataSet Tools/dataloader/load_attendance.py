"""
SQL Saturday Attendance Loader
Loads registered and attended counts from CSV files into the Events table.

CSV formats handled:
  - 2022-2023: Event, Event Number, EventDate, Registered, Attended, ...
  - 2024-2026: Date, Event, Registered, Attended, ... (event number in event name)

Matches events by extracting the event number from the CSV and comparing
against the SourceFile column in the Events table (e.g. 'sqlsat1022.json').
"""

import os
import csv
import re
import pyodbc
from dotenv import load_dotenv

load_dotenv()


class AttendanceLoader:
    def __init__(self):
        self.server = os.getenv('DB_SERVER', r'Aristotle\SQL2022')
        self.database = os.getenv('DB_NAME', 'sqlsatdata')
        self.username = os.getenv('DB_USER', '')
        self.password = os.getenv('DB_PASSWORD', '')

        if self.username and self.password:
            self.conn_string = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'UID={self.username};'
                f'PWD={self.password}'
            )
        else:
            self.conn_string = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'Trusted_Connection=yes'
            )
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = pyodbc.connect(self.conn_string)
            self.cursor = self.conn.cursor()
            print(f"Connected to {self.server}/{self.database}")
            return True
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")

    def parse_int(self, value):
        """Parse an integer from a CSV value, handling commas and empty strings."""
        if not value or not value.strip():
            return None
        # Remove commas (e.g. "1,300") and surrounding whitespace
        cleaned = value.strip().replace(',', '')
        try:
            return int(cleaned)
        except ValueError:
            return None

    def extract_event_number(self, row, headers):
        """Extract the event number from a CSV row.

        2022-2023 format: explicit 'Event Number' column
        2024-2026 format: embedded in event name as (#1075) or (1075)
        """
        # Check for explicit Event Number column
        if 'Event Number' in headers:
            val = row.get('Event Number', '').strip()
            if val:
                try:
                    return int(val)
                except ValueError:
                    pass

        # Extract from Event name - look for (#number) or (number)
        event_name = row.get('Event', '').strip()
        match = re.search(r'\(#?(\d{4,5})\)', event_name)
        if match:
            return int(match.group(1))

        return None

    def parse_csv(self, file_path):
        """Parse a CSV file and return attendance records as (event_number, registered, attended)."""
        records = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            for row in reader:
                event_number = self.extract_event_number(row, headers)
                if not event_number:
                    continue

                registered = self.parse_int(row.get('Registered', ''))
                attended = self.parse_int(row.get('Attended', ''))

                # Skip rows where both values are missing
                if registered is None and attended is None:
                    continue

                records.append((event_number, registered, attended))

        return records

    def update_events(self, records):
        """Update the Events table with attendance data.

        Matches on SourceFile containing the event number.
        If multiple CSV rows share an event number, sums the values.
        """
        # Aggregate by event number (some events have in-person + virtual rows)
        aggregated = {}
        for event_number, registered, attended in records:
            if event_number not in aggregated:
                aggregated[event_number] = {'registered': None, 'attended': None}
            entry = aggregated[event_number]
            if registered is not None:
                entry['registered'] = (entry['registered'] or 0) + registered
            if attended is not None:
                entry['attended'] = (entry['attended'] or 0) + attended

        update_query = """
            UPDATE dbo.Events
            SET RegisteredCount = ?, AttendedCount = ?
            WHERE SourceFile LIKE ?;
        """

        updated = 0
        not_found = 0
        for event_number, values in sorted(aggregated.items()):
            # Match SourceFile pattern like 'sqlsat1022.json' or 'SQLSat1022.json'
            pattern = f'%{event_number}%'

            self.cursor.execute(
                "SELECT COUNT(*) FROM dbo.Events WHERE SourceFile LIKE ?",
                pattern
            )
            count = self.cursor.fetchone()[0]

            if count == 0:
                print(f"  No event found for event number {event_number}")
                not_found += 1
                continue

            self.cursor.execute(
                update_query,
                values['registered'],
                values['attended'],
                pattern
            )
            self.conn.commit()
            updated += 1
            print(f"  Updated event {event_number}: "
                  f"registered={values['registered']}, attended={values['attended']}")

        return updated, not_found

    def process_directory(self, csv_dir):
        """Process all attendance CSV files in a directory."""
        if not os.path.exists(csv_dir):
            print(f"Directory not found: {csv_dir}")
            return

        csv_files = sorted(f for f in os.listdir(csv_dir)
                           if f.lower().endswith('.csv') and 'attendance' in f.lower())

        if not csv_files:
            print(f"No attendance CSV files found in: {csv_dir}")
            return

        print(f"Found {len(csv_files)} attendance CSV files")

        total_updated = 0
        total_not_found = 0

        for csv_file in csv_files:
            file_path = os.path.join(csv_dir, csv_file)
            print(f"\nProcessing: {csv_file}")

            records = self.parse_csv(file_path)
            print(f"  Parsed {len(records)} attendance records")

            updated, not_found = self.update_events(records)
            total_updated += updated
            total_not_found += not_found

        print(f"\n{'='*60}")
        print(f"Attendance loading complete!")
        print(f"Events updated: {total_updated}")
        print(f"Events not found in database: {total_not_found}")
        print(f"{'='*60}")


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(os.path.dirname(current_dir), 'raw', 'csv')

    print("=" * 60)
    print("SQL Saturday Attendance Loader")
    print("=" * 60)

    loader = AttendanceLoader()

    if not loader.connect():
        print("Failed to connect to database. Exiting.")
        return

    try:
        loader.process_directory(csv_dir)
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()
