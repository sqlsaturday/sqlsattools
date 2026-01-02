-- SQL Saturday Data Loader - Table Creation Script
-- Database: sqlsatdata
-- Run this script to create the necessary tables

USE sqlsatdata;
GO

-- Drop existing tables if they exist (in correct order due to foreign keys)
IF OBJECT_ID('dbo.SessionSpeakers', 'U') IS NOT NULL DROP TABLE dbo.SessionSpeakers;
IF OBJECT_ID('dbo.Sessions', 'U') IS NOT NULL DROP TABLE dbo.Sessions;
IF OBJECT_ID('dbo.Speakers', 'U') IS NOT NULL DROP TABLE dbo.Speakers;
IF OBJECT_ID('dbo.Rooms', 'U') IS NOT NULL DROP TABLE dbo.Rooms;
IF OBJECT_ID('dbo.Events', 'U') IS NOT NULL DROP TABLE dbo.Events;
GO

-- Events Table
CREATE TABLE dbo.Events (
    EventID INT IDENTITY(1,1) PRIMARY KEY,
    EventName NVARCHAR(255) NOT NULL,
    EventDate DATE NOT NULL,
    Location NVARCHAR(255) NOT NULL,
    SourceFile NVARCHAR(255) NOT NULL,
    LoadedDate DATETIME2 DEFAULT GETDATE()
);
GO

-- Rooms Table
CREATE TABLE dbo.Rooms (
    RoomID INT PRIMARY KEY,
    EventID INT NOT NULL,
    RoomName NVARCHAR(255) NOT NULL,
    SortOrder INT,
    FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID) ON DELETE CASCADE
);
GO

-- Sessions Table
CREATE TABLE dbo.Sessions (
    SessionID NVARCHAR(50) PRIMARY KEY,
    EventID INT NOT NULL,
    Title NVARCHAR(500) NOT NULL,
    Description NVARCHAR(MAX),
    StartsAt DATETIME2,
    EndsAt DATETIME2,
    IsServiceSession BIT DEFAULT 0,
    IsPlenumSession BIT DEFAULT 0,
    RoomID INT,
    LiveUrl NVARCHAR(500),
    RecordingUrl NVARCHAR(500),
    FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID) ON DELETE CASCADE,
    FOREIGN KEY (RoomID) REFERENCES dbo.Rooms(RoomID)
);
GO

-- Speakers Table
CREATE TABLE dbo.Speakers (
    SpeakerID NVARCHAR(100) PRIMARY KEY,
    EventID INT NOT NULL,
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    FullName NVARCHAR(255),
    Bio NVARCHAR(MAX),
    TagLine NVARCHAR(255),
    ProfilePicture NVARCHAR(500),
    IsTopSpeaker BIT DEFAULT 0,
    FOREIGN KEY (EventID) REFERENCES dbo.Events(EventID) ON DELETE CASCADE
);
GO

-- Session-Speaker Junction Table (many-to-many relationship)
CREATE TABLE dbo.SessionSpeakers (
    SessionID NVARCHAR(50) NOT NULL,
    SpeakerID NVARCHAR(100) NOT NULL,
    PRIMARY KEY (SessionID, SpeakerID),
    FOREIGN KEY (SessionID) REFERENCES dbo.Sessions(SessionID) ON DELETE CASCADE,
    FOREIGN KEY (SpeakerID) REFERENCES dbo.Speakers(SpeakerID) ON DELETE NO ACTION
);
GO

-- Create indexes for better query performance
CREATE INDEX IX_Sessions_EventID ON dbo.Sessions(EventID);
CREATE INDEX IX_Sessions_RoomID ON dbo.Sessions(RoomID);
CREATE INDEX IX_Sessions_StartTime ON dbo.Sessions(StartsAt);
CREATE INDEX IX_Speakers_EventID ON dbo.Speakers(EventID);
CREATE INDEX IX_Speakers_FullName ON dbo.Speakers(FullName);
CREATE INDEX IX_Rooms_EventID ON dbo.Rooms(EventID);
GO

PRINT 'Tables created successfully!';
GO
