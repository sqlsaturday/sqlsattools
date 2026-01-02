"""
SQL Saturday Data Loader
Loads event data from JSON files into SQL Server database
"""

import os
import json
import pyodbc
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SQLSatDataLoader:
    def __init__(self):
        """Initialize database connection"""
        self.server = os.getenv('DB_SERVER', r'Aristotle\SQL2022')
        self.database = os.getenv('DB_NAME', 'sqlsatdata')
        self.username = os.getenv('DB_USER', 'sqlsatdata')
        self.password = os.getenv('DB_PASSWORD', 'Demo12#4')

        self.conn_string = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password}'
        )

        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = pyodbc.connect(self.conn_string)
            self.cursor = self.conn.cursor()
            print(f"Connected to {self.server}/{self.database}")
            return True
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")

    def load_json_file(self, file_path):
        """Load and parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def insert_event(self, event_data, source_file):
        """Insert event record and return EventID"""
        try:
            # Extract event metadata with defaults for missing values
            event_name = event_data.get('eventName') or f"SQL Saturday Event - {source_file}"
            event_date = event_data.get('eventDate') or '1900-01-01'
            location = event_data.get('location') or 'Unknown Location'

            query = """
                INSERT INTO dbo.Events (EventName, EventDate, Location, SourceFile)
                OUTPUT INSERTED.EventID
                VALUES (?, ?, ?, ?);
            """

            self.cursor.execute(query,
                              event_name,
                              event_date,
                              location,
                              source_file)

            row = self.cursor.fetchone()
            if not row:
                raise Exception("Failed to retrieve EventID after insert")
            event_id = row[0]
            self.conn.commit()
            print(f"  Inserted event: {event_name} (ID: {event_id})")
            return int(event_id)
        except pyodbc.Error as e:
            print(f"  Error inserting event: {e}")
            self.conn.rollback()
            return None

    def insert_rooms(self, rooms, event_id):
        """Insert room records"""
        if not rooms:
            return

        try:
            query = """
                INSERT INTO dbo.Rooms (RoomID, EventID, RoomName, SortOrder)
                VALUES (?, ?, ?, ?);
            """

            room_count = 0
            for i, room in enumerate(rooms):
                # Handle both dict and non-dict formats
                if isinstance(room, dict):
                    room_id = room.get('id')
                    room_name = room.get('name', f'Room {i+1}')
                    sort_order = room.get('sort', i)
                else:
                    # Skip non-dict entries
                    continue

                if room_id:
                    self.cursor.execute(query, room_id, event_id, room_name, sort_order)
                    room_count += 1

            self.conn.commit()
            if room_count > 0:
                print(f"  Inserted {room_count} rooms")
        except pyodbc.Error as e:
            print(f"  Error inserting rooms: {e}")
            self.conn.rollback()

    def get_or_create_speaker_id(self, speaker_name, event_id):
        """Get or create a speaker ID from a speaker name"""
        # Generate a simple ID from the name
        speaker_id = speaker_name.lower().replace(' ', '-').replace('.', '')

        # Check if speaker already exists
        check_query = "SELECT COUNT(*) FROM dbo.Speakers WHERE SpeakerID = ?"
        self.cursor.execute(check_query, speaker_id)
        exists = self.cursor.fetchone()[0] > 0

        if not exists:
            # Create the speaker
            insert_query = """
                INSERT INTO dbo.Speakers
                (SpeakerID, EventID, FirstName, LastName, FullName, Bio, TagLine, ProfilePicture, IsTopSpeaker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            try:
                # Split name into first and last
                parts = speaker_name.split(' ', 1)
                first_name = parts[0] if len(parts) > 0 else speaker_name
                last_name = parts[1] if len(parts) > 1 else ''

                self.cursor.execute(insert_query,
                                  speaker_id,
                                  event_id,
                                  first_name,
                                  last_name,
                                  speaker_name,
                                  None,  # bio
                                  None,  # tagLine
                                  None,  # profilePicture
                                  False)  # isTopSpeaker
                self.conn.commit()
            except:
                self.conn.rollback()

        return speaker_id

    def insert_speakers(self, speakers, event_id):
        """Insert speaker records"""
        if not speakers:
            return

        query = """
            INSERT INTO dbo.Speakers
            (SpeakerID, EventID, FirstName, LastName, FullName, Bio, TagLine, ProfilePicture, IsTopSpeaker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        speaker_count = 0
        for speaker in speakers:
            # Skip non-dict entries
            if not isinstance(speaker, dict):
                continue

            speaker_id = speaker.get('id')
            if not speaker_id:
                continue

            try:
                self.cursor.execute(query,
                                  speaker_id,
                                  event_id,
                                  speaker.get('firstName'),
                                  speaker.get('lastName'),
                                  speaker.get('fullName'),
                                  speaker.get('bio'),
                                  speaker.get('tagLine'),
                                  speaker.get('profilePicture'),
                                  speaker.get('isTopSpeaker', False))
                self.conn.commit()
                speaker_count += 1
            except pyodbc.Error as e:
                # Skip duplicates (speakers can appear in multiple events)
                if '2627' in str(e):  # Primary key violation
                    continue
                else:
                    print(f"  Error inserting speaker {speaker_id}: {e}")
                self.conn.rollback()

        if speaker_count > 0:
            print(f"  Inserted {speaker_count} speakers")

    def normalize_schedule_entry(self, schedule_entry, event_id, index):
        """Convert schedule entry format to session format"""
        # Generate a unique session ID
        session_id = f"{event_id}_{index:04d}"

        # Create normalized session
        session = {
            'id': session_id,
            'title': schedule_entry.get('title', ''),
            'description': schedule_entry.get('description', ''),
            'startsAt': None,  # We don't have exact datetime from timeSlot
            'endsAt': None,
            'isServiceSession': schedule_entry.get('sessionType') in ['registration', 'break', 'lunch'],
            'isPlenumSession': False,
            'speakers': schedule_entry.get('speakers', []),
            'roomId': None,
            'liveUrl': None,
            'recordingUrl': None
        }

        return session

    def insert_sessions(self, sessions, event_id):
        """Insert session records and session-speaker relationships"""
        if not sessions:
            return

        session_query = """
            INSERT INTO dbo.Sessions
            (SessionID, EventID, Title, Description, StartsAt, EndsAt,
             IsServiceSession, IsPlenumSession, RoomID, LiveUrl, RecordingUrl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        speaker_query = """
            INSERT INTO dbo.SessionSpeakers (SessionID, SpeakerID)
            VALUES (?, ?);
        """

        session_count = 0
        speaker_link_count = 0

        for idx, session in enumerate(sessions):
            # Skip non-dict entries
            if not isinstance(session, dict):
                continue

            # Check if this is a 'schedule' format (has timeSlot/time instead of id)
            if ('timeSlot' in session or 'time' in session) and 'id' not in session:
                # Normalize different field names
                if 'time' in session:
                    session['timeSlot'] = session.pop('time')
                if 'type' in session:
                    session['sessionType'] = session.pop('type')
                session = self.normalize_schedule_entry(session, event_id, idx)

            session_id = session.get('id')
            if not session_id:
                continue

            # Insert session
            try:
                self.cursor.execute(session_query,
                                  session_id,
                                  event_id,
                                  session.get('title'),
                                  session.get('description'),
                                  session.get('startsAt'),
                                  session.get('endsAt'),
                                  session.get('isServiceSession', False),
                                  session.get('isPlenumSession', False),
                                  session.get('roomId'),
                                  session.get('liveUrl'),
                                  session.get('recordingUrl'))
                self.conn.commit()
                session_count += 1

                # Insert session-speaker relationships
                speakers = session.get('speakers', [])
                for speaker_ref in speakers:
                    # Handle different speaker reference formats
                    if isinstance(speaker_ref, dict):
                        speaker_id = speaker_ref.get('id')
                    elif isinstance(speaker_ref, str):
                        # Check if this looks like a name (has space) vs an ID
                        if ' ' in speaker_ref or speaker_ref[0].isupper():
                            # It's a name, create/get speaker ID
                            speaker_id = self.get_or_create_speaker_id(speaker_ref, event_id)
                        else:
                            # It's already an ID
                            speaker_id = speaker_ref
                    else:
                        continue

                    if not speaker_id:
                        continue

                    try:
                        self.cursor.execute(speaker_query, session_id, speaker_id)
                        self.conn.commit()
                        speaker_link_count += 1
                    except pyodbc.Error:
                        # Skip if relationship already exists or speaker doesn't exist
                        self.conn.rollback()
                        pass

            except pyodbc.Error as e:
                # Skip duplicate sessions
                if '2627' in str(e):  # Primary key violation
                    self.conn.rollback()
                    continue
                else:
                    print(f"  Error inserting session {session_id}: {e}")
                    self.conn.rollback()

        if session_count > 0:
            print(f"  Inserted {session_count} sessions with {speaker_link_count} speaker links")

    def process_file(self, file_path):
        """Process a single JSON file"""
        file_name = os.path.basename(file_path)
        print(f"\nProcessing: {file_name}")

        # Load JSON data
        data = self.load_json_file(file_path)
        if not data:
            return False

        # Insert event
        event_id = self.insert_event(data, file_name)
        if not event_id:
            return False

        # Insert related data
        # Handle both 'rooms' array formats (strings or objects)
        self.insert_rooms(data.get('rooms', []), event_id)

        # Handle both 'speakers' and extract from 'schedule' if needed
        speakers = data.get('speakers', [])
        self.insert_speakers(speakers, event_id)

        # Handle both 'sessions' and 'schedule' keys
        sessions = data.get('sessions', data.get('schedule', []))
        self.insert_sessions(sessions, event_id)

        return True

    def process_directory(self, directory_path):
        """Process all JSON files in a directory"""
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return

        json_files = [f for f in os.listdir(directory_path)
                     if f.endswith('.json')]

        if not json_files:
            print(f"No JSON files found in: {directory_path}")
            return

        print(f"\nFound {len(json_files)} JSON files to process")

        success_count = 0
        error_count = 0

        for json_file in sorted(json_files):
            file_path = os.path.join(directory_path, json_file)
            if self.process_file(file_path):
                success_count += 1
            else:
                error_count += 1

        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Successful: {success_count}")
        print(f"Errors: {error_count}")
        print(f"{'='*60}\n")


def main():
    """Main execution function"""
    # Get the raw json directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(os.path.dirname(current_dir), 'raw', 'json')

    print("="*60)
    print("SQL Saturday Data Loader")
    print("="*60)

    # Create loader instance
    loader = SQLSatDataLoader()

    # Connect to database
    if not loader.connect():
        print("Failed to connect to database. Exiting.")
        return

    try:
        # Process all JSON files
        loader.process_directory(json_dir)
    finally:
        # Ensure connection is closed
        loader.disconnect()


if __name__ == "__main__":
    main()
