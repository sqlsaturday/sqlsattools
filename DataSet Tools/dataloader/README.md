# SQL Saturday Data Loader

A Python application to load SQL Saturday event data from JSON files into a SQL Server database.

## Features

- Loads event, session, speaker, and room data from JSON files
- Creates normalized relational database schema
- Handles many-to-many relationships between sessions and speakers
- Processes multiple JSON files in batch
- Comprehensive error handling and logging

## Prerequisites

- Python 3.7 or higher
- SQL Server (tested with SQL Server 2022)
- ODBC Driver 17 for SQL Server

### Installing ODBC Driver

If you don't have the ODBC driver installed:

**Windows:**
Download and install from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**Linux:**
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

## Installation

1. Navigate to the dataloader directory:
```bash
cd "DataSet Tools/dataloader"
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Configure database connection:
   - Copy `.env.example` to `.env` (already done)
   - Update the `.env` file with your database credentials if different

## Database Setup

1. Ensure your SQL Server instance is running
2. Create the database and tables by running the SQL script:

```bash
# Using sqlcmd
sqlcmd -S Aristotle\SQL2022 -U sqlsatdata -P "Demo12#4" -d sqlsatdata -i create_tables.sql

# Or run the script manually in SQL Server Management Studio (SSMS)
```

## Database Schema

The application creates the following tables:

- **Events**: Main event information (name, date, location)
- **Rooms**: Event rooms/tracks
- **Sessions**: Session details (title, description, times)
- **Speakers**: Speaker information (name, bio, etc.)
- **SessionSpeakers**: Many-to-many relationship between sessions and speakers

## Usage

Run the data loader:

```bash
python load_data.py
```

The script will:
1. Connect to the SQL Server database
2. Scan the `../raw/json` directory for JSON files
3. Process each file and load data into the database
4. Display progress and results

### Example Output

```
============================================================
SQL Saturday Data Loader
============================================================
Connected to Aristotle\SQL2022/sqlsatdata

Found 45 JSON files to process

Processing: sqlsat1020.json
  Inserted event: SQL Saturday Portland 2023 (ID: 1)
  Inserted 3 rooms
  Inserted 25 speakers
  Inserted 30 sessions with 28 speaker links

Processing: sqlsat1022.json
  Inserted event: SQL Saturday Boston 2023 (ID: 2)
  ...

============================================================
Processing complete!
Successful: 45
Errors: 0
============================================================
```

## Configuration

Database settings can be modified in the `.env` file:

```
DB_SERVER=Aristotle\SQL2022
DB_NAME=sqlsatdata
DB_USER=sqlsatdata
DB_PASSWORD=Demo12#4
```

## Troubleshooting

### Connection Issues

If you get connection errors:
1. Verify SQL Server is running
2. Check that SQL Server Authentication is enabled
3. Verify the login credentials are correct
4. Ensure the database exists
5. Check firewall settings

### ODBC Driver Not Found

If you see "ODBC Driver 17 for SQL Server not found":
- Install the ODBC driver (see Prerequisites section)
- Or modify the connection string in `load_data.py` to use a different driver:
  - Try "ODBC Driver 18 for SQL Server"
  - Or "SQL Server" (older driver)

### Data Already Exists

If you need to reload data:
1. Drop and recreate tables using the SQL script
2. Or manually delete records from the Events table (cascade delete will remove related records)

## Project Structure

```
dataloader/
├── load_data.py          # Main Python script
├── create_tables.sql     # SQL table creation script
├── requirements.txt      # Python dependencies
├── .env                  # Database configuration
├── .env.example          # Example configuration
└── README.md            # This file
```

## Data Source

JSON files are located in: `../raw/json/`

Each JSON file contains:
- Event metadata
- Sessions array
- Speakers array
- Rooms array

## Why Python?

Python was chosen for this project because:
- Built-in JSON parsing
- Excellent SQL Server support via pyodbc
- Simple and readable syntax
- Great for ETL/data loading tasks
- Easy error handling and logging
- Cross-platform compatibility

## License

See the LICENSE file in the repository root.
